"""E2 round one — the equity cross-sectional gauntlet.

Scores a slate of PRICE/VOLUME factors uniformly (no fundamentals in the
archive) the same way round zero validated momentum: point-in-time
universe (trailing-60d $vol top-N, delisted names included), long-only
top-decile tilt, EXCESS over the equal-weight-universe benchmark (the
drift null — founding equity lesson), regime-split across five windows,
pooled t. Survivorship-corrected archive, −30% involuntary delisting
haircut.

Discipline carried from crypto: beat the BENCHMARK not zero; regime-
condition (Lesson 23); trust direction over magnitude; and — because
this tests N factors at once — apply a best-of-N multiple-testing
haircut before any factor is called a candidate. Gross excess only here
(net-of-turnover-cost + holdout are the next stage for any survivor).

    python scripts/equity_gauntlet.py
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
M, TOPN, DECILE, HAIRCUT = 21, 500, 0.10, 0.30
NEED = 252            # max lookback any factor needs
WINDOWS = {"2016-2019": ("2016-01-01", "2020-01-01"),
           "2020-2021": ("2020-01-01", "2022-01-01"),
           "2022-2023": ("2022-01-01", "2024-01-01"),
           "2024-2026": ("2024-01-01", "2026-07-01")}

# each factor: signal(closes, vols, j) -> float; HIGHER = long-preferred
def f_momentum(c, v, j):   return c[j - 21] / c[j - 252] - 1.0            # 12-1
def f_lowvol(c, v, j):
    rets = [c[i] / c[i - 1] - 1.0 for i in range(j - 59, j + 1) if c[i - 1] > 0]
    return -statistics.pstdev(rets) if len(rets) > 5 else 0.0             # low vol ranks high
def f_reversal(c, v, j):   return -(c[j] / c[j - 21] - 1.0)               # buy 1m losers
def f_52whigh(c, v, j):    return c[j] / max(c[j - 252:j + 1])            # near 52w high
FACTORS = {"momentum_12_1": f_momentum, "low_vol_60": f_lowvol,
           "reversal_1m": f_reversal, "high_52w_prox": f_52whigh}


def mean_se(xs):
    n = len(xs)
    if n < 2:
        return None, None, n
    m = sum(xs) / n
    se = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5
    return m, se, n


def main() -> int:
    conn = sqlite3.connect(DB)
    data: dict = {}
    for sym, day, close, vol in conn.execute(
            "SELECT symbol, day, close, volume FROM daily_bars ORDER BY symbol, day"):
        d = data.setdefault(sym, ([], [], []))
        d[0].append(day); d[1].append(close); d[2].append(vol)
    data = {s: v for s, v in data.items() if len(v[0]) >= NEED + 25}
    print(f"{len(data)} symbols usable")
    gdays = sorted({d for v in data.values() for d in v[0]})

    # per-factor per-window monthly excess series
    series = {f: {w: [] for w in WINDOWS} for f in FACTORS}
    for D in gdays[NEED::M]:
        wname = next((w for w, (a, b) in WINDOWS.items() if a <= D < b), None)
        if wname is None:
            continue
        cutoff = (date.fromisoformat(D) - timedelta(days=7)).isoformat()
        elig = []          # (sym, closes, vols, j, dv, fwd)
        for sym, (days, closes, vols) in data.items():
            j = bisect.bisect_right(days, D) - 1
            if j < NEED or days[j] < cutoff or closes[j] <= 0 or closes[j - 252] <= 0:
                continue
            dv = sum(closes[j - k] * vols[j - k] for k in range(60))
            fwd = (closes[j + 21] / closes[j] - 1.0) if j + 21 < len(days) \
                else (closes[-1] * (1 - HAIRCUT)) / closes[j] - 1.0
            elig.append((sym, closes, vols, j, dv, fwd))
        if len(elig) < 100:
            continue
        elig.sort(key=lambda t: -t[4])
        univ = elig[:TOPN]
        bench = sum(t[5] for t in univ) / len(univ)
        k = max(1, int(len(univ) * DECILE))
        for fname, fn in FACTORS.items():
            scored = sorted(univ, key=lambda t: fn(t[1], t[2], t[3]))
            top = sum(t[5] for t in scored[-k:]) / k
            series[fname][wname].append((top - bench) * 100.0)

    out = {"date": datetime.now(timezone.utc).date().isoformat(),
           "note": "gross excess over equal-weight benchmark; N=4 factors "
                   "-> best-of-N haircut applies; net-of-cost + holdout are next",
           "factors": {}}
    print(f"\n{'factor':<16} {'pooled excess/mo':>16} {'t':>6} {'n':>4}   per-window t")
    for fname in FACTORS:
        pooled = [x for w in WINDOWS for x in series[fname][w]]
        pm, pse, pn = mean_se(pooled)
        wt = {}
        for w in WINDOWS:
            wm, wse, wn = mean_se(series[fname][w])
            wt[w] = None if (wm is None or not wse) else round(wm / wse, 2)
        out["factors"][fname] = {
            "pooled_excess_mo_pct": None if pm is None else round(pm, 3),
            "pooled_t": None if (pm is None or not pse) else round(pm / pse, 2),
            "n_months": pn, "window_t": wt}
        tstr = " ".join(f"{w[:4]}:{wt[w]}" for w in WINDOWS)
        print(f"{fname:<16} {(pm or 0):>+15.3f}% {(pm/pse if pm and pse else 0):>+6.2f} "
              f"{pn:>4}   {tstr}")

    (REPO / "reports" / f"equity-gauntlet-{out['date']}.json").write_text(
        json.dumps(out, indent=2) + "\n")
    print("\nwrote report · reminder: best-of-4 selection inflates the top "
          "factor's t; a ~sqrt(2 ln 4)=1.7 hurdle applies before 'candidate'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
