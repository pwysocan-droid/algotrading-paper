"""Read-only Kalshi market-data adapter — Charter E Stage 0 measurement.

MEASUREMENT ONLY. This module hits the PUBLIC /markets endpoint (no auth, no
credentials) and must NEVER gain a function that places, modifies, or cancels an
order. Stage 0 is a venue cost-floor study; trading is a separately authorized
stage that does not exist yet. See book/pre-reg-charter-E.md + RECALIBRATION_REVIEW.md.
"""
from __future__ import annotations

import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"


def _f(x):
    return None if x is None else float(x)


def fetch_markets(status="open", max_pages=800, page=1000, session=None):
    """Paginate GET /markets and return normalized two-sided quotes. Prices from
    the `*_dollars` fields (0.00–1.00); sizes are raw `*_fp` (scale unverified —
    spread, not depth, is the primary Stage 0 quantity).

    NOTE: max_pages defaults HIGH on purpose. The original default (30 → 30k
    markets) SILENTLY TRUNCATED the population and hid the near-certainty (>90¢)
    tail entirely (Kalshi has >600k open markets; near-certainties are ~72 of
    them, ordered beyond the first 30k). That is the 'no silent caps' lesson —
    a bounded fetch read as 'this side doesn't exist' when it was just cut off."""
    s = session or requests.Session()
    out, cursor = [], None
    for _ in range(max_pages):
        params = {"limit": page, "status": status}
        if cursor:
            params["cursor"] = cursor
        r = s.get(f"{BASE}/markets", params=params, timeout=20)
        r.raise_for_status()
        j = r.json()
        markets = j.get("markets") or []
        for m in markets:
            yb, ya = _f(m.get("yes_bid_dollars")), _f(m.get("yes_ask_dollars"))
            two_sided = yb is not None and ya is not None
            out.append({
                "ticker": m.get("ticker"), "event_ticker": m.get("event_ticker"),
                "title": m.get("title"), "status": m.get("status"),
                "yes_bid": yb, "yes_ask": ya,
                "no_bid": _f(m.get("no_bid_dollars")), "no_ask": _f(m.get("no_ask_dollars")),
                "last_price": _f(m.get("last_price_dollars")),
                "yes_bid_size": m.get("yes_bid_size_fp"),
                "yes_ask_size": m.get("yes_ask_size_fp"),
                "volume": m.get("volume_fp"), "open_interest": m.get("open_interest_fp"),
                "liquidity": _f(m.get("liquidity_dollars")),
                "close_time": m.get("close_time"),
                "spread": (ya - yb) if two_sided else None,
                "mid": ((ya + yb) / 2) if two_sided else None,
            })
        cursor = j.get("cursor")
        if not cursor or not markets:
            break
    return out
