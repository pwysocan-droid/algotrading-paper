"""Deep daily-bar history — the regime test's raw material.

Lesson 22 ("reversion at every measured horizon") is provisional until
the same grid runs over regimes our 2.5-year archive never saw —
especially the 2020-21 trend phase. Binance serves free daily klines
back to each pair's listing (BTC/ETH 2017, SOL 2020, LINK 2019,
AVAX 2020). Runs on the VPS (Binance blocks US IPs); writes
daily_bars into context.db; idempotent.

    python scripts/fetch_daily_history.py
"""

from __future__ import annotations

import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.collect_context import DB_PATH, SPOT, SYMBOLS, TIMEOUT

START_MS = int(datetime(2017, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def migrate(db_path: Path = DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_bars (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL,
                day TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL, volume REAL,
                UNIQUE(symbol, day)
            )
            """
        )


def backfill(conn: sqlite3.Connection, symbol: str, binance: str) -> int:
    inserted, start = 0, START_MS
    while True:
        r = requests.get(
            f"{SPOT}/api/v3/klines",
            params={"symbol": binance, "interval": "1d",
                    "startTime": start, "limit": 1000},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            break
        for k in rows:
            day = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).date().isoformat()
            cur = conn.execute(
                "INSERT OR IGNORE INTO daily_bars"
                " (symbol, day, open, high, low, close, volume)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (symbol, day, float(k[1]), float(k[2]), float(k[3]),
                 float(k[4]), float(k[5])),
            )
            inserted += cur.rowcount
        if len(rows) < 1000:
            break
        start = rows[-1][0] + 1
        time.sleep(0.3)
    return inserted


def main() -> int:
    migrate()
    with sqlite3.connect(DB_PATH) as conn:
        for symbol, binance in SYMBOLS.items():
            n = backfill(conn, symbol, binance)
            span = conn.execute(
                "SELECT MIN(day), MAX(day), COUNT(*) FROM daily_bars"
                " WHERE symbol = ?", (symbol,)).fetchone()
            print(f"{symbol}: +{n} · {span[0]} → {span[1]} ({span[2]} days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
