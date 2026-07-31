"""Charter E Stage 0 — venue cost-floor study (measurement only).

Reads local Kalshi snapshots and reports effective spread + depth by price
bucket (tail-focused), the DOCUMENTED fee schedule, and a venue-robustness
assessment. The reported cost is an OPTIMISTIC LOWER BOUND: quoted spread + the
published fee, with NO executed-order verification and NO time-to-fill (both
require trading — see RECALIBRATION_REVIEW.md S0-2). Writes
reports/event-venue-floor-{date}.json. No trading logic anywhere in this file.
"""
from __future__ import annotations

import json
import math
import sqlite3
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DB = HERE / "kalshi.db"

# 5¢ price buckets; tails (<10¢, >90¢) are where the favorite–longshot prior lives.
BUCKETS = [(round(x / 100, 2), round((x + 5) / 100, 2)) for x in range(0, 100, 5)]


def price_bucket(p):
    if p is None:
        return None
    for lo, hi in BUCKETS:
        if lo <= p < hi:
            return (lo, hi)
    return (0.95, 1.00) if p >= 0.95 else None


def kalshi_fee(p):
    """Documented general-market trading fee per contract (taker), NOT executed-
    verified: ceil(0.07 · P · (1−P)) rounded up to the cent."""
    if p is None:
        return None
    return math.ceil(0.07 * p * (1 - p) * 100) / 100


def is_tail(bucket):
    return bucket is not None and (bucket[1] <= 0.10 or bucket[0] >= 0.90)


def _median(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 4) if xs else None


def bucket_stats(rows):
    """rows: iterable of dicts with mid, spread, yes_bid_size, yes_ask_size, ticker.
    Returns per-bucket cost/depth/coverage stats. Pure — unit-tested."""
    by = {}
    for r in rows:
        b = price_bucket(r.get("mid"))
        if b is None:
            continue
        by.setdefault(b, {"spreads": [], "depth": [], "tickers": set()})
        by[b]["spreads"].append(r.get("spread"))
        for sz in (r.get("yes_bid_size"), r.get("yes_ask_size")):
            if sz is not None:
                by[b]["depth"].append(sz)
        if r.get("ticker"):
            by[b]["tickers"].add(r["ticker"])
    out = []
    for b in BUCKETS:
        d = by.get(b)
        if not d:
            continue
        mid_p = (b[0] + b[1]) / 2
        med_spread = _median(d["spreads"])
        fee = kalshi_fee(mid_p)
        # all-in round-trip LOWER BOUND: cross the spread once + taker fee both sides
        allin = round(med_spread + 2 * fee, 4) if med_spread is not None else None
        out.append({
            "bucket": f"{b[0]:.2f}-{b[1]:.2f}", "tail": is_tail(b),
            "n_obs": len(d["spreads"]), "n_markets": len(d["tickers"]),
            "median_spread": med_spread,
            "median_halfspread_pct_of_price": (round((med_spread / 2) / mid_p, 3)
                                               if med_spread and mid_p else None),
            "documented_fee_per_contract": fee,
            "allin_roundtrip_cost_lower_bound": allin,
            "median_top_depth_fp": _median(d["depth"]),
        })
    return out


VENUE_ROBUSTNESS = {
    "venue": "Kalshi",
    "note": "DOCUMENTED, operator-to-verify — this is not an executed audit.",
    "regulatory": "CFTC-regulated designated contract market (DCM/DCO).",
    "fund_segregation": "member funds held at settlement bank — VERIFY current terms.",
    "historical_void_or_dispute_rate": "UNMEASURED — assess before any capital (2.10b tail).",
    "dominant_tail": "venue/settlement failure = 100% of on-venue capital → size ≤5%/venue (2.4).",
}


def build_report(db=DB):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in con.execute(
            "SELECT ts,ticker,mid,spread,yes_bid_size,yes_ask_size FROM snapshots")]
    except sqlite3.OperationalError:
        rows = []
    con.close()
    snaps = len({r["ts"] for r in rows})
    stats = bucket_stats(rows)
    tail = [b for b in stats if b["tail"]]
    return {
        "generated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "stage": "0 — venue cost-floor study (measurement only)",
        "cost_caveat": "LOWER BOUND: quoted spread + documented fee; no executed "
                       "verification, no time-to-fill (both require trading).",
        "coverage": {"total_obs": len(rows), "snapshots": snaps,
                     "tail_bucket_obs": sum(b["n_obs"] for b in tail)},
        "by_bucket": stats,
        "tail_buckets": tail,
        "venue_robustness": VENUE_ROBUSTNESS,
        "kill_note": "Charter E dies at Stage 0 if the tail-bucket lower-bound cost "
                     "already dominates any plausible bounded bias (kill is on "
                     "absolute cost — the racing bias magnitude is NOT the Kalshi "
                     "threshold; see RECALIBRATION_REVIEW S0-1).",
    }


def main():
    rep = build_report()
    out = REPO / "reports" / f"event-venue-floor-{datetime.now(timezone.utc).date().isoformat()}.json"
    out.write_text(json.dumps(rep, indent=2) + "\n")
    cov = rep["coverage"]
    print(f"Stage 0 floor study: {cov['total_obs']} obs / {cov['snapshots']} snapshots "
          f"({cov['tail_bucket_obs']} in tail buckets) -> {out.name}")
    for b in rep["tail_buckets"]:
        print(f"  tail {b['bucket']}: spread {b['median_spread']} · "
              f"all-in LB {b['allin_roundtrip_cost_lower_bound']} · "
              f"n={b['n_obs']}/{b['n_markets']}mkts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
