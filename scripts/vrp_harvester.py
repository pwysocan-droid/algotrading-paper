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

UNDERLYINGS = ["SPY", "QQQ", "IWM"]
DTE_TARGET = 35
WIDTH = {"SPY": 5, "QQQ": 5, "IWM": 3}     # spread width in $
RICHNESS_MIN = float(os.environ.get("RICHNESS_MIN", "0.20"))  # credit/width bar
BOOK_CAPITAL = 100_000.0                     # paper book; 5% = $5k max loss/position
MAX_LOSS_FRAC = 0.05
LEGDER = REPO / "book" / "positions.jsonl"

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
    max_loss = width - credit
    richness = credit / width if width else 0
    contracts = max(0, int((BOOK_CAPITAL * MAX_LOSS_FRAC) / (max_loss * 100)))
    rec = {"sym": sym, "expiry": expiry, "spot": round(spot, 2), "rv": round(rv, 3),
           "short_k": short_k, "long_k": long_k, "credit": round(credit, 2),
           "max_loss_per": round(max_loss * 100, 2), "richness": round(richness, 2),
           "contracts": contracts, "short_occ": sp["occ"], "long_occ": lp["occ"]}
    if richness < RICHNESS_MIN:
        rec["skip"] = f"premium thin (credit {richness:.0%} of width < {RICHNESS_MIN:.0%})"
        return rec
    if contracts < 1:
        rec["skip"] = "max loss > 5% cap even at 1 contract"
        return rec
    dec, reason, events = llm_standaside(sym, expiry, spot)
    rec["standaside"] = {"decision": dec, "reason": reason, "scheduled_events": events}
    rec["action"] = "WRITE" if dec == "write" else "STAND_ASIDE"
    return rec


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


def main() -> int:
    place = os.environ.get("PLACE") == "1"
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    print(f"VRP harvester {ts} · mode={'PAPER-PLACE' if place else 'DRY-RUN'} "
          f"· book ${BOOK_CAPITAL:,.0f} · 5% cap ${BOOK_CAPITAL*MAX_LOSS_FRAC:,.0f}\n")
    written = []
    for sym in UNDERLYINGS:
        try:
            rec = propose(sym)
        except Exception as exc:  # noqa: BLE001
            print(f"{sym}: ERROR {type(exc).__name__}: {exc}"); continue
        if rec is None:
            print(f"{sym}: no data"); continue
        if rec.get("skip"):
            print(f"{sym}: SKIP — {rec['skip']}"); continue
        sa = rec["standaside"]
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
    out = REPO / "reports" / f"vrp-{datetime.now(timezone.utc).date().isoformat()}.json"
    out.write_text(json.dumps({"ts": ts, "mode": "place" if place else "dry",
                               "written": written}, indent=2) + "\n")
    print(f"\n{len(written)} write candidate(s) · wrote {out.name}"
          + ("" if place else " · DRY-RUN (set PLACE=1 to trade paper)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
