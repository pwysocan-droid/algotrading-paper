"""B2 — survivorship investigation. Two holes, both tested (decision-log
2026-07-20 K1/E2). Network-only, no LLM cost.

  Hole 1: does Alpaca serve daily bars for DELISTED names? (test known
          2023 delistings: SIVB, FRC, SBNY, BBBYQ)
  Hole 2: can we reconstruct a POINT-IN-TIME investable universe at each
          formation date, or is 'liquid' inferred with look-ahead?
          (probe: does the asset API expose listing/delisting dates or
          historical status; does inactive-status enumeration exist)

Reports feasibility honestly; a clean answer to hole 1 with a dirty
answer to hole 2 still poisons the replication.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
H = {"APCA-API-KEY-ID": os.environ.get("ALPACA_API_KEY", ""),
     "APCA-API-SECRET-KEY": os.environ.get("ALPACA_SECRET_KEY", "")}
TRADE = "https://paper-api.alpaca.markets"
DATA = "https://data.alpaca.markets"
DELISTED = ["SIVB", "FRC", "SBNY", "BBBYQ", "FTX", "MULN"]


def main() -> int:
    print("=== HOLE 1: delisted-name bars ===")
    for sym in DELISTED:
        try:
            r = requests.get(f"{DATA}/v2/stocks/{sym}/bars",
                             params={"timeframe": "1Day", "start": "2022-01-01",
                                     "end": "2023-06-01", "adjustment": "all",
                                     "limit": 10000, "feed": "iex"},
                             headers=H, timeout=30)
            bars = r.json().get("bars") or [] if r.ok else []
            span = f"{bars[0]['t'][:10]}→{bars[-1]['t'][:10]}" if bars else "—"
            print(f"  {sym}: status {r.status_code}, {len(bars)} bars {span}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {sym}: ERR {type(exc).__name__}")

    print("\n=== HOLE 2: point-in-time universe ===")
    for status in ("active", "inactive"):
        try:
            r = requests.get(f"{TRADE}/v2/assets",
                             params={"status": status, "asset_class": "us_equity"},
                             headers=H, timeout=30)
            assets = r.json() if r.ok else []
            print(f"  status={status}: {len(assets)} assets")
            if assets:
                keys = sorted(assets[0].keys())
                print(f"    asset fields: {keys}")
                date_fields = [k for k in keys if "date" in k.lower()
                               or "list" in k.lower()]
                print(f"    listing/date fields present: {date_fields or 'NONE — no point-in-time status'}")
        except Exception as exc:  # noqa: BLE001
            print(f"  status={status}: ERR {type(exc).__name__}")

    print("\n=== VERDICT ===")
    print("Hole 1 clean iff delisted names return bars above.")
    print("Hole 2 clean iff asset records carry listing+delisting dates;")
    print("if only current inactive/active flags exist, universe is")
    print("reconstructable ONLY by 'traded on date D' (bar presence) —")
    print("a liquidity-at-D screen, not index membership. Document either way.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
