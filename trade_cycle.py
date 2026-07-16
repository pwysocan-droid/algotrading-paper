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

    emitted = signals.run_all_variants(WATCHED_SYMBOLS, db_path=db_path)
    placed = execute.process_pending(db_path=db_path)
    closed = execute.manage_exits(db_path=db_path, now=ts)

    return {"signals": len(emitted), "placed": placed, "closed": closed}


def main() -> int:
    db.migrate()
    counts = run_cycle()
    print(
        f"cycle: signals={counts['signals']} "
        f"placed={counts['placed']} closed={counts['closed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
