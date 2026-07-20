"""Regime-split momentum grid — is Lesson 22 structural or a window fact?

Same 9-cell measurement as the long-horizon probe (long-or-flat TS
momentum vs unconditional drift), run per regime window over the
2017-present daily bars. All cells, all windows, no selection.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent
SYMBOLS = ["BTC/USD", "ETH/USD", "SOL/USD", "LINK/USD", "AVAX/USD"]
WINDOWS = {
    "2017-2019 (early)": ("2017-08-17", "2020-01-01"),
    "2020-2021 (trend)": ("2020-01-01", "2022-01-01"),
    "2022 (bear)": ("2022-01-01", "2023-01-01"),
    "2023 (chop/recovery)": ("2023-01-01", "2024-01-01"),
    "2024-2025 (our archive)": ("2024-01-01", "2026-01-01"),
}
M = 30
GRID = [(lb, h) for lb in (1, 3, 6) for h in (1, 3, 6)]


def mean_se(xs):
    n = len(xs)
    if n < 2:
        return None, None, n
    m = sum(xs) / n
    se = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5
    return m, se, n


def closes_in(conn, symbol, a, b):
    return [r[0] for r in conn.execute(
        "SELECT close FROM daily_bars WHERE symbol=? AND day>=? AND day<?"
        " ORDER BY day ASC", (symbol, a, b))]


out = {}
with sqlite3.connect(REPO_ROOT / "context.db") as conn:
    for wname, (a, b) in WINDOWS.items():
        cells = {}
        for lb, hold in GRID:
            mom, drift = [], []
            for s in SYMBOLS:
                c = closes_in(conn, s, a, b)
                lb_d, hold_d = lb * M, hold * M
                i = lb_d
                while i + hold_d < len(c):
                    if c[i - lb_d] > 0 and c[i] > 0:
                        fwd = (c[i + hold_d] / c[i] - 1.0) * 100
                        drift.append(fwd)
                        mom.append(fwd if c[i] / c[i - lb_d] > 1.0 else 0.0)
                    i += hold_d
            m_m, _, n = mean_se(mom)
            m_d, _, _ = mean_se(drift)
            cells[f"lb{lb}h{hold}"] = {
                "n": n,
                "mom": None if m_m is None else round(m_m, 1),
                "drift": None if m_d is None else round(m_d, 1),
                "incr": None if (m_m is None or m_d is None) else round(m_m - m_d, 1),
            }
        incs = [c["incr"] for c in cells.values() if c["incr"] is not None]
        pos = sum(1 for x in incs if x > 0)
        out[wname] = {"cells": cells,
                      "cells_momentum_beats_drift": f"{pos}/{len(incs)}",
                      "mean_increment_pct": round(sum(incs) / len(incs), 1) if incs else None}
        print(f"{wname}: momentum beats drift in {pos}/{len(incs)} cells, "
              f"mean increment {out[wname]['mean_increment_pct']:+.1f}%")

date = datetime.now(timezone.utc).date().isoformat()
(REPO_ROOT / "reports" / f"regime-grid-{date}.json").write_text(
    json.dumps({"date": date, "windows": out}, indent=2) + "\n")
print("wrote report")
