"""Exit-grid × fill-model sweep — stacking the horizon and cost levers.

Grid-searches one strategy's exit parameters (tp/sl/horizon) under both
taker (market-order) and maker (limit-order) fill models. This is
SELECTION, so it runs only on the selection window: history up to
2026-01-01. The 2026 holdout is never touched here — validate the single
chosen config on it separately, once (decision-log 2026-07-17 "Close the
seam": the holdout answers one question per candidate, ever).

    python scripts/exit_grid_sweep.py --strategy drawdown_regime_contrarian_gate \
        --db research_bars.db
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
import replay
from config import SLIPPAGE_PCT, STRATEGY_VARIANTS, TAKER_FEE_PCT, WATCHED_SYMBOLS

REPO_ROOT = Path(__file__).resolve().parent.parent
SELECTION_START = datetime(2024, 1, 1, tzinfo=timezone.utc)
SELECTION_END = datetime(2026, 1, 1, tzinfo=timezone.utc)  # holdout begins here

HORIZONS = [48, 72, 120, 168]
TP_SL = [(0.08, 0.04), (0.10, 0.04), (0.12, 0.05)]
FILL_MODELS = ["taker", "maker"]


def _score_cell(args: tuple) -> dict:
    """One grid cell — top-level so multiprocessing spawn can pickle it."""
    strategy_variant, hours, tp, sl, fill_model, db_path_str = args
    variant = json.loads(json.dumps(STRATEGY_VARIANTS[strategy_variant]))
    variant["enabled"] = True
    variant["params"] = {**variant["params"],
                         "tp": tp, "sl": sl, "time_exit_hours": hours}
    with db.connect(Path(db_path_str)) as conn:
        trades = replay.replay_variant(
            conn, strategy_variant, variant, WATCHED_SYMBOLS,
            SELECTION_START, SELECTION_END,
            fee_pct=TAKER_FEE_PCT, slippage_pct=SLIPPAGE_PCT,
            fill_model=fill_model,
        )
    candidates_n = len(trades)
    trades = replay.apply_portfolio_constraints(trades)
    placed = [t for t in trades if t.accepted]
    pnls = [t.pnl_usd for t in placed if t.pnl_usd is not None]
    pcts = [t.pnl_pct for t in placed if t.pnl_pct is not None]
    n = len(placed)
    window_days = (SELECTION_END - SELECTION_START).days
    return {
        "fill_model": fill_model, "time_exit_hours": hours, "tp": tp, "sl": sl,
        "candidates": candidates_n, "placed": n,
        "total_pnl": sum(pnls),
        "edge_per_slot": sum(pnls) / n if n else None,
        "win_rate": sum(1 for p in pnls if p > 0) / n if n else None,
        "total_fees": sum(t.fees_usd for t in placed),
        "sharpe": replay.sharpe_ratio(pcts, window_days),
        "max_dd": replay.max_drawdown_pct(pnls),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="drawdown_regime_contrarian_gate")
    parser.add_argument("--db", default=str(REPO_ROOT / "research_bars.db"))
    args = parser.parse_args()

    cells = [(args.strategy, h, tp, sl, fm, args.db)
             for fm, h, (tp, sl) in product(FILL_MODELS, HORIZONS, TP_SL)]
    print(f"{len(cells)} cells · selection window {SELECTION_START.date()} → "
          f"{SELECTION_END.date()} (holdout untouched)")

    from multiprocessing import Pool, cpu_count
    with Pool(min(8, cpu_count())) as pool:
        results = pool.map(_score_cell, cells)

    results.sort(key=lambda r: (r["edge_per_slot"] is None,
                                -(r["edge_per_slot"] or 0)))
    for r in results:
        eps = "—" if r["edge_per_slot"] is None else f"${r['edge_per_slot']:+.3f}"
        wr = "—" if r["win_rate"] is None else f"{r['win_rate']*100:.1f}%"
        print(f"{r['fill_model']:>5} {r['time_exit_hours']:>4}h "
              f"tp{r['tp']:.2f}/sl{r['sl']:.2f}  placed={r['placed']:>4} "
              f"pnl=${r['total_pnl']:>9,.2f} edge/slot={eps:>8} win={wr}")

    date = datetime.now(timezone.utc).date().isoformat()
    out = REPO_ROOT / "reports" / f"exit-grid-{args.strategy}-{date}.json"
    out.write_text(json.dumps({
        "strategy": args.strategy,
        "selection_window": [SELECTION_START.isoformat(), SELECTION_END.isoformat()],
        "holdout_touched": False,
        "results": results,
    }, indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
