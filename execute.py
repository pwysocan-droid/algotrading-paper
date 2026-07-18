"""Execution layer — applies position limits and routes signals to trades.

Reads pending Signal rows. For each one, runs the position-limit checks:
  - Per-trade size: $200 max
  - Total open exposure: $1,000 max
  - Concurrent open positions: 5 max
  - Per-symbol cooldown: 1h between trades on the same symbol

Every signal produces a `decisions` row — action='placed' with a trade_id,
or action='rejected' with a reason explaining which limit was breached.
The execution layer refuses orders that breach any limit; the decisions
audit trail is non-negotiable.

For Week 1 with an empty STRATEGY_VARIANTS, no signals exist, so this
module runs cleanly and produces zero trades. The position-limit logic
is fully wired so Week 2's strategy roster lands against an enforced
ceiling on day one.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import db
from config import (
    MAX_CONCURRENT_POSITIONS,
    MAX_POSITION_USD,
    MAX_TOTAL_EXPOSURE_USD,
    SLIPPAGE_PCT,
    STOP_LOSS_PCT,
    SYMBOL_COOLDOWN_HOURS,
    TAKE_PROFIT_PCT,
    TAKER_FEE_PCT,
    TIME_EXIT_HOURS,
)


@dataclass(frozen=True)
class PendingSignal:
    id: int
    symbol: str
    variant_name: str
    strategy: str
    side: str
    bar_timestamp: str
    price_at_signal: float


@dataclass(frozen=True)
class LimitCheckResult:
    ok: bool
    reason: str = ""


def open_positions(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT id, variant_name, symbol, side, qty, entry_price, entry_time
          FROM trades
         WHERE status = 'open'
        """
    ).fetchall()


def total_open_exposure_usd(conn: sqlite3.Connection) -> float:
    row = conn.execute(
        "SELECT COALESCE(SUM(qty * entry_price), 0) AS exposure FROM trades WHERE status = 'open'"
    ).fetchone()
    return float(row["exposure"]) if row else 0.0


def last_trade_for_symbol(
    conn: sqlite3.Connection, symbol: str
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT entry_time
          FROM trades
         WHERE symbol = ?
         ORDER BY entry_time DESC
         LIMIT 1
        """,
        (symbol,),
    ).fetchone()


def check_limits(
    conn: sqlite3.Connection,
    sig: PendingSignal,
    intended_position_usd: float,
    now: datetime,
) -> LimitCheckResult:
    if intended_position_usd > MAX_POSITION_USD:
        return LimitCheckResult(
            False,
            f"position size ${intended_position_usd:.2f} exceeds per-trade max "
            f"${MAX_POSITION_USD:.2f}",
        )

    open_count = len(open_positions(conn))
    if open_count >= MAX_CONCURRENT_POSITIONS:
        return LimitCheckResult(
            False,
            f"{open_count} concurrent positions already open; max is "
            f"{MAX_CONCURRENT_POSITIONS}",
        )

    current_exposure = total_open_exposure_usd(conn)
    if current_exposure + intended_position_usd > MAX_TOTAL_EXPOSURE_USD:
        return LimitCheckResult(
            False,
            f"total exposure ${current_exposure:.2f} + new ${intended_position_usd:.2f} "
            f"exceeds ${MAX_TOTAL_EXPOSURE_USD:.2f}",
        )

    last = last_trade_for_symbol(conn, sig.symbol)
    if last is not None:
        last_time = datetime.fromisoformat(last["entry_time"])
        if last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=timezone.utc)
        if now - last_time < timedelta(hours=SYMBOL_COOLDOWN_HOURS):
            return LimitCheckResult(
                False,
                f"{sig.symbol} traded within last {SYMBOL_COOLDOWN_HOURS}h "
                f"(at {last['entry_time']}); cooldown not elapsed",
            )

    return LimitCheckResult(True)


def _record_decision(
    conn: sqlite3.Connection,
    signal_id: int,
    action: str,
    reason: str,
    decided_at: str,
    trade_id: int | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO decisions (signal_id, decided_at, action, trade_id, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (signal_id, decided_at, action, trade_id, reason),
    )
    return int(cur.lastrowid) if cur.lastrowid else 0


def _record_trade(
    conn: sqlite3.Connection,
    sig: PendingSignal,
    qty: float,
    entry_price: float,
    entry_time: str,
    is_real_money: int = 0,
    alpaca_order_id: str | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO trades (
            signal_id, variant_name, symbol, side, qty, entry_price, entry_time,
            is_real_money, alpaca_order_id, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
        """,
        (
            sig.id,
            sig.variant_name,
            sig.symbol,
            sig.side,
            qty,
            entry_price,
            entry_time,
            is_real_money,
            alpaca_order_id,
        ),
    )
    return int(cur.lastrowid) if cur.lastrowid else 0


def position_qty_for_signal(
    sig: PendingSignal, position_usd: float = MAX_POSITION_USD
) -> float:
    if sig.price_at_signal <= 0:
        raise ValueError(f"non-positive price_at_signal={sig.price_at_signal!r}")
    return position_usd / sig.price_at_signal


def execute_signal(
    conn: sqlite3.Connection,
    sig: PendingSignal,
    entry_price: float,
    entry_time: datetime | None = None,
    intended_position_usd: float = MAX_POSITION_USD,
    is_real_money: int = 0,
    alpaca_order_id: str | None = None,
) -> tuple[int, str, str]:
    """Apply limits, write a decision row, optionally write a trade row.

    Returns (decision_id, action, reason). action is 'placed' or 'rejected'.
    """
    now = entry_time or datetime.now(timezone.utc)
    decided_at = now.isoformat()
    # Staleness guard (audit 2026-07-17): a signal that sat undecided
    # (outage, crash) must not fill at its old price as if fresh.
    sig_ts = datetime.fromisoformat(sig.bar_timestamp)
    if sig_ts.tzinfo is None:
        sig_ts = sig_ts.replace(tzinfo=timezone.utc)
    if now - sig_ts > timedelta(minutes=15):
        decision_id = _record_decision(
            conn, sig.id, "rejected",
            f"stale signal: bar {sig.bar_timestamp} is >15min old at execution",
            decided_at, trade_id=None,
        )
        return decision_id, "rejected", "stale signal"
    result = check_limits(conn, sig, intended_position_usd, now)
    if not result.ok:
        decision_id = _record_decision(
            conn, sig.id, "rejected", result.reason, decided_at, trade_id=None
        )
        return decision_id, "rejected", result.reason

    # Entry slippage against the trader — same model as replay._apply_slippage
    entry_price = entry_price * (
        (1.0 + SLIPPAGE_PCT) if sig.side == "buy" else (1.0 - SLIPPAGE_PCT)
    )
    qty = intended_position_usd / entry_price
    trade_id = _record_trade(
        conn,
        sig,
        qty=qty,
        entry_price=entry_price,
        entry_time=decided_at,
        is_real_money=is_real_money,
        alpaca_order_id=alpaca_order_id,
    )
    reason = f"placed {sig.side} {qty:.6f} {sig.symbol} @ {entry_price:.2f}"
    decision_id = _record_decision(
        conn, sig.id, "placed", reason, decided_at, trade_id=trade_id
    )
    return decision_id, "placed", reason


def pending_signals(conn: sqlite3.Connection) -> list[PendingSignal]:
    """Signals with no associated decision row yet."""
    rows = conn.execute(
        """
        SELECT s.id, s.symbol, s.variant_name, s.strategy, s.side,
               s.bar_timestamp, s.price_at_signal
          FROM signals s
          LEFT JOIN decisions d ON d.signal_id = s.id
         WHERE d.id IS NULL
         ORDER BY s.id ASC
        """
    ).fetchall()
    return [
        PendingSignal(
            id=r["id"],
            symbol=r["symbol"],
            variant_name=r["variant_name"],
            strategy=r["strategy"],
            side=r["side"],
            bar_timestamp=r["bar_timestamp"],
            price_at_signal=r["price_at_signal"],
        )
        for r in rows
    ]


def process_pending(db_path: Path | None = None, now: datetime | None = None) -> int:
    """Process every pending signal in the DB. Returns count of placed trades.

    For Week 1 with no strategies registered there are no pending signals,
    so this returns 0 cleanly.
    """
    from config import STRATEGY_VARIANTS

    placed = 0
    with db.connect(db_path) as conn:
        for sig in pending_signals(conn):
            # Shadow-arm guard: disabled variants emit signals for
            # forward-test evidence only. Recording the rejection as a
            # decision keeps the signal out of the pending set forever;
            # the trade must NEVER be placed. This check is the single
            # wall between shadow research and real (paper) orders.
            variant = STRATEGY_VARIANTS.get(sig.variant_name)
            if not (variant and variant.get("enabled", False)):
                _record_decision(
                    conn, sig.id, "rejected",
                    "shadow arm — variant disabled, research signal only",
                    (now or datetime.now(timezone.utc)).isoformat(),
                    trade_id=None,
                )
                continue
            _, action, _ = execute_signal(
                conn, sig, entry_price=sig.price_at_signal, entry_time=now
            )
            if action == "placed":
                placed += 1
    return placed


def _close_trade(
    conn: sqlite3.Connection,
    trade: sqlite3.Row,
    exit_price: float,
    exit_time: str,
    exit_reason: str,
) -> None:
    """Close with the SAME cost model as replay (sim-to-live parity,
    decision-log 2026-07-17 calibration finding): exit slippage against
    the trader, taker fees on both legs subtracted from pnl_usd;
    pnl_pct stays gross-of-fees, mirroring replay's convention."""
    if trade["side"] == "buy":
        exit_price = exit_price * (1.0 - SLIPPAGE_PCT)
        gross = (exit_price - trade["entry_price"]) * trade["qty"]
        pnl_pct = (exit_price / trade["entry_price"] - 1.0) * 100.0
    else:
        exit_price = exit_price * (1.0 + SLIPPAGE_PCT)
        gross = (trade["entry_price"] - exit_price) * trade["qty"]
        pnl_pct = (1.0 - exit_price / trade["entry_price"]) * 100.0
    fees = (trade["entry_price"] + exit_price) * trade["qty"] * TAKER_FEE_PCT
    pnl_usd = gross - fees
    conn.execute(
        """
        UPDATE trades
           SET exit_price = ?, exit_time = ?, exit_reason = ?,
               pnl_usd = ?, pnl_pct = ?, status = 'closed'
         WHERE id = ?
        """,
        (exit_price, exit_time, exit_reason, pnl_usd, pnl_pct, trade["id"]),
    )


def manage_exits(
    db_path: Path | None = None,
    now: datetime | None = None,
    take_profit_pct: float = TAKE_PROFIT_PCT,
    stop_loss_pct: float = STOP_LOSS_PCT,
    time_exit_hours: int = TIME_EXIT_HOURS,
) -> int:
    """Layer 4 exits for open live-paper trades. Returns count closed.

    Without this, open positions never free their slots and the
    5-concurrent-position cap deadlocks the whole loop after 5 trades.
    Checks each open trade against its symbol's latest bar: stop/target
    from the bar's low/high (conservative — if both cross in one bar,
    assume the stop hit first, matching replay.simulate_exit), then the
    time exit at the bar's close.
    """
    ts = now or datetime.now(timezone.utc)
    closed = 0
    from config import STRATEGY_VARIANTS  # per-variant exit overrides

    with db.connect(db_path) as conn:
        for trade in open_positions(conn):
            vparams = (STRATEGY_VARIANTS.get(trade["variant_name"]) or {}).get("params", {})
            v_tp = float(vparams.get("tp", take_profit_pct))
            v_sl = float(vparams.get("sl", stop_loss_pct))
            v_hours = int(vparams.get("time_exit_hours", time_exit_hours))
            # Only bars that BEGIN at/after entry may close a trade — the
            # signal bar's range predates the fill and once closed trades
            # same-cycle on pre-entry price action (audit 2026-07-17).
            bar = conn.execute(
                """
                SELECT timestamp, high, low, close FROM bars
                 WHERE symbol = (SELECT symbol FROM trades WHERE id = ?)
                   AND timestamp >= (SELECT entry_time FROM trades WHERE id = ?)
                 ORDER BY timestamp DESC LIMIT 1
                """,
                (trade["id"], trade["id"]),
            ).fetchone()
            if bar is None:
                continue

            entry_price = trade["entry_price"]
            if trade["side"] == "buy":
                tp = entry_price * (1.0 + v_tp)
                sl = entry_price * (1.0 - v_sl)
                sl_hit = bar["low"] <= sl
                tp_hit = bar["high"] >= tp
            else:
                tp = entry_price * (1.0 - v_tp)
                sl = entry_price * (1.0 + v_sl)
                sl_hit = bar["high"] >= sl
                tp_hit = bar["low"] <= tp

            entry_time = datetime.fromisoformat(trade["entry_time"])
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)

            if sl_hit:  # conservative: stop wins ties
                _close_trade(conn, trade, sl, ts.isoformat(), "stop_loss")
            elif tp_hit:
                _close_trade(conn, trade, tp, ts.isoformat(), "take_profit")
            elif ts - entry_time >= timedelta(hours=v_hours):
                _close_trade(conn, trade, bar["close"], ts.isoformat(), "time_exit")
            else:
                continue
            closed += 1
    return closed
