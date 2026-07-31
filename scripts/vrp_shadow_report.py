"""Read the shadow ledger (book/shadow.jsonl) and report the decision-rule
record. This is the instrument that turns the accumulating zero-risk shadow
into the answer for Candidate #1.

The one test that matters (Art 2.5, the VRP thesis): does the strategy make
money FORWARD, net of costs? The verdict is realized P&L — nothing else.

Diagnostic (non-circular): compare the REALIZED breach rate to the MARKET's own
priced breakeven — richness = credit/width IS the loss-rate the market is
charging, straight from real quotes. Realized breach below market breakeven =
the market over-priced the tail = premium. We deliberately do NOT judge against
N(-realized_SD): that "delta-implied odds" bar comes from the same vol model
that PLACES the strike, so beating it is self-referential, not evidence.

Also slices three decision rules on the same resolved trades:
  always-write (every day) · gate-only (richness>=20%) · gate+stand-aside (live).

Reports only; makes no claim below n=30 (small-sample quarantine). Prints and
writes reports/vrp-shadow-summary.json.
"""
from __future__ import annotations
import json, math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SHADOW = REPO / "book" / "shadow.jsonl"
ARMS = ("1sd", "0.5sd")
# placement-model odds, kept ONLY as a self-referential reference (see docstring)
ARM_SD = {"1sd": 1.0, "0.5sd": 0.5}


def N(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def rows():
    if not SHADOW.exists():
        return []
    return [json.loads(l) for l in SHADOW.read_text().splitlines() if l.strip()]


def stats(rs):
    n = len(rs)
    if not n:
        return {"n": 0}
    pnl = [r["pnl_per_contract"] for r in rs]
    return {"n": n, "total_pnl": round(sum(pnl), 2),
            "avg_pnl": round(sum(pnl) / n, 2),
            "win_rate": round(sum(1 for p in pnl if p > 0) / n, 3)}


def main():
    rs = rows()
    resolved = [r for r in rs if r.get("status") == "resolved"]
    open_ = [r for r in rs if r.get("status") == "shadow_open"]
    out = {"total_logged": len(rs), "resolved": len(resolved), "open": len(open_),
           "by_arm": {}}
    print(f"Shadow ledger: {len(rs)} logged · {len(resolved)} resolved · {len(open_)} open\n")

    for arm in ARMS:
        ar = [r for r in resolved if r.get("arm", "1sd") == arm]
        block = {"resolved": len(ar), "placement_model_odds_ref": round(N(-ARM_SD[arm]), 3)}
        if ar:
            # market breakeven = the loss-rate the market priced in (from real quotes)
            mkt_breakeven = sum(r["richness"] for r in ar) / len(ar)
            breach_rate = sum(1 for r in ar if r["underlying_at_expiry"] < r["short_k"]) / len(ar)
            block["market_breakeven"] = round(mkt_breakeven, 3)
            block["realized_breach_rate"] = round(breach_rate, 3)
            block["diagnostic"] = ("breach < market breakeven — premium sign"
                                   if breach_rate < mkt_breakeven
                                   else "breach >= market breakeven — no premium sign")
            # THE VERDICT: realized P&L, three decision rules on the same trades
            block["always_write"] = stats(ar)
            block["gate_only"] = stats([r for r in ar if r.get("gate_pass")])
            block["gate_plus_standaside"] = stats([r for r in ar
                                                   if r.get("outcome") == "write"])
            q = "  [n<30 — QUARANTINED, no claim]" if len(ar) < 30 else ""
            print(f"{arm}: {len(ar)} resolved{q}")
            print(f"  VERDICT (realized P&L, always-write): {block['always_write']}")
            print(f"  gate-only:  {block['gate_only']}")
            print(f"  gate+aside: {block['gate_plus_standaside']}")
            print(f"  diagnostic: realized breach {breach_rate:.0%} vs market "
                  f"breakeven {mkt_breakeven:.0%} -> {block['diagnostic']}")
        else:
            print(f"{arm}: 0 resolved yet "
                  f"({sum(1 for r in open_ if r.get('arm','1sd')==arm)} open, "
                  f"first resolves at earliest expiry)")
        out["by_arm"][arm] = block
        print()

    (REPO / "reports" / "vrp-shadow-summary.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print("wrote reports/vrp-shadow-summary.json")


if __name__ == "__main__":
    raise SystemExit(main())
