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
    """The differentiator: refuse to write insurance into a known catalyst."""
    try:
        from claude_client import ClaudeClient, model_for_role
        from pydantic import BaseModel

        class Verdict(BaseModel):
            decision: str      # "write" | "stand_aside"
            reason: str
            catalysts: list[str]

        today = datetime.now(timezone.utc).date().isoformat()
        prompt = (
            f"You are the stand-aside gate of a variance-risk-premium options "
            f"seller. Today is {today}. We are about to SELL a defined-risk put-"
            f"credit spread on {sym} (spot {spot:.2f}) expiring {expiry} — i.e. "
            f"we collect premium and profit if {sym} stays above the short "
            f"strike. This blows up if we write into a known upcoming shock the "
            f"static vol surface underprices. Decide 'stand_aside' if, between "
            f"today and {expiry}, there is a scheduled macro catalyst likely to "
            f"move {sym} (FOMC decision, CPI print, jobs report, major election/"
            f"policy event) OR an active credible tail-risk narrative (banking/"
            f"liquidity stress, geopolitical shock, sector contagion) in the "
            f"current environment. Otherwise 'write'. Be concrete about the "
            f"catalyst and its date if you cite one; do not invent dates you are "
            f"unsure of — uncertainty about a catalyst is itself a reason to "
            f"stand aside on an index in a tense tape.")
        c = ClaudeClient(model=model_for_role("synthesis"))
        v = c.complete_structured(prompt=prompt, schema_cls=Verdict,
                                  called_from="vrp_standaside", max_tokens=1024)
        return v.parsed.decision, v.parsed.reason, v.parsed.catalysts
    except Exception as exc:  # noqa: BLE001 — LLM failure => conservative stand-aside
        return "stand_aside", f"LLM gate unavailable ({type(exc).__name__}) — "
        "conservative default", []


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
    dec, reason, cats = llm_standaside(sym, expiry, spot)
    rec["standaside"] = {"decision": dec, "reason": reason, "catalysts": cats}
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
