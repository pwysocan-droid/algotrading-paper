"""Signal layer — runs each enabled variant against latest bars.

For Week 1, STRATEGY_VARIANTS is empty per the curriculum. The signal
driver runs cleanly against zero variants and emits zero signals. The
strategy interface and Signal dataclass are defined here so Week 2's
strategy-roster review has a stable shape to register against.

Each strategy is a pure function: (bars, params, context) -> Signal | None.
No side effects. The driver below is what writes Signal rows to the DB.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import db
from config import STRATEGY_VARIANTS, StrategyVariant


@dataclass(frozen=True)
class BarRow:
    symbol: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    symbol: str
    variant_name: str
    strategy: str
    side: str  # 'buy' | 'sell'
    bar_timestamp: str
    price_at_signal: float
    reasoning: dict[str, Any]
    context_used: dict[str, Any] = field(default_factory=dict)


StrategyFn = Callable[[list[BarRow], dict[str, Any], dict[str, Any]], Signal | None]

STRATEGY_REGISTRY: dict[str, StrategyFn] = {
    # Strategies will be registered here in Week 2 after the roster review.
    # e.g. "bollinger": bollinger_strategy
}


def get_strategy_fn(name: str) -> StrategyFn:
    if name not in STRATEGY_REGISTRY:
        raise KeyError(
            f"strategy {name!r} not registered. Known strategies: "
            f"{sorted(STRATEGY_REGISTRY.keys())!r}"
        )
    return STRATEGY_REGISTRY[name]


def load_recent_bars(
    conn: sqlite3.Connection, symbol: str, limit: int = 200
) -> list[BarRow]:
    rows = conn.execute(
        """
        SELECT symbol, timestamp, open, high, low, close, volume
          FROM bars
         WHERE symbol = ?
         ORDER BY timestamp DESC
         LIMIT ?
        """,
        (symbol, limit),
    ).fetchall()
    bars = [
        BarRow(
            symbol=r["symbol"],
            timestamp=r["timestamp"],
            open=r["open"],
            high=r["high"],
            low=r["low"],
            close=r["close"],
            volume=r["volume"],
        )
        for r in rows
    ]
    bars.reverse()
    return bars


def _persist_signal(conn: sqlite3.Connection, sig: Signal) -> int:
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO signals (
            symbol, variant_name, strategy, side, bar_timestamp,
            price_at_signal, reasoning_json, context_used_json, emitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sig.symbol,
            sig.variant_name,
            sig.strategy,
            sig.side,
            sig.bar_timestamp,
            sig.price_at_signal,
            json.dumps(sig.reasoning, default=str),
            json.dumps(sig.context_used, default=str) if sig.context_used else None,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    return int(cur.lastrowid) if cur.lastrowid else 0


def run_variant(
    conn: sqlite3.Connection,
    variant_name: str,
    variant: StrategyVariant,
    symbols: list[str],
    context: dict[str, Any] | None = None,
) -> list[Signal]:
    """Run a single variant across all symbols, persist any emitted signals."""
    if not variant.get("enabled", False):
        return []
    strategy_name = variant["strategy"]
    fn = get_strategy_fn(strategy_name)
    params = variant.get("params", {})
    ctx = context or {}

    emitted: list[Signal] = []
    for symbol in symbols:
        bars = load_recent_bars(conn, symbol)
        if not bars:
            continue
        sig = fn(bars, params, ctx)
        if sig is None:
            continue
        sig = Signal(
            symbol=symbol,
            variant_name=variant_name,
            strategy=strategy_name,
            side=sig.side,
            bar_timestamp=sig.bar_timestamp,
            price_at_signal=sig.price_at_signal,
            reasoning=sig.reasoning,
            context_used=sig.context_used,
        )
        _persist_signal(conn, sig)
        emitted.append(sig)
    return emitted


def run_all_variants(
    symbols: list[str],
    variants: dict[str, StrategyVariant] | None = None,
    context: dict[str, Any] | None = None,
    db_path: Path | None = None,
) -> list[Signal]:
    """Iterate every enabled variant in the registry, emit signals.

    For Week 1 with an empty registry this returns []. The function still
    runs — that's what "signal layer runs cleanly against zero variants"
    means in the spec.
    """
    registry = variants if variants is not None else STRATEGY_VARIANTS
    all_signals: list[Signal] = []
    with db.connect(db_path) as conn:
        for name, variant in registry.items():
            sigs = run_variant(conn, name, variant, symbols, context=context)
            all_signals.extend(sigs)
    return all_signals
