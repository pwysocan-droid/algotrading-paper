"""The live paper-trading cycle: signals → execution → exits.

Called by vps/cron-fetch.sh every 5 minutes, right after fetch.py, so the
loop runs on fresh bars. This is the stage the W29 review flagged as
missing ("2016 successful runs, 0 decisions" — a pipeline that terminated
before the only stage that matters). Each phase is independent: an
exception in one is reported but does not block the others, and every
row it produces (signals, decisions, trades) is its own audit trail.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import db
import execute
import signals
from config import WATCHED_SYMBOLS


def run_cycle(db_path: Path | None = None, now: datetime | None = None) -> dict[str, int]:
    """One full cycle. Returns counts for the cron log."""
    ts = now or datetime.now(timezone.utc)

    # Exits FIRST so freed slots/exposure are available to this cycle's
    # entries — mirrors replay.apply_portfolio_constraints, which frees
    # ledger positions before admitting same-bar candidates (audit
    # 2026-07-17). Each phase isolated: one failure must not stop the
    # others — especially exit management on open positions.
    counts = {"signals": 0, "placed": 0, "closed": 0, "errors": 0}
    try:
        counts["closed"] = execute.manage_exits(db_path=db_path, now=ts)
    except Exception as exc:
        counts["errors"] += 1
        print(f"ERROR manage_exits: {type(exc).__name__}: {exc}")
    try:
        counts["signals"] = len(signals.run_all_variants(WATCHED_SYMBOLS, db_path=db_path))
    except Exception as exc:
        counts["errors"] += 1
        print(f"ERROR signals: {type(exc).__name__}: {exc}")
    try:
        counts["placed"] = execute.process_pending(db_path=db_path, now=ts)
    except Exception as exc:
        counts["errors"] += 1
        print(f"ERROR execute: {type(exc).__name__}: {exc}")
    return counts


def main() -> int:
    db.migrate()
    counts = run_cycle()
    print(
        f"cycle: signals={counts['signals']} placed={counts['placed']} "
        f"closed={counts['closed']} errors={counts['errors']}"
    )
    return 1 if counts["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
