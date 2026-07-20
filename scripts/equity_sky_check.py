"""E1 — is the equity sky alive at retail horizons? (first light)

Three measurements on the E0 archive, every cell reported, no
selection, regime-split from day one (Lesson 23):

  1. Directional TS momentum (long/short by trailing-return sign) vs
     zero — drift-free signal check, the measurement that exposed the
     crypto epoch flip.
  2. Long-or-flat momentum vs drift — the drift-timing view.
  3. Cross-sectional momentum: rank by trailing 6m return skipping the
     latest month (6-1), decile long-short spread over the next month —
     the classic equity anomaly, breadth-powered.

Costs: ~0.05% round-trip on liquid names — noted, not modeled; any
result within ±0.1%/month of zero is inside the cost floor anyway.
Survivorship caveat inherited from E0 and stamped on the output.

    python scripts/equity_sky_check.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent
DB = REPO_ROOT / "equities.db"
WINDOWS = {
    "2016-2019": ("2016-01-01", "2020-01-01"),
    "2020-2021": ("2020-01-01", "2022-01-01"),
    "2022": ("2022-01-01", "2023-01-01"),
    "2023": ("2023-01-01", "2024-01-01"),
    "2024-2026": ("2024-01-01", "2026-07-01"),
}
M = 21  # trading days per month
GRID = [(lb, h) for lb in (1, 3, 6) for h in (1, 3, 6)]


def mean_se(xs):
    n = len(xs)
    if n < 2:
        return None, None, n
    m = sum(xs) / n
    se = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5
    return m, se, n


def main() -> int:
    conn = sqlite3.connect(DB)
    symbols = [r[0] for r in conn.execute(
        "SELECT symbol FROM universe ORDER BY dollar_vol DESC LIMIT 1000")]
    series: dict[str, tuple[list[str], list[float]]] = {}
    for s in symbols:
        rows = conn.execute(
            "SELECT day, close FROM daily_bars WHERE symbol=? ORDER BY day", (s,)
        ).fetchall()
        if len(rows) >= 300:
            series[s] = ([r[0] for r in rows], [r[1] for r in rows])
    print(f"{len(series)} symbols with usable history")

    out: dict = {"survivorship_caveat": True}
    for wname, (a, b) in WINDOWS.items():
        # --- time-series grids (on the top 200 by dollar volume for speed)
        ts_dir, ts_flat = {}, {}
        for lb, hold in GRID:
            dir_x, flat_x, drift_x = [], [], []
            for s in list(series)[:200]:
                days, closes = series[s]
                idx = [i for i, d in enumerate(days) if a <= d < b]
                if not idx:
                    continue
                i = idx[0] + lb * M
                while i + hold * M <= idx[-1]:
                    past, now = closes[i - lb * M], closes[i]
                    if past > 0 and now > 0:
                        fwd = (closes[i + hold * M] / now - 1.0) * 100
                        sign = 1.0 if now / past > 1 else -1.0
                        dir_x.append(sign * fwd)
                        flat_x.append(fwd if sign > 0 else 0.0)
                        drift_x.append(fwd)
                    i += hold * M
            m_dir, _, n = mean_se(dir_x)
            m_fl, _, _ = mean_se(flat_x)
            m_dr, _, _ = mean_se(drift_x)
            key = f"lb{lb}h{hold}"
            ts_dir[key] = {"n": n, "mean_pct": None if m_dir is None else round(m_dir, 2)}
            ts_flat[key] = {
                "n": n,
                "incr_vs_drift": None if (m_fl is None or m_dr is None)
                else round(m_fl - m_dr, 2),
            }
        dvals = [v["mean_pct"] for v in ts_dir.values() if v["mean_pct"] is not None]
        pos = sum(1 for x in dvals if x > 0)

        # --- cross-sectional 6-1 momentum decile spread, monthly
        spreads = []
        # month anchors from the first symbol's calendar
        cal = [d for d in series[symbols[0]][0] if a <= d < b][::M]
        for t in range(7, len(cal) - 1):
            d_rank, d_next = cal[t], cal[t + 1]
            scored = []
            for s, (days, closes) in series.items():
                dmap = {d: c for d, c in zip(days, closes)}
                def px(day):
                    return dmap.get(day)
                p0, p_skip, p_now, p_fwd = (px(cal[t - 7]), px(cal[t - 1]),
                                            px(d_rank), px(d_next))
                if None in (p0, p_skip, p_now, p_fwd) or p0 <= 0 or p_now <= 0:
                    continue
                mom = p_skip / p0 - 1.0          # 6m return, skip latest month
                fwd = (p_fwd / p_now - 1.0) * 100
                scored.append((mom, fwd))
            if len(scored) < 100:
                continue
            scored.sort(key=lambda x: x[0])
            dec = len(scored) // 10
            lo = sum(x[1] for x in scored[:dec]) / dec
            hi = sum(x[1] for x in scored[-dec:]) / dec
            spreads.append(hi - lo)
        m_cs, se_cs, n_cs = mean_se(spreads)

        out[wname] = {
            "ts_directional": {"cells_positive": f"{pos}/{len(dvals)}",
                               "mean_pct": round(sum(dvals) / len(dvals), 2) if dvals else None,
                               "cells": ts_dir},
            "ts_long_or_flat_incr": ts_flat,
            "cross_sectional_6_1": {"n_months": n_cs,
                                    "monthly_spread_pct": None if m_cs is None else round(m_cs, 2),
                                    "se": None if se_cs is None else round(se_cs, 2)},
        }
        print(f"{wname}: TS-directional {pos}/{len(dvals)} cells positive "
              f"(mean {sum(dvals)/len(dvals):+.2f}%) · "
              f"CS 6-1 spread {m_cs:+.2f}%±{se_cs:.2f}/mo (n={n_cs})"
              if dvals and m_cs is not None else f"{wname}: insufficient data")

    date = datetime.now(timezone.utc).date().isoformat()
    (REPO_ROOT / "reports" / f"equity-sky-check-{date}.json").write_text(
        json.dumps({"date": date, "windows": out}, indent=2) + "\n")
    print("wrote report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
