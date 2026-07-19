"""Fragility re-analyses #2 and #3 — measuring the unmeasured control arms.

Run-4 fragility audit (2026-07-19): the most fragile epitaphs are
comparative claims where only one arm was measured. The two cheapest
decisive checks need no replay machinery, just bars:

  #2 post_shock_multiday_drift ("shock direction carries no 5-day
     signal", score 30): compute unconditional sign(shock)-aligned
     forward returns after EVERY qualifying shock bar — no barriers,
     no slots. Barrier outcomes measured path variance; this measures
     drift itself. Stakes: a false 'no drift' bricks up one of only
     two admissible territories.

  #3 pullback_to_breakout_level_limit ("the retest IS the failure
     signal", score 45): partition all qualifying breakouts into
     retested-within-2h vs never-retested and compare raw forward
     returns with no strategy machinery. If both populations perform
     alike, the death lived in the spec's mechanics, not in retests —
     and the maker-band lesson changes.

    python scripts/fragility_reanalysis.py [--db research_bars.db]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
from config import WATCHED_SYMBOLS

REPO_ROOT = Path(__file__).resolve().parent.parent


def load(conn, symbol):
    rows = conn.execute(
        "SELECT open, high, low, close, volume FROM bars"
        " WHERE symbol = ? ORDER BY timestamp ASC", (symbol,)).fetchall()
    return ([r["open"] for r in rows], [r["high"] for r in rows],
            [r["low"] for r in rows], [r["close"] for r in rows],
            [r["volume"] for r in rows])


def mean_se(xs):
    n = len(xs)
    if n < 2:
        return (None, None, n)
    m = sum(xs) / n
    se = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5
    return (m, se, n)


def shock_drift(conn) -> dict:
    """#2: sign-aligned forward returns after 3%-body/3x-volume shocks."""
    horizons = {"24h": 288, "72h": 864, "120h": 1440}
    out = {}
    aligned = {k: [] for k in horizons}
    for symbol in WATCHED_SYMBOLS:
        o, h, lo, c, v = load(conn, symbol)
        n = len(c)
        vmed = [0.0] * n
        window = []
        for i in range(n):
            if i >= 100:
                vmed[i] = statistics.median(v[i - 100:i])
            for name, k in horizons.items():
                pass
        for i in range(100, n - 1441):
            if o[i] <= 0 or vmed[i] <= 0:
                continue
            move = (c[i] - o[i]) / o[i]
            if abs(move) <= 0.03 or v[i] <= 3.0 * vmed[i]:
                continue
            sign = 1.0 if move > 0 else -1.0
            for name, k in horizons.items():
                if c[i] > 0 and c[i + k] > 0:
                    aligned[name].append(sign * (c[i + k] / c[i] - 1.0) * 100)
    for name in horizons:
        m, se, cnt = mean_se(aligned[name])
        out[name] = {"n": cnt, "mean_pct": m, "se_pct": se}
    return out


def breakout_retest(conn) -> dict:
    """#3: raw 24h forward returns, retested vs never-retested breakouts."""
    lvl_w, margin, vol_w, retest_w, fwd = 48, 0.005, 50, 24, 288
    retested, never = [], []
    for symbol in WATCHED_SYMBOLS:
        o, h, lo, c, v = load(conn, symbol)
        n = len(c)
        i = lvl_w + vol_w
        while i < n - fwd - retest_w:
            hi = max(h[i - lvl_w:i])
            med = statistics.median(v[i - vol_w:i])
            if med > 0 and c[i] > hi * (1 + margin) and v[i] > med and hi > 0:
                touch = any(lo[j] <= hi for j in range(i + 1, i + 1 + retest_w))
                ret = (c[i + fwd] / c[i] - 1.0) * 100 if c[i] > 0 else None
                if ret is not None:
                    (retested if touch else never).append(ret)
                i += retest_w  # one event per window — no overlap double-count
            else:
                i += 1
    m_r, se_r, n_r = mean_se(retested)
    m_n, se_n, n_n = mean_se(never)
    return {
        "retested": {"n": n_r, "mean_24h_pct": m_r, "se_pct": se_r},
        "never_retested": {"n": n_n, "mean_24h_pct": m_n, "se_pct": se_n},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=REPO_ROOT / "research_bars.db")
    args = parser.parse_args()
    with db.connect(args.db) as conn:
        drift = shock_drift(conn)
        retest = breakout_retest(conn)
    result = {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "fragile_2_shock_drift_sign_aligned": drift,
        "fragile_3_breakout_retest_raw": retest,
    }
    out = REPO_ROOT / "reports" / f"fragility-reanalysis-{result['date']}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
