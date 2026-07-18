"""Backfill funding-rate history — the backfillable part of Layer-2.

Critique finding (2026-07-18 closing-move session): forward-only
collection pays full price for a partly backfillable good. Binance
serves complete funding-rate history (3 settlements/day) via public
pagination; open-interest history only ~30 days (forward tape covers
it); book snapshots are not backfillable (forward tape only). This
pulls all available funding history into context.db.

Runs on the VPS (Binance blocks US IPs). Idempotent: UNIQUE(symbol, ts)
+ INSERT OR IGNORE, so re-runs only fill gaps.

    python scripts/backfill_funding.py
"""

from __future__ import annotations

import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.collect_context import DB_PATH, FAPI, SYMBOLS, TIMEOUT

START_MS = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def migrate_funding(db_path: Path = DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS funding_history (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL,
                ts TEXT NOT NULL,
                rate REAL NOT NULL,
                UNIQUE(symbol, ts)
            )
            """
        )


def backfill_symbol(conn: sqlite3.Connection, symbol: str, binance: str) -> int:
    inserted = 0
    start = START_MS
    while True:
        r = requests.get(
            f"{FAPI}/fapi/v1/fundingRate",
            params={"symbol": binance, "startTime": start, "limit": 1000},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            break
        for row in rows:
            ts = datetime.fromtimestamp(
                int(row["fundingTime"]) / 1000, tz=timezone.utc
            ).replace(microsecond=0).isoformat()
            cur = conn.execute(
                "INSERT OR IGNORE INTO funding_history (symbol, ts, rate)"
                " VALUES (?, ?, ?)",
                (symbol, ts, float(row["fundingRate"])),
            )
            inserted += cur.rowcount
        last = int(rows[-1]["fundingTime"])
        if len(rows) < 1000:
            break
        start = last + 1
        time.sleep(0.3)  # stay far under rate limits
    return inserted


def main() -> int:
    migrate_funding()
    with sqlite3.connect(DB_PATH) as conn:
        for symbol, binance in SYMBOLS.items():
            n = backfill_symbol(conn, symbol, binance)
            total = conn.execute(
                "SELECT COUNT(*) FROM funding_history WHERE symbol = ?", (symbol,)
            ).fetchone()[0]
            print(f"{symbol}: +{n} rows (total {total})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
