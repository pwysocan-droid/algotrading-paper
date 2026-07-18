"""Layer-2 context collector — recording what OHLCV throws away.

Information-audit finding (2026-07-18): funding rates, open interest,
and order-book shape are where documented short-horizon crypto effects
live, and book snapshots cannot be bought retroactively — every day
not collecting is information permanently destroyed. This starts the
tape rolling NOW; strategies that consume it come later (Layer-2
revival, build_queue.md).

Sources: Binance public endpoints (no key; reachable from the VPS's
EU IP — blocked from US IPs, so this runs on the VPS only). Writes to
context.db — a SEPARATE database, deliberately: trader.db's schema is
locked architecture and this never touches it.

Run every 5 minutes by vps/cron-context.sh; one snapshot per symbol
per invocation. All failures degrade to NULL columns, never a crash.
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "context.db"

SYMBOLS = {  # our symbol -> Binance perp/spot symbol
    "BTC/USD": "BTCUSDT",
    "ETH/USD": "ETHUSDT",
    "SOL/USD": "SOLUSDT",
    "LINK/USD": "LINKUSDT",
    "AVAX/USD": "AVAXUSDT",
}
FAPI = "https://fapi.binance.com"
SPOT = "https://api.binance.com"
TIMEOUT = 10


def migrate(db_path: Path = DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS context_snapshots (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL,
                ts TEXT NOT NULL,
                funding_rate REAL,
                mark_price REAL,
                next_funding_time TEXT,
                open_interest REAL,
                bid REAL,
                ask REAL,
                spread_pct REAL,
                depth_imbalance REAL,
                UNIQUE(symbol, ts)
            )
            """
        )


def depth_imbalance(bids: list, asks: list) -> float | None:
    """(bid qty − ask qty) / total over the visible book: +1 all bids,
    −1 all asks. Pure function so it's unit-testable."""
    bid_qty = sum(float(q) for _p, q in bids)
    ask_qty = sum(float(q) for _p, q in asks)
    total = bid_qty + ask_qty
    if total <= 0:
        return None
    return (bid_qty - ask_qty) / total


def _get(url: str, params: dict) -> dict | None:
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as exc:  # noqa: BLE001 — one bad endpoint must not stop the tape
        print(f"WARN {url.rsplit('/', 1)[-1]} {params.get('symbol')}: {type(exc).__name__}")
        return None


def snapshot(symbol: str, binance: str) -> dict:
    row: dict = {"symbol": symbol,
                 "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
    prem = _get(f"{FAPI}/fapi/v1/premiumIndex", {"symbol": binance})
    if prem and "lastFundingRate" in prem:
        row["funding_rate"] = float(prem["lastFundingRate"])
        row["mark_price"] = float(prem["markPrice"])
        row["next_funding_time"] = datetime.fromtimestamp(
            int(prem["nextFundingTime"]) / 1000, tz=timezone.utc).isoformat()
    oi = _get(f"{FAPI}/fapi/v1/openInterest", {"symbol": binance})
    if oi and "openInterest" in oi:
        row["open_interest"] = float(oi["openInterest"])
    book = _get(f"{SPOT}/api/v3/depth", {"symbol": binance, "limit": 20})
    if book and book.get("bids") and book.get("asks"):
        bid = float(book["bids"][0][0])
        ask = float(book["asks"][0][0])
        row["bid"], row["ask"] = bid, ask
        mid = (bid + ask) / 2
        if mid > 0:
            row["spread_pct"] = (ask - bid) / mid * 100.0
        row["depth_imbalance"] = depth_imbalance(book["bids"], book["asks"])
    return row


def main() -> int:
    migrate()
    cols = ["symbol", "ts", "funding_rate", "mark_price", "next_funding_time",
            "open_interest", "bid", "ask", "spread_pct", "depth_imbalance"]
    n_ok = 0
    with sqlite3.connect(DB_PATH) as conn:
        for symbol, binance in SYMBOLS.items():
            row = snapshot(symbol, binance)
            conn.execute(
                f"INSERT OR IGNORE INTO context_snapshots ({','.join(cols)}) "
                f"VALUES ({','.join('?' * len(cols))})",
                [row.get(c) for c in cols],
            )
            if row.get("funding_rate") is not None or row.get("bid") is not None:
                n_ok += 1
    print(f"context snapshot: {n_ok}/{len(SYMBOLS)} symbols captured")
    return 0


if __name__ == "__main__":
    sys.exit(main())
