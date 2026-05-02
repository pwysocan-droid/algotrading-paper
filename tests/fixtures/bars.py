"""Canned OHLCV bars for unit tests.

A fake BarSource that returns deterministic bars for any requested window.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from fetch import Bar


@dataclass
class FakeBarSource:
    """In-memory bar source. Returns the given bars filtered by window."""

    bars: list[Bar] = field(default_factory=list)
    raise_on_call: Exception | None = None
    call_count: int = 0

    def get_bars(self, symbols: list[str], start: datetime, end: datetime) -> list[Bar]:
        self.call_count += 1
        if self.raise_on_call is not None:
            raise self.raise_on_call
        symbol_set = set(symbols)
        out: list[Bar] = []
        for b in self.bars:
            if b.symbol not in symbol_set:
                continue
            ts = datetime.fromisoformat(b.timestamp)
            if start <= ts <= end:
                out.append(b)
        return out


def make_bar_series(
    symbol: str,
    start: datetime,
    n: int,
    interval_minutes: int = 5,
    base_price: float = 100.0,
) -> list[Bar]:
    """Generate `n` bars at fixed intervals with a deterministic price walk.

    Bars are simple — open == close == base_price + i, so tests that need
    distinct close-vs-next-open prices should use `make_bars_with_gap`.
    """
    out: list[Bar] = []
    ts = start
    for i in range(n):
        price = base_price + i
        out.append(
            Bar(
                symbol=symbol,
                timestamp=ts.astimezone(timezone.utc).isoformat(),
                open=price,
                high=price + 0.5,
                low=price - 0.5,
                close=price,
                volume=1000.0,
            )
        )
        ts = ts + timedelta(minutes=interval_minutes)
    return out


def make_bars_with_gap(
    symbol: str,
    start: datetime,
    closes: list[float],
    next_opens: list[float],
    interval_minutes: int = 5,
) -> list[Bar]:
    """Generate bars where bar N's close and bar N+1's open differ explicitly.

    `closes[i]` is the close of bar i. `next_opens[i]` is the open of bar i+1.
    Used to test the look-ahead-bias guard: if a signal fires on bar i's close,
    the entry price must equal `next_opens[i]`, not `closes[i]`.
    """
    if len(closes) != len(next_opens):
        raise ValueError("closes and next_opens must have equal length")
    out: list[Bar] = []
    ts = start
    prev_open = closes[0]
    for i, (close, next_open) in enumerate(zip(closes, next_opens)):
        out.append(
            Bar(
                symbol=symbol,
                timestamp=ts.astimezone(timezone.utc).isoformat(),
                open=prev_open,
                high=max(prev_open, close) + 0.5,
                low=min(prev_open, close) - 0.5,
                close=close,
                volume=1000.0,
            )
        )
        ts = ts + timedelta(minutes=interval_minutes)
        prev_open = next_open
    out.append(
        Bar(
            symbol=symbol,
            timestamp=ts.astimezone(timezone.utc).isoformat(),
            open=next_opens[-1],
            high=next_opens[-1] + 0.5,
            low=next_opens[-1] - 0.5,
            close=next_opens[-1],
            volume=1000.0,
        )
    )
    return out
