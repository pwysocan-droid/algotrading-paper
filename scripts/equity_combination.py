"""E2 combination stage — do the sub-threshold scraps clear the floor jointly?

The fee floor binds per DEPLOYED RULE, not per signal. A multi-factor
composite (a) may capture decorrelated bits of edge each factor has
alone, and (b) rebalances LESS than any single factor because the
factors partially offset — lower turnover, lower cost drag. Tests
z-scored composites vs the momentum-alone baseline, reporting gross
excess, information ratio, the decile's own vol vs benchmark, TURNOVER,
and a turnover-adjusted net estimate. Point-in-time, survivorship-
corrected, benchmark-relative, monthly.
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
TOPN, DECILE, HAIRCUT, NEED, H = 500, 0.10, 0.30, 252, 21
COST_ONEWAY = 0.05   # % per leg (equity liquid)


def f_momentum(c, v, j): return c[j - 21] / c[j - 252] - 1.0
def f_lowvol(c, v, j):
    r = [c[i] / c[i - 1] - 1.0 for i in range(j - 59, j + 1) if c[i - 1] > 0]
    return -statistics.pstdev(r) if len(r) > 5 else 0.0
def f_reversal(c, v, j): return -(c[j] / c[j - 21] - 1.0)
def f_52whigh(c, v, j): return c[j] / max(c[j - 252:j + 1])
FACTORS = {"mom": f_momentum, "lowvol": f_lowvol, "rev": f_reversal, "hi52": f_52whigh}
# composites as weighted z-score blends
COMPOSITES = {
    "mom_only":       {"mom": 1},
    "mom+lowvol":     {"mom": 1, "lowvol": 1},
    "mom+lowvol+rev": {"mom": 1, "lowvol": 1, "rev": 1},
    "all4":           {"mom": 1, "lowvol": 1, "rev": 1, "hi52": 1},
}


def zscore(vals):
    m = statistics.mean(vals)
    sd = statistics.pstdev(vals) or 1.0
    return [(x - m) / sd for x in vals]


def stats(xs):
    n = len(xs)
    if n < 3:
        return None
    m = statistics.mean(xs); sd = statistics.pstdev(xs)
    return m, (sd / n ** 0.5 if n else 0), sd, n


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

    excess = {c: [] for c in COMPOSITES}
    dret = {c: [] for c in COMPOSITES}
    prev_top = {c: None for c in COMPOSITES}
    turnover = {c: [] for c in COMPOSITES}
    bret = []
    for D in gdays[NEED::H]:
        cutoff = (date.fromisoformat(D) - timedelta(days=7)).isoformat()
        elig = []
        for sym, (days, closes, vols) in data.items():
            j = bisect.bisect_right(days, D) - 1
            if j < NEED or days[j] < cutoff or closes[j] <= 0 or closes[j - 252] <= 0:
                continue
            dv = sum(closes[j - k] * vols[j - k] for k in range(60))
            fwd = (closes[j + H] / closes[j] - 1.0) if j + H < len(days) \
                else (closes[-1] * (1 - HAIRCUT)) / closes[j] - 1.0
            elig.append([sym, closes, vols, j, dv, fwd])
        if len(elig) < 100:
            continue
        elig.sort(key=lambda t: -t[4])
        univ = elig[:TOPN]
        bench = sum(t[5] for t in univ) / len(univ)
        bret.append(bench)
        # z-score each raw factor across the universe
        zf = {}
        for fk, fn in FACTORS.items():
            zf[fk] = zscore([fn(t[1], t[2], t[3]) for t in univ])
        k = max(1, int(len(univ) * DECILE))
        for cname, weights in COMPOSITES.items():
            comp = [sum(w * zf[fk][i] for fk, w in weights.items())
                    for i in range(len(univ))]
            order = sorted(range(len(univ)), key=lambda i: comp[i])
            top_idx = order[-k:]
            top_syms = frozenset(univ[i][0] for i in top_idx)
            tm = sum(univ[i][5] for i in top_idx) / k
            excess[cname].append((tm - bench) * 100.0)
            dret[cname].append(tm)
            if prev_top[cname] is not None:
                churned = len(top_syms - prev_top[cname]) / k
                turnover[cname].append(churned)
            prev_top[cname] = top_syms

    bench_vol = statistics.pstdev(bret) if len(bret) > 2 else 1.0
    per_yr = 252 / H
    out = {"date": datetime.now(timezone.utc).date().isoformat(), "composites": {}}
    print(f"{'composite':<16}{'gross/mo':>10}{'t':>7}{'ann_IR':>8}"
          f"{'vol/bench':>11}{'turnover':>10}{'net/mo est':>12}")
    for cname in COMPOSITES:
        s = stats(excess[cname])
        if not s:
            continue
        m, se, sd, n = s
        t = m / se if se else 0
        ir = m / sd * per_yr ** 0.5 if sd else 0
        tvr = statistics.mean(turnover[cname]) if turnover[cname] else 0
        net = m - tvr * COST_ONEWAY * 2          # buy+sell the churned fraction
        vr = statistics.pstdev(dret[cname]) / bench_vol if bench_vol else 0
        out["composites"][cname] = {"gross_mo_pct": round(m, 3), "t": round(t, 2),
            "ann_IR": round(ir, 2), "vol_over_bench": round(vr, 2),
            "turnover": round(tvr, 2), "net_mo_pct_est": round(net, 3), "n": n}
        print(f"{cname:<16}{m:>+9.3f}%{t:>+7.2f}{ir:>+8.2f}{vr:>11.2f}"
              f"{tvr:>10.2f}{net:>+11.3f}%")
    (REPO / "reports" / f"equity-combination-{out['date']}.json").write_text(
        json.dumps(out, indent=2) + "\n")
    print("\nread: does any composite beat mom_only on IR AND clear net>0? "
          "lower turnover = the cost-floor advantage of blending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
