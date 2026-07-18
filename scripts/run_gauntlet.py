"""The gauntlet — score the LLM-surfaced candidates over the 6-month window.

Each candidate runs alone through replay_variant (real fees + slippage)
and apply_portfolio_constraints (cooldown/exposure/concurrency), exactly
the pipeline that exposed the textbook strategies. Scored by the fitness
function Phase 1 discovered: edge per constraint slot = net P&L per
placed trade. Output: reports/gauntlet-YYYY-MM-DD.md with the ranking.

Registration of the top 2 is a separate, human-reviewed config change —
this script measures, it does not promote.

    python scripts/run_gauntlet.py [--days 180]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
import replay
from config import SLIPPAGE_PCT, STRATEGY_VARIANTS, TAKER_FEE_PCT, WATCHED_SYMBOLS

CANDIDATES = [
    "liquidation_cascade_reclaim",
    "btc_leads_alt_lag_capture",
    "dead_zone_range_break",
    "volume_thrust_regime_shift",
    "weekend_illiquidity_momentum",
]


def _score_candidate(args: tuple) -> dict:
    """One candidate, one window — importable top-level so multiprocessing
    (spawn, macOS default) can pickle it. Each worker opens its own
    read-only-use sqlite connection."""
    name, days, db_path_str = args[:3]
    fill_model = args[3] if len(args) > 3 else "taker"
    db_path = Path(db_path_str) if db_path_str else None
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    window_days = float(days)

    variant = dict(STRATEGY_VARIANTS[name])
    variant["enabled"] = True  # local copy only — config stays disabled
    with db.connect(db_path) as conn:
        trades = replay.replay_variant(
            conn, name, variant, WATCHED_SYMBOLS, start, end,
            fee_pct=TAKER_FEE_PCT, slippage_pct=SLIPPAGE_PCT,
            fill_model=fill_model,
        )
    candidates_n = len(trades)
    trades = replay.apply_portfolio_constraints(trades)
    placed = [t for t in trades if t.accepted]
    pnls = [t.pnl_usd for t in placed if t.pnl_usd is not None]
    pcts = [t.pnl_pct for t in placed if t.pnl_pct is not None]
    total = sum(pnls)
    n = len(placed)
    wins = sum(1 for p in pnls if p > 0)
    return {
        "name": name,
        "fill_model": fill_model,
        "candidates": candidates_n,
        "placed": n,
        "total_pnl": total,
        "edge_per_slot": total / n if n else None,
        "win_rate": wins / n if n else None,
        "sharpe": replay.sharpe_ratio(pcts, window_days),
        "max_dd": replay.max_drawdown_pct(pnls),
        "days": days,
        # Trade-level records — learning-quality audit 2026-07-18: the
        # aggregates above answer "did it die"; pooled per-trade data
        # across ALL ideas is what lets anyone later ask "under what
        # conditions did everything win a little" (cross-idea meta-
        # analysis, regime slicing, ablation re-scoring). Never discard.
        "trades": [
            {
                "symbol": t.symbol, "side": t.side,
                "entry_ts": t.entry_bar_timestamp, "exit_ts": t.exit_bar_timestamp,
                "entry_px": t.entry_price, "exit_px": t.exit_price,
                "exit_reason": t.exit_reason, "pnl_usd": t.pnl_usd,
                "pnl_pct": t.pnl_pct, "fees_usd": t.fees_usd,
            }
            for t in placed
        ],
    }


def run_gauntlet(days: int = 180, db_path: Path | None = None,
                 names: list[str] | None = None,
                 fill_model: str = "taker") -> list[dict]:
    """All candidates in parallel — one process each (they're independent
    and CPU-bound; observed ~4x wall-clock on this hardware)."""
    from multiprocessing import Pool, cpu_count

    todo = names if names is not None else CANDIDATES
    args = [(n, days, str(db_path) if db_path else None, fill_model) for n in todo]
    with Pool(min(len(args), max(1, cpu_count() - 1))) as pool:
        results = pool.map(_score_candidate, args)
    for r in results:
        eps = "—" if r["placed"] == 0 else f"${r['total_pnl'] / r['placed']:,.3f}"
        print(f"{r['name']} ({days}d): candidates={r['candidates']} "
              f"placed={r['placed']} pnl=${r['total_pnl']:,.2f} edge/slot={eps}")

    results.sort(key=lambda r: (r["edge_per_slot"] is not None, r["edge_per_slot"] or 0),
                 reverse=True)
    return results


def run_staged(filter_days: int = 180, full_days: int = 930,
               db_path: Path | None = None,
               names: list[str] | None = None,
               fill_model: str = "taker") -> list[dict]:
    """Curriculum-cascade: a cheap short-window filter kills the obvious
    deaths (>=30 placed and net-negative); only survivors earn the full
    multi-year window. Small samples pass the filter — they haven't
    earned a verdict either way."""
    todo = names if names is not None else CANDIDATES
    stage1 = run_gauntlet(days=filter_days, db_path=db_path, names=todo,
                          fill_model=fill_model)
    survivors, killed = [], []
    for r in stage1:
        if r["placed"] >= 30 and r["total_pnl"] < 0:
            r["stage"] = f"killed@{filter_days}d"
            killed.append(r)
        else:
            survivors.append(r["name"])
    print(f"\nstage 1: {len(killed)} killed, {len(survivors)} advance to {full_days}d\n")
    stage2 = []
    if survivors:
        stage2 = run_gauntlet(days=full_days, db_path=db_path, names=survivors,
                              fill_model=fill_model)
        for r in stage2:
            r["stage"] = f"full@{full_days}d"
    results = stage2 + killed
    results.sort(key=lambda r: (r["edge_per_slot"] is not None, r["edge_per_slot"] or 0),
                 reverse=True)
    return results


def render_report(results: list[dict], days: int, now: datetime | None = None) -> str:
    ts = now or datetime.now(timezone.utc)
    em = "—"
    lines = [
        "# algotrading-paper / candidate gauntlet",
        "",
        f"{days}d constrained replay · fees {TAKER_FEE_PCT:.2%}/leg · "
        f"slippage {SLIPPAGE_PCT:.2%}/leg · ranked by edge per constraint slot",
        "",
        ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "",
        "| # | Candidate | candidates | placed | net P&L | edge/slot | win rate | Sharpe | max DD |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for i, r in enumerate(results, 1):
        lines.append(
            f"| {i} | `{r['name']}` | {r['candidates']:,} | {r['placed']:,} "
            f"| ${r['total_pnl']:,.2f} "
            f"| {em if r['edge_per_slot'] is None else f'${r['edge_per_slot']:,.3f}'} "
            f"| {em if r['win_rate'] is None else f'{r['win_rate']:.1%}'} "
            f"| {em if r['sharpe'] is None else f'{r['sharpe']:.2f}'} "
            f"| {em if r['max_dd'] is None else f'{r['max_dd']:.1f}%'} |"
        )
    lines += [
        "",
        "Notes: each candidate replayed alone under the full portfolio",
        "constraints; live behavior with a shared ceiling will differ. The",
        "gauntlet measures; registration of the top 2 is a reviewed config",
        "change plus a decision-log entry. n < 30 placed means any claim",
        "is statistically unreliable regardless of sign (small-sample trap).",
        "",
        "---",
        "",
        "generated by scripts/run_gauntlet.py",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the candidate gauntlet")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--db", type=Path, default=None,
                        help="alternate bars database (e.g. research_bars.db)")
    parser.add_argument("--names", default=None,
                        help="comma-separated variant names (default: the synthesis candidates)")
    parser.add_argument("--fill-model", default="taker", choices=["taker", "maker"],
                        help="fill model axis (decision-log 2026-07-17: test both)")
    parser.add_argument("--staged", action="store_true",
                        help="cheap short-window filter first; only survivors run the full window")
    parser.add_argument("--filter-days", type=int, default=180,
                        help="stage-1 window for --staged (default 180)")
    args = parser.parse_args()

    names = [n.strip() for n in args.names.split(",") if n.strip()] if args.names else None

    if args.db is None:
        db.migrate()
    if args.staged:
        results = run_staged(filter_days=args.filter_days, full_days=args.days,
                             db_path=args.db, names=names, fill_model=args.fill_model)
    else:
        results = run_gauntlet(days=args.days, db_path=args.db, names=names,
                               fill_model=args.fill_model)
    report = render_report(results, args.days)
    stamp = datetime.now(timezone.utc)
    base = Path(__file__).resolve().parent.parent / "reports"
    # timestamped (not just dated) so same-day runs never clobber each other
    tag = stamp.strftime("%Y-%m-%dT%H%M")
    out = base / f"gauntlet-{tag}.md"
    out.write_text(report)
    # machine-readable twin for the dashboard's results-by-date page
    import json as _json
    (base / f"gauntlet-{tag}.json").write_text(_json.dumps({
        "date": stamp.date().isoformat(),
        "generated_at": stamp.isoformat(),
        "days": args.days,
        "staged": args.staged,
        "fill_model": args.fill_model,
        "database": str(args.db) if args.db else "trader.db",
        "results": results,
    }, indent=2) + "\n")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
