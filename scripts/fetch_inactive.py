"""B2 fix — enqueue DELISTED/inactive names and fetch their bars, so the
equity archive stops being survivor-biased (decision-log 2026-07-20).
Reuses fetch_equities' migrate/fetch_dailies; additive, network-only.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.fetch_equities import (DB_PATH, HEADERS, TRADE_API, EXCHANGES,
                                    fetch_dailies, migrate)


def main() -> int:
    migrate()
    r = requests.get(f"{TRADE_API}/v2/assets",
                     params={"status": "inactive", "asset_class": "us_equity"},
                     headers=HEADERS, timeout=30)
    r.raise_for_status()
    inactive = [a["symbol"] for a in r.json()
                if a.get("exchange") in EXCHANGES
                and a["symbol"].isalpha() and len(a["symbol"]) <= 5]
    print(f"inactive major-exchange names: {len(inactive)}")
    with sqlite3.connect(DB_PATH) as conn:
        for sym in inactive:
            conn.execute(
                "INSERT OR IGNORE INTO universe (symbol, name, exchange,"
                " dollar_vol, fetched) VALUES (?, '', '', 0, 0)", (sym,))
    fetch_dailies(inactive, years=10)
    with sqlite3.connect(DB_PATH) as conn:
        n = conn.execute("SELECT COUNT(*) FROM daily_bars").fetchone()[0]
        s = conn.execute("SELECT COUNT(DISTINCT symbol) FROM daily_bars").fetchone()[0]
    print(f"archive now: {n:,} bars across {s} symbols (survivorship-corrected)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
