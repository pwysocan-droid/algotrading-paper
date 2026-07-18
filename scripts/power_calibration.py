"""Power calibration — can our gauntlet even see the edges we hunt?

Tier-0 elicitation (2026-07-18) verdict: "a pipeline that has never
measured its own power may never have been running an experiment at
all." This answers it. Method: the null arm's constrained 930d replay
gives the realistic per-trade net-return distribution under our exact
cost/constraint model. Bootstrap subsamples of size n, shift the mean
by a known planted edge, and measure how often our standard verdict
rules fire:

  - PASS rule (kill bar): mean net return > +0.3%/trade
  - SIGN rule: total net P&L > 0 (what a naive reading of the
    gauntlet table implies)

Power = detection rate with a real planted edge. False-positive rate =
the same rules firing at edge 0. Every past and future verdict should
be read against this table.

    python scripts/power_calibration.py [--db research_bars.db]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
import replay
from config import SLIPPAGE_PCT, STRATEGY_VARIANTS, TAKER_FEE_PCT, WATCHED_SYMBOLS

REPO_ROOT = Path(__file__).resolve().parent.parent

EDGES_PCT = [0.0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2]   # planted mean shift, %/trade
SAMPLE_NS = [7, 30, 100, 300, 600]                  # realized ns from real rounds
DRAWS = 4000
KILL_BAR_PCT = 0.3


def _rand(seed: str) -> float:
    """Deterministic uniform [0,1) — reproducible without random module."""
    h = hashlib.sha256(seed.encode()).hexdigest()
    return int(h[:12], 16) / float(16 ** 12)


def null_trade_returns(db_path: Path) -> list[float]:
    """Per-trade NET pnl_pct of the null arm over the full window under
    real costs and portfolio constraints — the honest noise
    distribution of this platform."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=930)
    variant = dict(STRATEGY_VARIANTS["null_baseline"])
    variant["enabled"] = True
    with db.connect(db_path) as conn:
        trades = replay.replay_variant(
            conn, "null_baseline", variant, WATCHED_SYMBOLS, start, end,
            fee_pct=TAKER_FEE_PCT, slippage_pct=SLIPPAGE_PCT,
        )
    trades = replay.apply_portfolio_constraints(trades)
    # net-of-fees per-trade return (%): pnl_usd / notional
    return [
        t.pnl_usd / (t.qty * t.entry_price) * 100.0
        for t in trades
        if t.accepted and t.pnl_usd is not None and t.qty * t.entry_price > 0
    ]


def bootstrap_power(returns: list[float]) -> list[dict]:
    m = len(returns)
    out = []
    for edge in EDGES_PCT:
        for n in SAMPLE_NS:
            pass_hits = sign_hits = 0
            for d in range(DRAWS):
                total = 0.0
                for k in range(n):
                    idx = int(_rand(f"{edge}:{n}:{d}:{k}") * m)
                    total += returns[idx] + edge
                mean = total / n
                if mean > KILL_BAR_PCT:
                    pass_hits += 1
                if mean > 0:
                    sign_hits += 1
            out.append({
                "edge_pct": edge, "n": n,
                "p_pass_kill_bar": pass_hits / DRAWS,
                "p_positive_pnl": sign_hits / DRAWS,
            })
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=REPO_ROOT / "research_bars.db")
    args = parser.parse_args()

    returns = null_trade_returns(args.db)
    n = len(returns)
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    print(f"null distribution: n={n} mean={mean:.3f}% std={var ** 0.5:.3f}%")

    rows = bootstrap_power(returns)
    date = datetime.now(timezone.utc).date().isoformat()
    out = REPO_ROOT / "reports" / f"power-calibration-{date}.json"
    out.write_text(json.dumps({
        "date": date,
        "null_n": n, "null_mean_pct": mean, "null_std_pct": var ** 0.5,
        "kill_bar_pct": KILL_BAR_PCT, "draws": DRAWS,
        "rows": rows,
    }, indent=2) + "\n")

    print(f"\n{'edge %/tr':>10} | " + " | ".join(f"n={n_:>4}" for n_ in SAMPLE_NS)
          + "   (P[mean > +0.3% kill bar])")
    for edge in EDGES_PCT:
        cells = [r for r in rows if r["edge_pct"] == edge]
        print(f"{edge:>10.1f} | " + " | ".join(
            f"{c['p_pass_kill_bar']:>6.0%}" for c in cells))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
