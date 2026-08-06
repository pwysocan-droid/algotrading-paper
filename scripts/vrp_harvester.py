"""Candidate #1 — variance-risk-premium harvester (paper-first, CONSTITUTION Art 2).

The machine: sell defined-risk put-credit spreads on liquid index ETFs when
the market pays a RICH credit for a strike that is ~1 realized-SD OTM (i.e.
IV > RV — the variance premium), UNLESS the LLM stand-aside rule finds a
catalyst in the tenor. Bounded loss = width - credit (2.2). Paper account is
level-3 / $100k, so 5%-sized spreads are expressible; live is gated on
capital + options approval.

Dry-run by default (propose + log, no order). PLACE=1 places the spread on
the Alpaca PAPER account. Speed over ceremony (0.4): run it, read the fills.

    python scripts/vrp_harvester.py            # dry-run
    PLACE=1 python scripts/vrp_harvester.py     # place on paper
"""
from __future__ import annotations

import json
import math
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

REPO = Path(__file__).resolve().parent.parent
PAPER = "https://paper-api.alpaca.markets"
DATA = "https://data.alpaca.markets"
H = {"APCA-API-KEY-ID": os.environ.get("ALPACA_API_KEY", ""),
     "APCA-API-SECRET-KEY": os.environ.get("ALPACA_SECRET_KEY", "")}
# options market data can use the live-data entitlement if paper key lacks it
HD = {"APCA-API-KEY-ID": os.environ.get("ALPACA_LIVE_KEY_ID", H["APCA-API-KEY-ID"]),
      "APCA-API-SECRET-KEY": os.environ.get("ALPACA_LIVE_SECRET", H["APCA-API-SECRET-KEY"])}

# Universe trimmed on real calibration (reports/vrp-richness-backfill-*.json):
# dropped TLT (never fairly paid — 0% of days at 1-SD) and EEM (illiquid, sparse/
# crossed quotes, n as low as 112). Kept names clear their delta-fair bar 4-9% of days.
UNDERLYINGS = ["SPY", "QQQ", "IWM", "DIA", "GLD"]
DTE_TARGET = 35
WIDTH = {"SPY": 5, "QQQ": 5, "IWM": 3, "DIA": 5,   # spread width in $ (~ price-scaled)
         "GLD": 5, "TLT": 2, "EEM": 1}             # TLT/EEM widths kept (unused now)
RICHNESS_MIN = float(os.environ.get("RICHNESS_MIN", "0.20"))  # legacy flat bar (superseded)
# Book gate v2 — CONSTITUTION 2.9 / book/pre-reg-book-gate-v2.md. Write when the
# day's richness is top-decile of its trailing 1-year distribution (IV-rank
# convention) AND above an absolute floor. NOT a fairness test (safety = 2.2/2.4);
# a pre-registered deployment-TIMING hypothesis, tested vs the always-write shadow.
GATE_PCTL = int(os.environ.get("GATE_PCTL", "90"))        # top decile
GATE_WINDOW = int(os.environ.get("GATE_WINDOW", "252"))   # 1yr trailing (IV-rank)
GATE_FLOOR = float(os.environ.get("GATE_FLOOR", "0.08"))  # absolute floor (~pooled median)
PREDICTED_FIRE = 0.21   # backfill p90 cadence (reports/vrp-richness-backfill-1sd.json)
PROFIT_TAKE = float(os.environ.get("PROFIT_TAKE", "0.50"))  # close at 50% of credit captured
CLOSE_DTE = int(os.environ.get("CLOSE_DTE", "10"))          # close near expiry (gamma/pin)
BOOK_CAPITAL = 100_000.0                     # paper book; 5% = $5k max loss/position
MAX_LOSS_FRAC = 0.05
LEGDER = REPO / "book" / "positions.jsonl"
SHADOW = REPO / "book" / "shadow.jsonl"   # zero-risk decision-rule record (Art 3.2)

# Real scheduled-macro calendar (2026). FOMC decision dates are the Fed's
# published 2026 schedule; CPI (~12th) and NFP (1st Friday) are computed.
# These events are ALREADY PRICED INTO IV — their presence is context, NOT a
# reason to stand aside. Verify FOMC dates against the Fed's published schedule.
FOMC_2026 = ["2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
             "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-16"]


def scheduled_events(start_iso: str, end_iso: str) -> list[str]:
    from datetime import date as _d, timedelta as _td
    a, b = _d.fromisoformat(start_iso), _d.fromisoformat(end_iso)
    out = [f"FOMC {d}" for d in FOMC_2026 if a <= _d.fromisoformat(d) <= b]
    m = _d(a.year, a.month, 1)
    while m <= b:
        # NFP: first Friday; CPI: ~12th
        nfp = m + _td(days=(4 - m.weekday()) % 7)
        cpi = _d(m.year, m.month, 12)
        if a <= nfp <= b:
            out.append(f"Jobs/NFP {nfp}")
        if a <= cpi <= b:
            out.append(f"CPI {cpi}")
        m = _d(m.year + (m.month == 12), (m.month % 12) + 1, 1)
    return sorted(out)


def stock_bars(sym, n=30):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=n * 2 + 10)
    r = requests.get(f"{DATA}/v2/stocks/{sym}/bars",
                     params={"timeframe": "1Day", "start": start.date().isoformat(),
                             "limit": 400, "feed": "iex", "adjustment": "all"},
                     headers=HD, timeout=20)
    r.raise_for_status()
    return [b["c"] for b in (r.json().get("bars") or [])]


def realized_vol(closes):
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))
            if closes[i - 1] > 0]
    rr = rets[-20:]
    return statistics.pstdev(rr) * math.sqrt(252) if len(rr) > 5 else None


def option_chain(sym, expiry):
    """Snapshot the put chain for one expiry; return {strike: {bid, ask}}."""
    out, token = {}, None
    for _ in range(6):
        params = {"feed": "indicative", "type": "put", "expiration_date": expiry,
                  "limit": 1000}
        if token:
            params["page_token"] = token
        r = requests.get(f"{DATA}/v1beta1/options/snapshots/{sym}",
                         params=params, headers=HD, timeout=20)
        if not r.ok:
            break
        j = r.json()
        for occ, snap in (j.get("snapshots") or {}).items():
            q = snap.get("latestQuote") or {}
            # OCC: SYM + YYMMDD + C/P + strike*1000 (8 digits)
            strike = int(occ[-8:]) / 1000.0
            out[strike] = {"bid": q.get("bp"), "ask": q.get("ap"), "occ": occ}
        token = j.get("next_page_token")
        if not token:
            break
    return out


def nearest_expiry():
    """~DTE_TARGET days out, a Friday (monthly/weekly)."""
    target = datetime.now(timezone.utc).date() + timedelta(days=DTE_TARGET)
    while target.weekday() != 4:      # Friday
        target += timedelta(days=1)
    return target.isoformat()


def llm_standaside(sym, expiry, spot):
    """Differentiator, refined: routine scheduled macro is ALREADY priced into
    IV, so their presence is NOT a reason to stand aside. Default WRITE; stand
    aside only for EXTRAORDINARY, underpriced tail risk (a live crisis/regime
    the surface hasn't caught up to). The scheduled calendar is given as priced
    context so the model stops citing routine CPI/FOMC as a reason."""
    today = datetime.now(timezone.utc).date().isoformat()
    events = scheduled_events(today, expiry)
    try:
        from claude_client import ClaudeClient, model_for_role
        from pydantic import BaseModel

        class Verdict(BaseModel):
            decision: str      # "write" | "stand_aside"
            reason: str

        prompt = (
            f"You gate a variance-risk-premium seller. Today {today}; selling a "
            f"defined-risk put-credit spread on {sym} (spot {spot:.2f}) expiring "
            f"{expiry}. DEFAULT IS TO WRITE — the premium is already rich enough "
            f"to pass our richness gate. The following scheduled macro events "
            f"fall in the window and are ALREADY PRICED INTO IMPLIED VOL, so they "
            f"are NOT by themselves a reason to stand aside: {events or 'none'}. "
            f"Return 'stand_aside' ONLY if there is an EXTRAORDINARY, currently "
            f"UNDERPRICED tail risk the static vol surface has not caught up to — "
            f"an active credible crisis or regime break (banking/liquidity "
            f"contagion, disorderly geopolitical shock, a specific dislocation), "
            f"NOT routine data prints or a generically 'uncertain' tape. If you "
            f"cannot name a concrete extraordinary risk, return 'write'. One "
            f"sentence reason.")
        c = ClaudeClient(model=model_for_role("synthesis"))
        v = c.complete_structured(prompt=prompt, schema_cls=Verdict,
                                  called_from="vrp_standaside", max_tokens=512)
        return v.parsed.decision, v.parsed.reason, events
    except Exception as exc:  # noqa: BLE001 — on LLM failure, WRITE (events are priced;
        # the richness gate already protects us; a dead LLM must not freeze the book)
        return "write", f"LLM gate unavailable ({type(exc).__name__}); events priced", events


BACKFILL_1SD = REPO / "reports" / "vrp-richness-backfill-1sd.json"


def _richness_history(sym):
    """Trailing 1-SD richness series for `sym` = committed backfill seed +
    forward 1sd shadow observations (book/pre-reg-book-gate-v2.md). Deduped by
    date; today's row is not yet logged when propose() runs, so it is excluded."""
    seen = {}
    try:
        bf = json.loads(BACKFILL_1SD.read_text())
        for r in (bf["by_underlying"].get(sym, {}).get("rows") or []):
            if r.get("rich_hc") is not None:
                seen[r["date"]] = r["rich_hc"]
    except Exception:  # noqa: BLE001 — no seed ⇒ fall back to floor-only until history builds
        pass
    if SHADOW.exists():
        for line in SHADOW.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if (r.get("sym") == sym and r.get("arm", "1sd") == "1sd"
                    and r.get("richness") is not None):
                seen[r["date"]] = r["richness"]
    return [seen[d] for d in sorted(seen)][-GATE_WINDOW:]


def trailing_pctl(sym):
    """Trailing GATE_PCTL percentile of the richness history, or None if <30 obs."""
    s = _richness_history(sym)
    if len(s) < 30:
        return None
    s = sorted(s)
    return s[min(len(s) - 1, int(len(s) * GATE_PCTL / 100))]


def propose(sym):
    closes = stock_bars(sym)
    if len(closes) < 22:
        return None
    spot, rv = closes[-1], realized_vol(closes)
    if not rv:
        return None
    expiry = nearest_expiry()
    dte = (datetime.fromisoformat(expiry).date() - datetime.now(timezone.utc).date()).days
    one_sd = spot * rv * math.sqrt(dte / 252.0)
    short_k = round((spot - one_sd) / WIDTH[sym]) * WIDTH[sym]   # ~1 SD OTM put
    long_k = short_k - WIDTH[sym]
    chain = option_chain(sym, expiry)
    sp, lp = chain.get(float(short_k)), chain.get(float(long_k))
    if not (sp and lp and sp.get("bid") and lp.get("ask")):
        return {"sym": sym, "skip": f"strikes {short_k}/{long_k} not quoted "
                f"(expiry {expiry}, spot {spot:.2f}, 1SD {one_sd:.2f})"}
    credit = sp["bid"] - lp["ask"]                 # conservative: sell bid, buy ask
    width = WIDTH[sym]
    # MEASUREMENT (book/proposal-book-gate-seed §4): mid credit + real crossing cost.
    # Gate UNCHANGED — this only logs; the gate still uses the executable credit/width.
    mid_credit = crossing = None
    if sp.get("ask") is not None and lp.get("bid") is not None:
        mid_credit = round((sp["bid"] + sp["ask"]) / 2 - (lp["bid"] + lp["ask"]) / 2, 3)
        crossing = round(mid_credit - credit, 3)   # $/spread the real bid/ask crossing costs
    if credit <= 0:                                # crossed/illiquid quote, not real premium
        return {"sym": sym, "skip": f"no usable credit (crossed/illiquid: "
                f"{short_k}/{long_k} bid {sp['bid']} ask {lp['ask']})",
                "spot": round(spot, 2), "short_k": short_k, "long_k": long_k,
                "mid_credit": mid_credit, "crossing_cost": crossing}
    max_loss = width - credit
    richness = credit / width if width else 0
    contracts = max(0, int((BOOK_CAPITAL * MAX_LOSS_FRAC) / (max_loss * 100)))
    rec = {"sym": sym, "expiry": expiry, "spot": round(spot, 2), "rv": round(rv, 3),
           "short_k": short_k, "long_k": long_k, "credit": round(credit, 2),
           "mid_credit": mid_credit, "crossing_cost": crossing,
           "max_loss_per": round(max_loss * 100, 2), "richness": round(richness, 2),
           "contracts": contracts, "short_occ": sp["occ"], "long_occ": lp["occ"]}
    # Book gate v2 (2.9): top-decile of trailing 1yr AND above the absolute floor.
    thr = trailing_pctl(sym)
    rec["gate_pctl_thr"] = round(thr, 3) if thr is not None else None
    rec["gate_floor"] = GATE_FLOOR
    below_floor = richness < GATE_FLOOR
    below_pctl = (thr is not None) and (richness < thr)
    rec["gate_pass"] = not (below_floor or below_pctl)
    if below_floor:
        rec["skip"] = f"below floor ({richness:.0%} < {GATE_FLOOR:.0%})"
        return rec
    if below_pctl:
        rec["skip"] = (f"not top-decile ({richness:.0%} < trailing-{GATE_WINDOW}d "
                       f"p{GATE_PCTL} {thr:.0%})")
        return rec
    if contracts < 1:
        rec["skip"] = "max loss > 5% cap even at 1 contract"
        return rec
    dec, reason, events = llm_standaside(sym, expiry, spot)
    rec["standaside"] = {"decision": dec, "reason": reason, "scheduled_events": events}
    rec["action"] = "WRITE" if dec == "write" else "STAND_ASIDE"
    return rec


def propose_variant(sym, sd_mult):
    """Shadow-only spread at `sd_mult` realized-SD OTM (e.g. 0.5 = closer strike,
    fatter premium). Same math as propose(), no gate/stand-aside — pure data for
    the shadow arm so real quotes decide the strike distance, not a guess."""
    closes = stock_bars(sym)
    if len(closes) < 22:
        return None
    spot, rv = closes[-1], realized_vol(closes)
    if not rv:
        return None
    expiry = nearest_expiry()
    dte = (datetime.fromisoformat(expiry).date() - datetime.now(timezone.utc).date()).days
    W = WIDTH[sym]
    one_sd = spot * rv * math.sqrt(dte / 252.0)
    short_k = round((spot - sd_mult * one_sd) / W) * W
    long_k = short_k - W
    chain = option_chain(sym, expiry)
    sp, lp = chain.get(float(short_k)), chain.get(float(long_k))
    if not (sp and lp and sp.get("bid") and lp.get("ask")):
        return None
    credit = sp["bid"] - lp["ask"]
    if credit <= 0:
        return None
    return {"sym": sym, "expiry": expiry, "spot": round(spot, 2),
            "short_k": short_k, "long_k": long_k, "credit": round(credit, 2),
            "richness": round(credit / W, 3), "outcome": "shadow_variant"}


def place_paper(rec):
    """Multi-leg put-credit spread on the PAPER account (PLACE=1)."""
    order = {"order_class": "mleg", "qty": str(rec["contracts"]),
             "type": "limit", "time_in_force": "day",
             "limit_price": str(round(rec["credit"] * 0.9, 2)),   # a touch worse than mid
             "legs": [
                 {"symbol": rec["short_occ"], "side": "sell", "ratio_qty": "1",
                  "position_intent": "sell_to_open"},
                 {"symbol": rec["long_occ"], "side": "buy", "ratio_qty": "1",
                  "position_intent": "buy_to_open"}]}
    r = requests.post(f"{PAPER}/v2/orders", json=order, headers=H, timeout=20)
    return r.status_code, r.text[:300]


def _held_option_symbols() -> dict:
    """OCC symbol -> signed qty actually held on the paper account. Manage
    trusts THIS, not the ledger's intent, before closing anything."""
    try:
        r = requests.get(f"{PAPER}/v2/positions", headers=H, timeout=20)
        r.raise_for_status()
        return {p["symbol"]: float(p["qty"]) for p in r.json()
                if p.get("asset_class") == "us_option"}
    except Exception:  # noqa: BLE001
        return {}


def _ledger_rows():
    if not LEGDER.exists():
        return []
    return [json.loads(l) for l in LEGDER.read_text().splitlines() if l.strip()]


def manage_positions(place):
    """Exit half of the loop: close each open spread at PROFIT_TAKE of credit
    captured, or near expiry. Defined-risk means the loss is already capped;
    management harvests the profit and rolls off gamma/pin risk near expiry."""
    rows = _ledger_rows()
    held = _held_option_symbols()
    changed = False
    today = datetime.now(timezone.utc).date()
    for r in rows:
        if r.get("status") != "open":
            continue
        d = r.get("detail", {})
        # reconcile: only manage legs actually HELD (open order may not have filled)
        both_held = (held.get(d.get("short_occ"), 0) != 0
                     and held.get(d.get("long_occ"), 0) != 0)
        if not both_held:
            age_days = (datetime.now(timezone.utc)
                        - datetime.fromisoformat(r["ts"])).days
            if age_days >= 1:
                r["status"] = "unfilled"
                r["note"] = "open order never filled (not held on account)"
                changed = True
                print(f"  MANAGE {d.get('sym')} -> UNFILLED (open never filled)")
            continue
        sym, expiry = d.get("sym"), d.get("expiry")
        credit, contracts = d.get("credit"), d.get("contracts")
        chain = option_chain(sym, expiry)
        sp, lp = chain.get(float(d.get("short_k"))), chain.get(float(d.get("long_k")))
        dte = (datetime.fromisoformat(expiry).date() - today).days
        close_debit = None
        if sp and lp and sp.get("ask") is not None and lp.get("bid") is not None:
            close_debit = sp["ask"] - lp["bid"]         # buy short, sell long
        reason = None
        if close_debit is not None and close_debit <= PROFIT_TAKE * credit:
            reason = "profit_take"
        elif dte <= CLOSE_DTE:
            reason = "near_expiry"
        if not reason:
            continue
        realized = (credit - close_debit) * 100 * contracts if close_debit is not None else None
        if place and close_debit is not None:
            order = {"order_class": "mleg", "qty": str(contracts), "type": "limit",
                     "time_in_force": "day", "limit_price": str(round(close_debit * 1.1 + 0.01, 2)),
                     "legs": [
                         {"symbol": d["short_occ"], "side": "buy", "ratio_qty": "1",
                          "position_intent": "buy_to_close"},
                         {"symbol": d["long_occ"], "side": "sell", "ratio_qty": "1",
                          "position_intent": "sell_to_close"}]}
            rr = requests.post(f"{PAPER}/v2/orders", json=order, headers=H, timeout=20)
            r["close_order"] = {"status": rr.status_code, "body": rr.text[:160]}
            print(f"     -> close order {rr.status_code}: {rr.text[:70]}")
        r["status"] = "closed"; r["close_reason"] = reason
        r["realized_pnl"] = round(realized, 2) if realized is not None else None
        r["closed_ts"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        changed = True
        rp = f"${realized:.0f}" if realized is not None else "?"
        print(f"  MANAGE {sym} {d.get('short_k')}/{d.get('long_k')} -> CLOSE ({reason}) realized {rp}")
    if changed:
        LEGDER.write_text("".join(json.dumps(x) + "\n" for x in rows))


def close_on(sym, day):
    """Underlying close on a specific date (for shadow resolution at expiry)."""
    r = requests.get(f"{DATA}/v2/stocks/{sym}/bars",
                     params={"timeframe": "1Day", "start": day, "end": day,
                             "limit": 1, "feed": "iex", "adjustment": "all"},
                     headers=HD, timeout=20)
    if not r.ok:
        return None
    bars = r.json().get("bars") or []
    return bars[0]["c"] if bars else None


def log_shadow(scan, ts, arm="1sd"):
    """Zero-risk decision-rule record (Art 3.2): log EVERY underlying's proposed
    spread each day — executed or not — so the gate + stand-aside rule is
    evaluated on ~250 days/yr, not just the rare days it trades. `arm` tags the
    strike hypothesis (1sd = live/primary; 0.5sd = shadow-only closer strike),
    so real quotes, not a guess, decide the strike distance."""
    existing = set()
    if SHADOW.exists():
        for l in SHADOW.read_text().splitlines():
            if l.strip():
                r = json.loads(l)
                existing.add((r["date"], r["sym"], r.get("arm", "1sd")))
    day = ts[:10]
    with SHADOW.open("a") as f:
        for s in scan:
            if (s.get("short_k") is None or s.get("credit") is None
                    or s["credit"] <= 0 or not s.get("expiry")):
                continue                          # skip crossed/illiquid quotes
            key = (day, s["sym"], arm)
            if key in existing:
                continue
            rich = s.get("richness")
            f.write(json.dumps({
                "date": day, "sym": s["sym"], "arm": arm, "expiry": s["expiry"],
                "spot": s.get("spot"), "short_k": s["short_k"], "long_k": s["long_k"],
                "width": WIDTH.get(s["sym"]), "credit": s["credit"], "richness": rich,
                "mid_credit": s.get("mid_credit"),      # measurement (seed-proposal §4)
                "crossing_cost": s.get("crossing_cost"),
                "gate_pass": s.get("gate_pass"),   # 1sd: real gate v2; 0.5sd: None (always-write)
                "gate_pctl_thr": s.get("gate_pctl_thr"),
                "outcome": s.get("outcome"), "status": "shadow_open"}) + "\n")


def fire_rate():
    """Cumulative realized gate fire-rate on the 1sd arm: gate_pass True over all
    1sd shadow rows with a recorded gate decision. Compared vs PREDICTED_FIRE so a
    drift from the ~21% backfill prediction is visible daily, not at month two."""
    if not SHADOW.exists():
        return None, 0
    passes = total = 0
    for line in SHADOW.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("arm", "1sd") == "1sd" and r.get("gate_pass") is not None:
            total += 1
            passes += 1 if r.get("gate_pass") else 0
    return (passes / total if total else None), total


def resolve_shadows():
    """At/after expiry, compute each shadow spread's hypothetical P&L from the
    underlying's settlement close. Payoff of a put-credit spread at price U:
    U>=short -> keep credit; U<=long -> max loss; between -> partial."""
    if not SHADOW.exists():
        return 0
    rows = [json.loads(l) for l in SHADOW.read_text().splitlines() if l.strip()]
    today = datetime.now(timezone.utc).date()
    cache, resolved = {}, 0
    for r in rows:
        if r.get("status") != "shadow_open":
            continue
        if datetime.fromisoformat(r["expiry"]).date() > today:
            continue
        key = (r["sym"], r["expiry"])
        U = cache.get(key) or close_on(r["sym"], r["expiry"])
        cache[key] = U
        if U is None:
            continue                          # bar not posted yet; resolve next run
        sk, lk, credit, width = r["short_k"], r["long_k"], r["credit"], r["width"]
        if U >= sk:
            pnl = credit
        elif U <= lk:
            pnl = credit - width
        else:
            pnl = credit - (sk - U)
        r["underlying_at_expiry"] = round(U, 2)
        r["pnl_per_contract"] = round(pnl * 100, 2)
        r["status"] = "resolved"
        resolved += 1
    if resolved:
        SHADOW.write_text("".join(json.dumps(x) + "\n" for x in rows))
    return resolved


def main() -> int:
    place = os.environ.get("PLACE") == "1"
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    print(f"VRP harvester {ts} · mode={'PAPER-PLACE' if place else 'DRY-RUN'} "
          f"· book ${BOOK_CAPITAL:,.0f} · 5% cap ${BOOK_CAPITAL*MAX_LOSS_FRAC:,.0f}\n")
    print("-- manage open positions --")
    manage_positions(place)
    nres = resolve_shadows()
    if nres:
        print(f"-- shadow: resolved {nres} matured spread(s) --")
    print("-- scan for new writes --")
    written = []
    scan = []   # every underlying's real outcome (richness/skip) — self-documenting
    for sym in UNDERLYINGS:
        try:
            rec = propose(sym)
        except Exception as exc:  # noqa: BLE001
            print(f"{sym}: ERROR {type(exc).__name__}: {exc}")
            scan.append({"sym": sym, "outcome": "error",
                         "detail": f"{type(exc).__name__}: {exc}"}); continue
        if rec is None:
            print(f"{sym}: no data")
            scan.append({"sym": sym, "outcome": "no_data"}); continue
        if rec.get("skip"):
            print(f"{sym}: SKIP — {rec['skip']}")
            scan.append({"sym": sym, "outcome": "skip", "reason": rec["skip"],
                         "richness": rec.get("richness"), "credit": rec.get("credit"),
                         "mid_credit": rec.get("mid_credit"), "crossing_cost": rec.get("crossing_cost"),
                         "short_k": rec.get("short_k"), "long_k": rec.get("long_k"),
                         "spot": rec.get("spot"), "rv": rec.get("rv"),
                         "expiry": rec.get("expiry"), "gate_pass": rec.get("gate_pass"),
                         "gate_pctl_thr": rec.get("gate_pctl_thr")}); continue
        sa = rec["standaside"]
        scan.append({"sym": sym, "outcome": rec["action"].lower(),
                     "richness": rec["richness"], "credit": rec["credit"],
                     "mid_credit": rec.get("mid_credit"), "crossing_cost": rec.get("crossing_cost"),
                     "short_k": rec["short_k"], "long_k": rec["long_k"],
                     "spot": rec["spot"], "rv": rec["rv"], "expiry": rec["expiry"],
                     "gate_pass": rec.get("gate_pass"),
                     "gate_pctl_thr": rec.get("gate_pctl_thr")})
        print(f"{sym}: {rec['action']}  {rec['short_k']}/{rec['long_k']}p {rec['expiry']} "
              f"credit ${rec['credit']:.2f} maxloss ${rec['max_loss_per']:.0f} "
              f"rich {rec['richness']:.0%} x{rec['contracts']}")
        print(f"     stand-aside[{sa['decision']}]: {sa['reason'][:110]}")
        if rec["action"] == "WRITE":
            if place:
                code, body = place_paper(rec)
                rec["order"] = {"status": code, "body": body}
                print(f"     -> paper order {code}: {body[:80]}")
                with LEGDER.open("a") as f:
                    f.write(json.dumps({"ts": ts, "instrument": sym, "venue": "alpaca-paper",
                        "side": "put_credit_spread", "status": "open",
                        "structural_worst_case_pct": round(rec['max_loss_per']*rec['contracts']
                            / BOOK_CAPITAL*100, 3), "detail": rec}) + "\n")
            written.append(rec)
    log_shadow(scan, ts, arm="1sd")   # primary (live) strike hypothesis
    # shadow-only closer strike (0.5 SD): fatter premium, higher odds — data, not a guess
    variant = []
    for sym in UNDERLYINGS:
        try:
            v = propose_variant(sym, 0.5)
        except Exception:  # noqa: BLE001
            v = None
        if v:
            variant.append(v)
    log_shadow(variant, ts, arm="0.5sd")
    rf, fn = fire_rate()
    gate = {"pctl": GATE_PCTL, "window": GATE_WINDOW, "floor": GATE_FLOOR,
            "predicted_fire": PREDICTED_FIRE,
            "realized_fire": round(rf, 3) if rf is not None else None, "fire_n": fn}
    out = REPO / "reports" / f"vrp-{datetime.now(timezone.utc).date().isoformat()}.json"
    out.write_text(json.dumps({"ts": ts, "mode": "place" if place else "dry",
                               "gate": gate, "scan": scan, "written": written},
                              indent=2) + "\n")
    fr = f"{rf:.0%}" if rf is not None else "n/a"
    print(f"\n{len(written)} write candidate(s) · gate fire {fr} (predicted "
          f"{PREDICTED_FIRE:.0%}, n={fn}) · wrote {out.name}"
          + ("" if place else " · DRY-RUN (set PLACE=1 to trade paper)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
