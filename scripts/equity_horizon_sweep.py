"""E2 round 1b — horizon sweep + risk-adjusted scoring.

Answers two questions the monthly-only round one couldn't:
  1. HORIZON: is the thin result a horizon artifact? Re-run the four
     price factors at weekly (5d), monthly (21d), quarterly (63d)
     rebalance/hold. Short-term reversal should light up weekly if it
     exists; momentum should prefer longer holds.
  2. YARDSTICK: report the annualized INFORMATION RATIO of each tilt
     (mean/std of per-rebalance excess) alongside raw excess — the
     right lens for low-vol, which is a risk-adjusted effect. Also the
     decile's own return volatility vs benchmark (does low-vol deliver
     the lower-risk half of its thesis).

Same point-in-time, survivorship-corrected, benchmark-relative,
regime-pooled discipline. Best-of-(4×3) selection now — a stiffer
multiple-testing hurdle (~sqrt(2 ln 12)=2.2t) applies to any winner.
"""
from __future__ import annotations

import bisect
import json
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sqlite3

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "equities.db"
TOPN, DECILE, HAIRCUT, NEED = 500, 0.10, 0.30, 252
HORIZONS = {"weekly": 5, "monthly": 21, "quarterly": 63}


def f_momentum(c, v, j): return c[j - 21] / c[j - 252] - 1.0
def f_lowvol(c, v, j):
    rets = [c[i] / c[i - 1] - 1.0 for i in range(j - 59, j + 1) if c[i - 1] > 0]
    return -statistics.pstdev(rets) if len(rets) > 5 else 0.0
def f_reversal(c, v, j): return -(c[j] / c[j - 21] - 1.0)
def f_52whigh(c, v, j): return c[j] / max(c[j - 252:j + 1])
FACTORS = {"momentum_12_1": f_momentum, "low_vol_60": f_lowvol,
           "reversal_1m": f_reversal, "high_52w_prox": f_52whigh}


def stats(xs):
    n = len(xs)
    if n < 3:
        return None
    m = statistics.mean(xs)
    sd = statistics.pstdev(xs)
    se = statistics.pstdev(xs) / n ** 0.5
    return m, se, sd, n


def main() -> int:
    conn = sqlite3.connect(DB)
    data: dict = {}
    for sym, day, close, vol in conn.execute(
            "SELECT symbol, day, close, volume FROM daily_bars ORDER BY symbol, day"):
        d = data.setdefault(sym, ([], [], []))
        d[0].append(day); d[1].append(close); d[2].append(vol)
    data = {s: v for s, v in data.items() if len(v[0]) >= NEED + 25}
    gdays = sorted({d for v in data.values() for d in v[0]})
    print(f"{len(data)} symbols\n")
    print(f"{'factor':<16}{'horizon':<11}{'excess/reb':>11}{'t':>7}{'ann_IR':>8}"
          f"{'decile_vol/bench':>18}")

    out = {"date": datetime.now(timezone.utc).date().isoformat(), "cells": {}}
    for hname, H in HORIZONS.items():
        anchors = gdays[NEED::H]
        rows = {f: [] for f in FACTORS}          # per-reb excess
        dret = {f: [] for f in FACTORS}          # decile absolute fwd
        bret = []                                # benchmark absolute fwd
        for D in anchors:
            cutoff = (date.fromisoformat(D) - timedelta(days=7)).isoformat()
            elig = []
            for sym, (days, closes, vols) in data.items():
                j = bisect.bisect_right(days, D) - 1
                if j < NEED or days[j] < cutoff or closes[j] <= 0 or closes[j - 252] <= 0:
                    continue
                dv = sum(closes[j - k] * vols[j - k] for k in range(60))
                fwd = (closes[j + H] / closes[j] - 1.0) if j + H < len(days) \
                    else (closes[-1] * (1 - HAIRCUT)) / closes[j] - 1.0
                elig.append((sym, closes, vols, j, dv, fwd))
            if len(elig) < 100:
                continue
            elig.sort(key=lambda t: -t[4])
            univ = elig[:TOPN]
            bench = sum(t[5] for t in univ) / len(univ)
            bret.append(bench)
            k = max(1, int(len(univ) * DECILE))
            for fn_name, fn in FACTORS.items():
                sc = sorted(univ, key=lambda t: fn(t[1], t[2], t[3]))
                top_fwd = [t[5] for t in sc[-k:]]
                tm = sum(top_fwd) / len(top_fwd)
                rows[fn_name].append((tm - bench) * 100.0)
                dret[fn_name].append(tm)
        per_yr = 252 / H
        bench_vol = statistics.pstdev(bret) if len(bret) > 2 else 1.0
        for fn_name in FACTORS:
            s = stats(rows[fn_name])
            if not s:
                continue
            m, se, sd, n = s
            t = m / se if se else 0.0
            ir = (m / sd * per_yr ** 0.5) if sd else 0.0
            dv_ratio = (statistics.pstdev(dret[fn_name]) / bench_vol
                        if bench_vol else 0.0)
            out["cells"][f"{fn_name}/{hname}"] = {
                "excess_per_reb_pct": round(m, 3), "t": round(t, 2),
                "ann_IR": round(ir, 2), "decile_vol_over_bench": round(dv_ratio, 2),
                "n": n}
            print(f"{fn_name:<16}{hname:<11}{m:>+10.3f}%{t:>+7.2f}{ir:>+8.2f}"
                  f"{dv_ratio:>18.2f}")
    (REPO / "reports" / f"equity-horizon-sweep-{out['date']}.json").write_text(
        json.dumps(out, indent=2) + "\n")
    print("\nbest-of-12 hurdle ~2.2t · IR is the cost-agnostic consistency "
          "lens · low_vol decile_vol_over_bench<1 = it delivers the low-risk half")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
