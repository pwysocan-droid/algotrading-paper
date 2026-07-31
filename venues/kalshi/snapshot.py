"""Snapshot Kalshi two-sided quotes into a LOCAL SQLite DB (gitignored).

Disk-safe by design: raw snapshots are NEVER committed to git (heeds the
trader.db 28 GB bloat lesson — only the compact floor-report JSON is committed).
Own DB file, single-writer, no trader.db writes. Minimal liquidity screen: store
only markets with a real two-sided quote.
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from adapter import fetch_markets  # noqa: E402

DB = HERE / "kalshi.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots(
  ts TEXT NOT NULL, ticker TEXT NOT NULL, event_ticker TEXT,
  mid REAL, spread REAL, yes_bid REAL, yes_ask REAL,
  yes_bid_size REAL, yes_ask_size REAL, volume REAL, open_interest REAL,
  liquidity REAL, close_time TEXT,
  PRIMARY KEY (ts, ticker));
"""


def snapshot_once(db=DB):
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    kept = 0
    for m in fetch_markets(status="open"):
        if m["yes_bid"] is None or m["yes_ask"] is None:
            continue                      # liquidity screen: two-sided quote only
        con.execute(
            "INSERT OR IGNORE INTO snapshots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ts, m["ticker"], m["event_ticker"], m["mid"], m["spread"],
             m["yes_bid"], m["yes_ask"], m["yes_bid_size"], m["yes_ask_size"],
             m["volume"], m["open_interest"], m["liquidity"], m["close_time"]))
        kept += 1
    con.commit()
    con.close()
    return ts, kept


if __name__ == "__main__":
    t, n = snapshot_once()
    print(f"kalshi snapshot {t}: {n} two-sided markets -> {DB}")
