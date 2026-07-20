"""Long-horizon natural experiment — is it the asset or the horizon that's dead?

Operator-designed probe (2026-07-20): momentum and carry at 1-6 MONTH
holds on daily bars derived from data already held. The short-horizon
apparatus measured its space empty; this asks whether the asset class
pays at horizons the apparatus never touched.

House disciplines: selection window only (through 2026-01-01, holdout
untouched); EVERY grid cell reported, no best-cell selection; the
drift null (unconditional same-window hold) printed beside every
momentum number — absolute positives at long holds are the
gross-positive trap in its longest coat yet. Costs (0.6% round-trip)
amortize to ~nothing at these holds and are noted, not modeled.

    python scripts/long_horizon_probe.py
"""

from __future__ import annotations

import json
import sqlite3
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
from config import WATCHED_SYMBOLS

REPO_ROOT = Path(__file__).resolve().parent.parent
SELECTION_END = "2026-01-01"
MONTH_D = 30
LOOKBACKS_M = [1, 3, 6]
HOLDS_M = [1, 3, 6]


def daily_closes(conn, symbol: str) -> tuple[list[str], list[float]]:
    rows = conn.execute(
        """
        SELECT substr(timestamp, 1, 10) AS day, close
          FROM bars WHERE symbol = ? AND timestamp < ?
         GROUP BY day HAVING timestamp = MAX(timestamp)
         ORDER BY day ASC
        """,
        (symbol, SELECTION_END),
    ).fetchall()
    return [r["day"] for r in rows], [r["close"] for r in rows]


def daily_funding(symbol: str) -> dict[str, float]:
    path = REPO_ROOT / "context.db"
    if not path.exists():
        return {}
    out: dict[str, list[float]] = {}
    with sqlite3.connect(path) as conn:
        for ts, rate in conn.execute(
            "SELECT ts, rate FROM funding_history WHERE symbol = ?", (symbol,)
        ):
            out.setdefault(ts[:10], []).append(rate)
    return {d: sum(v) / len(v) for d, v in out.items()}


def mean_se(xs):
    n = len(xs)
    if n < 2:
        return None, None, n
    m = sum(xs) / n
    se = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5
    return m, se, n


def main() -> int:
    grid: dict = {}
    carry: dict = {}
    with db.connect(REPO_ROOT / "research_bars.db") as conn:
        data = {s: daily_closes(conn, s) for s in WATCHED_SYMBOLS}
    funding = {s: daily_funding(s) for s in WATCHED_SYMBOLS}

    for lb in LOOKBACKS_M:
        for hold in HOLDS_M:
            mom, drift = [], []
            lb_d, hold_d = lb * MONTH_D, hold * MONTH_D
            for s in WATCHED_SYMBOLS:
                days, closes = data[s]
                # non-overlapping monthly anchors stepped by the hold
                i = lb_d
                while i + hold_d < len(closes):
                    past, now = closes[i - lb_d], closes[i]
                    fwd = closes[i + hold_d] / closes[i] - 1.0
                    if past > 0 and now > 0:
                        drift.append(fwd * 100)
                        sig = 1.0 if now / past - 1.0 > 0 else 0.0  # long-or-flat
                        mom.append(sig * fwd * 100)
                    i += hold_d
            m_m, se_m, n_m = mean_se(mom)
            m_d, se_d, n_d = mean_se(drift)
            grid[f"lb{lb}m_hold{hold}m"] = {
                "n": n_m,
                "momentum_mean_pct": m_m, "momentum_se": se_m,
                "drift_mean_pct": m_d, "drift_se": se_d,
                "increment_pct": (m_m - m_d) if (m_m is not None and m_d is not None) else None,
            }
            print(f"lb={lb}m hold={hold}m  n={n_m:>3}  "
                  f"momentum {m_m:+.1f}%±{se_m:.1f}  drift {m_d:+.1f}%±{se_d:.1f}  "
                  f"increment {m_m - m_d:+.1f}%")

    # carry probe: trailing-30d mean funding vs next-30d return, terciles
    lo_t, hi_t = [], []
    pooled = []
    for s in WATCHED_SYMBOLS:
        days, closes = data[s]
        f = funding[s]
        for i in range(30, len(closes) - 30):
            window = [f.get(d) for d in days[i - 30: i]]
            window = [x for x in window if x is not None]
            if len(window) < 20:
                continue
            avg_f = sum(window) / len(window)
            fwd = (closes[i + 30] / closes[i] - 1.0) * 100
            pooled.append((avg_f, fwd))
    if pooled:
        pooled.sort(key=lambda t: t[0])
        third = len(pooled) // 3
        lo_t = [x[1] for x in pooled[:third]]
        hi_t = [x[1] for x in pooled[-third:]]
        m_lo, se_lo, n_lo = mean_se(lo_t)
        m_hi, se_hi, n_hi = mean_se(hi_t)
        carry = {
            "note": "trailing-30d mean funding tercile -> next-30d return "
                    "(OVERLAPPING windows: SEs understated ~5x, direction only)",
            "low_funding_tercile": {"n": n_lo, "fwd_30d_pct": m_lo, "se": se_lo},
            "high_funding_tercile": {"n": n_hi, "fwd_30d_pct": m_hi, "se": se_hi},
        }
        print(f"\ncarry: low-funding tercile fwd30d {m_lo:+.1f}%±{se_lo:.1f} (n={n_lo}) · "
              f"high-funding tercile {m_hi:+.1f}%±{se_hi:.1f} (n={n_hi})")

    out = {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "window": f"selection only (through {SELECTION_END})",
        "design": "long-or-flat TS momentum vs unconditional drift, "
                  "non-overlapping holds, all cells reported",
        "grid": grid,
        "carry": carry,
    }
    path = REPO_ROOT / "reports" / f"long-horizon-probe-{out['date']}.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
