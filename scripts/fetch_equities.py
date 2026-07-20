"""E0 — equities daily-bar archive (the second sky's raw material).

Two phases, resumable and unsupervised:
  A. Universe: all active tradable US equities on major exchanges via
     the trading API, ranked by dollar volume from latest snapshots;
     keep the top N (default 2000). Survivorship bias is ACKNOWLEDGED
     and recorded — a today-defined universe bakes in winners; every
     conclusion drawn from this archive carries that caveat until a
     point-in-time universe exists.
  B. Ten years of daily bars, split+dividend adjusted, one symbol per
     request (well inside rate limits), into equities.db (gitignored
     research artifact, like research_bars.db).

    python scripts/fetch_equities.py [--top 2000] [--years 10]
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "equities.db"
HEADERS = {
    "APCA-API-KEY-ID": os.environ.get("ALPACA_API_KEY", ""),
    "APCA-API-SECRET-KEY": os.environ.get("ALPACA_SECRET_KEY", ""),
}
TRADE_API = "https://paper-api.alpaca.markets"
DATA_API = "https://data.alpaca.markets"
EXCHANGES = {"NYSE", "NASDAQ", "ARCA", "AMEX", "BATS"}


def migrate() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_bars (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL, day TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL, volume REAL,
                UNIQUE(symbol, day)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS universe (
                symbol TEXT PRIMARY KEY, name TEXT, exchange TEXT,
                dollar_vol REAL, fetched INTEGER DEFAULT 0
            )
            """
        )


def build_universe(top: int) -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        done = conn.execute("SELECT COUNT(*) FROM universe").fetchone()[0]
        if done >= top:
            return [r[0] for r in conn.execute(
                "SELECT symbol FROM universe ORDER BY dollar_vol DESC LIMIT ?",
                (top,))]
    r = requests.get(f"{TRADE_API}/v2/assets",
                     params={"status": "active", "asset_class": "us_equity"},
                     headers=HEADERS, timeout=30)
    r.raise_for_status()
    assets = [a for a in r.json()
              if a.get("tradable") and a.get("exchange") in EXCHANGES
              and a["symbol"].isalpha() and len(a["symbol"]) <= 5]
    print(f"universe: {len(assets)} candidate assets; ranking by dollar volume")
    ranked = []
    syms = [a["symbol"] for a in assets]
    names = {a["symbol"]: (a.get("name", ""), a.get("exchange", "")) for a in assets}
    for i in range(0, len(syms), 100):
        batch = syms[i:i + 100]
        try:
            resp = requests.get(
                f"{DATA_API}/v2/stocks/snapshots",
                params={"symbols": ",".join(batch), "feed": "iex"},
                headers=HEADERS, timeout=30)
            resp.raise_for_status()
            for sym, snap in resp.json().items():
                d = (snap or {}).get("dailyBar") or {}
                dv = float(d.get("c", 0)) * float(d.get("v", 0))
                if dv > 0 and float(d.get("c", 0)) >= 3.0:
                    ranked.append((sym, dv))
        except Exception as exc:  # noqa: BLE001
            print(f"WARN snapshot batch {i}: {type(exc).__name__}")
        time.sleep(0.35)
    ranked.sort(key=lambda t: -t[1])
    keep = ranked[:top]
    with sqlite3.connect(DB_PATH) as conn:
        for sym, dv in keep:
            nm, ex = names.get(sym, ("", ""))
            conn.execute(
                "INSERT OR REPLACE INTO universe (symbol, name, exchange, dollar_vol)"
                " VALUES (?, ?, ?, ?)", (sym, nm, ex, dv))
    print(f"universe: kept top {len(keep)} by dollar volume")
    return [s for s, _ in keep]


def fetch_dailies(symbols: list[str], years: int) -> None:
    start = (datetime.now(timezone.utc) - timedelta(days=365 * years)).date().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        pending = [s for s in symbols if conn.execute(
            "SELECT fetched FROM universe WHERE symbol = ?", (s,)
        ).fetchone()[0] == 0]
    print(f"fetching dailies for {len(pending)} symbols (resumable)")
    for idx, sym in enumerate(pending):
        try:
            page = None
            rows = []
            while True:
                params = {"timeframe": "1Day", "start": start,
                          "adjustment": "all", "limit": 10000, "feed": "iex"}
                if page:
                    params["page_token"] = page
                resp = requests.get(f"{DATA_API}/v2/stocks/{sym}/bars",
                                    params=params, headers=HEADERS, timeout=30)
                resp.raise_for_status()
                j = resp.json()
                rows += j.get("bars") or []
                page = j.get("next_page_token")
                if not page:
                    break
            with sqlite3.connect(DB_PATH) as conn:
                for b in rows:
                    conn.execute(
                        "INSERT OR IGNORE INTO daily_bars"
                        " (symbol, day, open, high, low, close, volume)"
                        " VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (sym, b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]))
                conn.execute("UPDATE universe SET fetched = 1 WHERE symbol = ?", (sym,))
        except Exception as exc:  # noqa: BLE001
            print(f"WARN {sym}: {type(exc).__name__}")
        if idx % 100 == 0:
            print(f"  {idx}/{len(pending)} done")
        time.sleep(0.31)  # ~190 req/min, under the limit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=2000)
    parser.add_argument("--years", type=int, default=10)
    args = parser.parse_args()
    if not HEADERS["APCA-API-KEY-ID"]:
        print("ALPACA_API_KEY missing")
        return 1
    migrate()
    symbols = build_universe(args.top)
    fetch_dailies(symbols, args.years)
    with sqlite3.connect(DB_PATH) as conn:
        n = conn.execute("SELECT COUNT(*) FROM daily_bars").fetchone()[0]
        s = conn.execute("SELECT COUNT(DISTINCT symbol) FROM daily_bars").fetchone()[0]
        span = conn.execute("SELECT MIN(day), MAX(day) FROM daily_bars").fetchone()
    print(f"DONE: {n:,} daily bars across {s} symbols · {span[0]} → {span[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
