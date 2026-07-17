"""Weekly sim-to-live calibration — does the factory predict the pipe?

For each enabled variant, compares LIVE outcomes (trades table since the
live loop started) against a BACKTEST of the same variant over the same
window on the same bars, with the same costs. If the factory's replay
can't predict live behavior for strategies running in production, its
gauntlet verdicts on new candidates deserve no trust — this report is
the standing check the W29 review demanded.

Writes reports/calibration-YYYY-MM-DD.md (the Friday investigator reads
reports/). Run weekly by cron-friday.sh before the review.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
import replay
from config import SLIPPAGE_PCT, STRATEGY_VARIANTS, TAKER_FEE_PCT, WATCHED_SYMBOLS

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_LOOP_START = "2026-07-16T21:00:00+00:00"  # first live cycle


def live_stats(conn, name: str) -> dict:
    r = conn.execute(
        """
        SELECT COUNT(*) AS placed,
               SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed,
               SUM(CASE WHEN status='closed' AND pnl_usd>0 THEN 1 ELSE 0 END) AS wins,
               COALESCE(SUM(CASE WHEN status='closed' THEN pnl_usd END),0) AS pnl,
               SUM(CASE WHEN exit_reason='stop_loss' THEN 1 ELSE 0 END) AS stops,
               SUM(CASE WHEN exit_reason='take_profit' THEN 1 ELSE 0 END) AS targets,
               SUM(CASE WHEN exit_reason='time_exit' THEN 1 ELSE 0 END) AS times
          FROM trades WHERE variant_name = ? AND entry_time >= ?
        """,
        (name, LIVE_LOOP_START),
    ).fetchone()
    return dict(r)


def backtest_stats(conn, name: str, variant: dict, start, end) -> dict:
    v = dict(variant)
    v["enabled"] = True
    trades = replay.replay_variant(
        conn, name, v, WATCHED_SYMBOLS, start, end,
        fee_pct=TAKER_FEE_PCT, slippage_pct=SLIPPAGE_PCT,
    )
    trades = replay.apply_portfolio_constraints(trades)
    placed = [t for t in trades if t.accepted]
    closed = [t for t in placed if t.pnl_usd is not None]
    return {
        "placed": len(placed),
        "closed": len(closed),
        "wins": sum(1 for t in closed if t.pnl_usd > 0),
        "pnl": sum(t.pnl_usd for t in closed),
        "stops": sum(1 for t in closed if t.exit_reason == "stop_loss"),
        "targets": sum(1 for t in closed if t.exit_reason == "take_profit"),
        "times": sum(1 for t in closed if t.exit_reason == "time_exit"),
    }


def main() -> int:
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(LIVE_LOOP_START)
    lines = [
        f"# Sim-to-live calibration — {now.date().isoformat()}",
        "",
        f"Window: {LIVE_LOOP_START} → {now.isoformat()} · identical bars, "
        f"costs, and constraints on both sides. Divergence here means the "
        f"factory's verdicts on candidates deserve less trust.",
        "",
        "| variant | side | placed | closed | wins | P&L | stop/tp/time |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    with db.connect() as conn:
        for name, variant in STRATEGY_VARIANTS.items():
            if not variant.get("enabled"):
                continue
            lv = live_stats(conn, name)
            bt = backtest_stats(conn, name, variant, start, now)
            for side, s in (("live", lv), ("sim", bt)):
                lines.append(
                    f"| {name} | {side} | {s['placed']} | {s['closed'] or 0} "
                    f"| {s['wins'] or 0} | ${(s['pnl'] or 0):,.2f} "
                    f"| {s['stops'] or 0}/{s['targets'] or 0}/{s['times'] or 0} |"
                )
    lines += ["", "Small windows are noisy — divergence matters once closed "
              "counts reach ~30/side. Deterministic variants should match "
              "near-exactly; see parity_check.py for the per-signal version.",
              ""]
    out = REPO_ROOT / "reports" / f"calibration-{now.date().isoformat()}.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
