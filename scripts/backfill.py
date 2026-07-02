"""Backfill historical bars for an arbitrary date range.

One-off / manual tool — not part of the recurring 5-min cron
(vps/cron-fetch.sh only ever calls fetch.py's recent-window path).
Reuses fetch.py's fetch_window() against AlpacaBarSource, writing one
runs row with kind='backfill'.

Per the single-writer discipline (queued as a decision-log entry after
the 2026-05-23 VPS migration): trader.db has one writer, the VPS. Run
this ON the VPS, not locally — a locally-produced trader.db diff creates
the same binary merge-conflict risk that already bit the migration once.

Usage (on the VPS):
    python scripts/backfill.py --start=2026-01-03 --end=2026-04-03
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Running as `python scripts/backfill.py` only puts scripts/ on sys.path,
# not the project root — same fix scripts/generate_surface.py already
# needed for its `import db`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
from config import WATCHED_SYMBOLS
from fetch import AlpacaBarSource, BarSource, fetch_window


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def run_backfill(
    start: datetime,
    end: datetime,
    symbols: list[str] | None = None,
    source: BarSource | None = None,
    db_path: Path | None = None,
) -> tuple[int, int]:
    """Fetch [start, end] for `symbols` (default WATCHED_SYMBOLS), kind='backfill'.

    Returns (run_id, bars_added). `source` is injectable for tests; a real
    invocation constructs AlpacaBarSource (requires ALPACA_* in .env).
    """
    if end <= start:
        raise ValueError(f"end ({end.isoformat()}) must be after start ({start.isoformat()})")
    src = source or AlpacaBarSource()
    syms = symbols or WATCHED_SYMBOLS
    return fetch_window(src, syms, start, end, db_path=db_path, kind="backfill")


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill historical bars for a date range")
    parser.add_argument("--start", required=True, help="ISO date, e.g. 2026-01-03")
    parser.add_argument("--end", required=True, help="ISO date, e.g. 2026-04-03")
    parser.add_argument(
        "--symbols", nargs="*", default=None,
        help="symbols to backfill (default: all WATCHED_SYMBOLS)",
    )
    args = parser.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)

    db.migrate()
    run_id, bars_added = run_backfill(start, end, symbols=args.symbols)
    print(
        f"run_id={run_id} bars_added={bars_added} "
        f"symbols={args.symbols or WATCHED_SYMBOLS} start={args.start} end={args.end}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
