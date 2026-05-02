"""Data layer — pulls 5-minute OHLCV bars from Alpaca and writes to bars.

Idempotent: re-running over the same window is safe (UPSERT on
(symbol, timestamp)). Every run writes a row to the runs table — success
or failure. The runs table is the audit trail; its writes are non-negotiable.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Protocol

from dotenv import load_dotenv

import db
from config import BAR_TIMEFRAME_MINUTES, WATCHED_SYMBOLS

load_dotenv()


@dataclass(frozen=True)
class Bar:
    symbol: str
    timestamp: str  # ISO 8601 UTC
    open: float
    high: float
    low: float
    close: float
    volume: float


class BarSource(Protocol):
    def get_bars(self, symbols: list[str], start: datetime, end: datetime) -> list[Bar]: ...


class AlpacaBarSource:
    """Live Alpaca crypto-data bar source. Reads credentials from env."""

    def __init__(self) -> None:
        api_key = os.environ.get("ALPACA_API_KEY")
        secret_key = os.environ.get("ALPACA_SECRET_KEY")
        if not api_key or not secret_key:
            raise RuntimeError(
                "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env"
            )

        from alpaca.data.historical import CryptoHistoricalDataClient
        from alpaca.data.requests import CryptoBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        self._client = CryptoHistoricalDataClient(api_key=api_key, secret_key=secret_key)
        self._request_cls = CryptoBarsRequest
        self._timeframe = TimeFrame(BAR_TIMEFRAME_MINUTES, TimeFrameUnit.Minute)

    def get_bars(self, symbols: list[str], start: datetime, end: datetime) -> list[Bar]:
        request = self._request_cls(
            symbol_or_symbols=symbols,
            timeframe=self._timeframe,
            start=start,
            end=end,
        )
        bar_set = self._client.get_crypto_bars(request)
        out: list[Bar] = []
        for symbol, rows in bar_set.data.items():
            for r in rows:
                ts = r.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                out.append(
                    Bar(
                        symbol=symbol,
                        timestamp=ts.astimezone(timezone.utc).isoformat(),
                        open=float(r.open),
                        high=float(r.high),
                        low=float(r.low),
                        close=float(r.close),
                        volume=float(r.volume),
                    )
                )
        return out


def upsert_bars(conn: sqlite3.Connection, bars: Iterable[Bar], fetched_at: str) -> int:
    rows = [
        (b.symbol, b.timestamp, b.open, b.high, b.low, b.close, b.volume, fetched_at)
        for b in bars
    ]
    if not rows:
        return 0
    cur = conn.executemany(
        """
        INSERT INTO bars (symbol, timestamp, open, high, low, close, volume, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol, timestamp) DO UPDATE SET
            open=excluded.open,
            high=excluded.high,
            low=excluded.low,
            close=excluded.close,
            volume=excluded.volume,
            fetched_at=excluded.fetched_at
        """,
        rows,
    )
    return cur.rowcount if cur.rowcount and cur.rowcount > 0 else len(rows)


def _record_run_start(conn: sqlite3.Connection, started_at: str) -> int:
    cur = conn.execute(
        "INSERT INTO runs (started_at, status) VALUES (?, 'in_progress')",
        (started_at,),
    )
    return int(cur.lastrowid) if cur.lastrowid is not None else -1


def _record_run_finish(
    conn: sqlite3.Connection,
    run_id: int,
    finished_at: str,
    status: str,
    bars_added: int = 0,
    error_text: str | None = None,
) -> None:
    conn.execute(
        """
        UPDATE runs
           SET finished_at = ?, status = ?, bars_added = ?, error_text = ?
         WHERE id = ?
        """,
        (finished_at, status, bars_added, error_text, run_id),
    )


def fetch_window(
    source: BarSource,
    symbols: list[str],
    start: datetime,
    end: datetime,
    db_path: Path | None = None,
) -> tuple[int, int]:
    """Fetch bars from `source` for `symbols` in [start, end] and upsert.

    Returns (run_id, bars_added). Logs success or failure to the runs table.
    """
    started_at = datetime.now(timezone.utc).isoformat()

    with db.connect(db_path) as conn:
        run_id = _record_run_start(conn, started_at)

    bars_added = 0
    error_text: str | None = None
    status = "ok"

    try:
        bars = source.get_bars(symbols, start, end)
        with db.connect(db_path) as conn:
            bars_added = upsert_bars(conn, bars, fetched_at=started_at)
    except Exception as exc:
        status = "failed"
        error_text = f"{type(exc).__name__}: {exc}"

    finished_at = datetime.now(timezone.utc).isoformat()
    with db.connect(db_path) as conn:
        _record_run_finish(
            conn, run_id, finished_at, status, bars_added=bars_added, error_text=error_text
        )

    if status == "failed":
        raise RuntimeError(f"fetch failed: {error_text}")
    return run_id, bars_added


def fetch_recent(
    source: BarSource | None = None,
    minutes: int = 60,
    db_path: Path | None = None,
) -> tuple[int, int]:
    """Fetch the last N minutes of bars for all WATCHED_SYMBOLS."""
    src = source or AlpacaBarSource()
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)
    return fetch_window(src, WATCHED_SYMBOLS, start, end, db_path=db_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch recent bars from Alpaca")
    parser.add_argument("--minutes", type=int, default=60, help="lookback window")
    args = parser.parse_args()

    db.migrate()
    run_id, n = fetch_recent(minutes=args.minutes)
    print(f"run_id={run_id} bars_added={n}")
