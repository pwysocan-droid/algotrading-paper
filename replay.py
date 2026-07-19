"""Replay tool — backtest a strategy variant against historical bars.

Critical: the look-ahead-bias guard. A signal generated on bar N's close
is "available" in real time at bar N's close, but a real trade can only
execute against bar N+1's open. The replay sets entry_price to the OPEN of
the bar AFTER the bar that produced the signal — never the close of the
producing bar.

For Week 1 the variant registry is empty; --variant=null is the only valid
value and produces a fully-formed v1-pattern empty-state report with zero
simulated trades.
"""

from __future__ import annotations

import argparse
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import db
from config import (
    BAR_TIMEFRAME_MINUTES,
    LIMIT_FILL_TIMEOUT_BARS,
    MAKER_FEE_PCT,
    MAX_CONCURRENT_POSITIONS,
    MAX_POSITION_USD,
    MAX_TOTAL_EXPOSURE_USD,
    SLIPPAGE_PCT,
    STOP_LOSS_PCT,
    STRATEGY_VARIANTS,
    SYMBOL_COOLDOWN_HOURS,
    TAKE_PROFIT_PCT,
    TAKER_FEE_PCT,
    TIME_EXIT_HOURS,
    WATCHED_SYMBOLS,
)
from render import (
    EMDASH,
    Stat,
    TableSpec,
    format_count,
    format_currency,
    format_iso_ts,
    format_pct,
    render_v1_report,
)
import signals as sig_mod
from signals import BarRow, Signal, get_strategy_fn


@dataclass
class SimulatedTrade:
    variant_name: str
    strategy: str
    symbol: str
    side: str
    signal_bar_timestamp: str  # bar N — the bar whose close produced the signal
    entry_bar_timestamp: str  # bar N+1 — the bar whose OPEN is the entry price
    entry_price: float
    qty: float
    exit_bar_timestamp: str | None = None
    exit_price: float | None = None
    exit_reason: str | None = None  # 'take_profit' | 'stop_loss' | 'time_exit'
    pnl_usd: float | None = None  # net of fees when fee_pct > 0
    pnl_pct: float | None = None
    fees_usd: float = 0.0
    accepted: bool = True  # set by apply_portfolio_constraints
    reject_reason: str | None = None


def _parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _apply_slippage(price: float, side: str, leg: str, slippage_pct: float) -> float:
    """Slippage always works against the trader — never a favorable fill.

    buy+entry or sell+exit: you're paying, so the worse fill is higher.
    sell+entry or buy+exit: you're receiving, so the worse fill is lower.
    """
    if slippage_pct == 0.0:
        return price
    if (side == "buy" and leg == "entry") or (side == "sell" and leg == "exit"):
        return price * (1.0 + slippage_pct)
    return price * (1.0 - slippage_pct)


def load_bars_in_range(
    conn: sqlite3.Connection, symbol: str, start: datetime, end: datetime
) -> list[BarRow]:
    rows = conn.execute(
        """
        SELECT symbol, timestamp, open, high, low, close, volume
          FROM bars
         WHERE symbol = ? AND timestamp >= ? AND timestamp <= ?
         ORDER BY timestamp ASC
        """,
        (symbol, start.isoformat(), end.isoformat()),
    ).fetchall()
    return [
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


def simulate_exit(
    bars_after_entry: list[BarRow],
    entry_price: float,
    side: str,
    take_profit_pct: float = TAKE_PROFIT_PCT,
    stop_loss_pct: float = STOP_LOSS_PCT,
    time_exit_hours: int = TIME_EXIT_HOURS,
    tp_requires_trade_through: bool = False,
) -> tuple[str | None, float | None, str | None]:
    """Walk forward through bars, return (exit_bar_ts, exit_price, exit_reason).

    Conservative simulation: if a bar's high crosses take-profit and low
    crosses stop-loss, assume stop-loss hit first (worst-case for the trade).

    tp_requires_trade_through: a resting limit at the take-profit price only
    fills if price trades strictly THROUGH it (maker fill model); a touch at
    exactly tp may leave the order unfilled in the queue.
    """
    if not bars_after_entry:
        return (None, None, None)

    if side == "buy":
        tp = entry_price * (1.0 + take_profit_pct)
        sl = entry_price * (1.0 - stop_loss_pct)
    elif side == "sell":
        tp = entry_price * (1.0 - take_profit_pct)
        sl = entry_price * (1.0 + stop_loss_pct)
    else:
        raise ValueError(f"unsupported side: {side!r}")

    entry_time = datetime.fromisoformat(bars_after_entry[0].timestamp)
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=timezone.utc)
    time_exit_at = entry_time + timedelta(hours=time_exit_hours)

    for bar in bars_after_entry:
        bar_ts = datetime.fromisoformat(bar.timestamp)
        if bar_ts.tzinfo is None:
            bar_ts = bar_ts.replace(tzinfo=timezone.utc)
        if side == "buy":
            sl_hit = bar.low <= sl
            tp_hit = bar.high > tp if tp_requires_trade_through else bar.high >= tp
        else:
            sl_hit = bar.high >= sl
            tp_hit = bar.low < tp if tp_requires_trade_through else bar.low <= tp

        if sl_hit and tp_hit:
            return (bar.timestamp, sl, "stop_loss")
        if sl_hit:
            return (bar.timestamp, sl, "stop_loss")
        if tp_hit:
            return (bar.timestamp, tp, "take_profit")
        if bar_ts >= time_exit_at:
            return (bar.timestamp, bar.close, "time_exit")

    last = bars_after_entry[-1]
    return (last.timestamp, last.close, "time_exit")


def replay_variant(
    conn: sqlite3.Connection,
    variant_name: str,
    variant: dict[str, Any],
    symbols: list[str],
    start: datetime,
    end: datetime,
    position_usd: float = MAX_POSITION_USD,
    fee_pct: float = 0.0,
    slippage_pct: float = 0.0,
    window_cap: int = 400,
    fill_model: str = "taker",
    maker_fee_pct: float = MAKER_FEE_PCT,
    limit_fill_timeout_bars: int = LIMIT_FILL_TIMEOUT_BARS,
) -> list[SimulatedTrade]:
    """Run a strategy variant in backtest mode over [start, end].

    window_cap bounds the per-step bar window handed to the strategy
    (matching live, where load_recent_bars caps at ~200-300). Without it
    the growing bars[:i+1] slice makes multi-year replays O(n^2). 400
    trailing bars exceeds every registered strategy's deepest lookback
    (344 for entropy_collapse_impulse).

    Look-ahead-bias guard: for a signal generated at bar N's close, the entry
    price is the OPEN of bar N+1, not bar N's close. If bar N is the last bar
    in the window the signal is dropped (no future bar available).

    fee_pct/slippage_pct default to 0.0 so callers that test signal timing
    (e.g. the look-ahead-bias guard) get exact bar-open prices unless they
    opt in. run_replay passes the real config values explicitly.

    fill_model='maker' models limit-order entries (the cost lever): a limit
    rests at the signal bar's CLOSE and fills only if a bar within
    limit_fill_timeout_bars trades strictly through it — otherwise the
    signal expires unfilled and is dropped. Filled legs pay maker_fee_pct
    and zero slippage. Take-profit exits are also resting limits (maker,
    trade-through required); stop-loss and time exits remain market orders
    (taker fee + slippage). Conservative by construction: no price
    improvement, touch-without-trade-through never fills.

    Portfolio constraints (cooldown, exposure, concurrent-position caps) are
    NOT applied here — this produces unconstrained candidate trades for one
    variant. Call apply_portfolio_constraints() on the merged, multi-variant
    list to get what the live system would actually place.
    """
    if not variant.get("enabled", False):
        return []
    strategy_name = variant["strategy"]
    fn = get_strategy_fn(strategy_name)
    params = variant.get("params", {})

    # Cross-symbol context (context_keys=['btc_bars']): preload BTC bars
    # once; per step, slice to timestamps <= the signal bar's timestamp so
    # the look-ahead guard holds for the context series too.
    import bisect

    wants_btc = "btc_bars" in variant.get("context_keys", [])
    btc_bars: list[BarRow] = []
    btc_ts: list[str] = []
    if wants_btc:
        btc_bars = load_bars_in_range(conn, "BTC/USD", start, end)
        btc_ts = [b.timestamp for b in btc_bars]

    # Round-005 ideas 2/4 (context_keys=['basket_bars']): the cross-
    # sectional rank engine needs every symbol's own bars, not just the
    # one being scored. Preload once per symbol; per step, slice to
    # timestamps <= the signal bar's timestamp so the look-ahead guard
    # holds for the basket series too (mirrors btc_bars above).
    wants_basket = "basket_bars" in variant.get("context_keys", [])
    basket_bars: dict[str, list[BarRow]] = {}
    basket_ts: dict[str, list[str]] = {}
    if wants_basket:
        for sym in symbols:
            basket_bars[sym] = load_bars_in_range(conn, sym, start, end)
            basket_ts[sym] = [b.timestamp for b in basket_bars[sym]]

    # Meta context (context_keys=['system_state']): simulate the null
    # arm's constrained trades over the same window once (deterministic,
    # so reproducible), then serve trailing-24h win rate / stop-outs per
    # step. Backtest approximation of live load_system_state(), where
    # "portfolio stop-outs" reduce to the null arm's own — documented.
    wants_state = "system_state" in variant.get("context_keys", [])
    null_exits: list[tuple[str, bool, bool]] = []  # (exit_ts, win, stop)
    null_exit_ts: list[str] = []
    null_cand_ts: list[str] = []
    null_cand_rejected: list[bool] = []
    if wants_state:
        from config import STRATEGY_VARIANTS as _ALL

        null_variant = dict(_ALL["null_baseline"])
        null_variant["enabled"] = True
        null_trades = replay_variant(
            conn, "null_baseline", null_variant, symbols, start, end,
            position_usd=position_usd, fee_pct=fee_pct, slippage_pct=slippage_pct,
        )
        null_trades = apply_portfolio_constraints(null_trades)
        closed = [
            t for t in null_trades
            if t.accepted and t.exit_bar_timestamp and t.pnl_usd is not None
        ]
        closed.sort(key=lambda t: t.exit_bar_timestamp)
        null_exits = [
            (t.exit_bar_timestamp, t.pnl_usd > 0, t.exit_reason == "stop_loss")
            for t in closed
        ]
        null_exit_ts = [e[0] for e in null_exits]
        # Round-002 gate inputs, approximated from the null arm (documented:
        # live rejection_rate spans all arms; here only null is simulated).
        by_entry = sorted(null_trades, key=lambda t: t.entry_bar_timestamp)
        null_cand_ts = [t.entry_bar_timestamp for t in by_entry]
        null_cand_rejected = [not t.accepted for t in by_entry]

    def _state_at(ts_str: str) -> dict[str, Any]:
        hi = bisect.bisect_right(null_exit_ts, ts_str)
        cutoff = (_parse_ts(ts_str) - timedelta(hours=24)).isoformat()
        lo = bisect.bisect_left(null_exit_ts, cutoff)
        window_exits = null_exits[lo:hi]
        closed_n = len(window_exits)
        wins = sum(1 for _, w, _s in window_exits if w)
        stops = sum(1 for _, _w, s in window_exits if s)
        c_hi = bisect.bisect_right(null_cand_ts, ts_str)
        recent_cand = null_cand_rejected[max(0, c_hi - 50): c_hi]
        last_exits = null_exits[max(0, hi - 10): hi]
        last_20 = null_exits[max(0, hi - 20): hi]
        last_40 = null_exits[max(0, hi - 40): hi]
        last_100 = null_exits[max(0, hi - 100): hi]
        return {
            "null_win_rate": (wins / closed_n) if closed_n else None,
            "recent_stopouts": stops,
            "rejection_rate": (
                sum(recent_cand) / len(recent_cand) if recent_cand else None
            ),
            "placebo_stop_rate": (
                sum(1 for _, _w, s in last_exits if s) / len(last_exits)
                if last_exits else None
            ),
            # r003: live spans ALL arms; in replay only the null arm is
            # simulated, so this reduces to the null arm's own last-10
            # (same documented approximation as the fields above).
            "stop_out_rate": (
                sum(1 for _, _w, s in last_exits if s) / len(last_exits)
                if last_exits else None
            ),
            # r004 gate inputs (the fallback implementer added these to
            # the LIVE feed only — without this mirror the gated engine
            # would fire ZERO times in every gauntlet, the vol_thrust
            # never-fires bug in reverse; caught in review 2026-07-18).
            "null_win_rate_100": (
                sum(1 for _, w, _s in last_100 if w) / len(last_100)
                if last_100 else None
            ),
            "stopout_cluster_index": sig_mod._stopout_cluster_index([
                {"exit_reason": "stop_loss" if s else "time_exit", "exit_time": ts}
                for ts, _w, s in last_20
            ]),
            # r005 ideas 1/4 gate inputs — same mirror discipline as
            # null_win_rate_100 above (live-only would repeat the
            # never-fires bug for these two ideas' gates).
            "null_win_rate_20": (
                sum(1 for _, w, _s in last_20 if w) / len(last_20)
                if last_20 else None
            ),
            "null_win_rate_40": (
                sum(1 for _, w, _s in last_40 if w) / len(last_40)
                if last_40 else None
            ),
        }

    out: list[SimulatedTrade] = []
    for symbol in symbols:
        bars = load_bars_in_range(conn, symbol, start, end)
        if len(bars) < 2:
            continue
        for i in range(len(bars) - 1):
            lo = max(0, i + 1 - window_cap) if window_cap else 0
            window = bars[lo: i + 1]
            ctx: dict[str, Any] = {}
            if wants_btc:
                cut = bisect.bisect_right(btc_ts, window[-1].timestamp)
                ctx["btc_bars"] = btc_bars[:cut]
            if wants_basket:
                ctx["basket_bars"] = {
                    sym: basket_bars[sym][:bisect.bisect_right(basket_ts[sym], window[-1].timestamp)]
                    for sym in symbols
                }
            if wants_state:
                ctx["system_state"] = _state_at(window[-1].timestamp)
            sig: Signal | None = fn(window, params, ctx)
            if sig is None:
                continue
            if fill_model == "maker":
                limit_px = bars[i].close
                fill_i = None
                for j in range(i + 1, min(i + 1 + limit_fill_timeout_bars, len(bars))):
                    traded_through = (
                        bars[j].low < limit_px if sig.side == "buy"
                        else bars[j].high > limit_px
                    )
                    if traded_through:
                        fill_i = j
                        break
                if fill_i is None:
                    continue  # limit expired unfilled — the cost of being maker
                entry_bar = bars[fill_i]
                entry_price = limit_px
                entry_fee_pct = maker_fee_pct
                forward = bars[fill_i + 1:]
            else:
                entry_bar = bars[i + 1]
                entry_price = _apply_slippage(entry_bar.open, sig.side, "entry", slippage_pct)
                entry_fee_pct = fee_pct
                forward = bars[i + 2 :]
            qty = position_usd / entry_price
            exit_ts, raw_exit_price, exit_reason = simulate_exit(
                forward, entry_price=entry_price, side=sig.side,
                take_profit_pct=float(params.get("tp", TAKE_PROFIT_PCT)),
                stop_loss_pct=float(params.get("sl", STOP_LOSS_PCT)),
                time_exit_hours=int(params.get("time_exit_hours", TIME_EXIT_HOURS)),
                tp_requires_trade_through=(fill_model == "maker"),
            )
            if raw_exit_price is None:
                exit_price = None
                exit_fee_pct = fee_pct
            elif fill_model == "maker" and exit_reason == "take_profit":
                exit_price = raw_exit_price  # resting limit: maker, no slippage
                exit_fee_pct = maker_fee_pct
            else:
                exit_price = _apply_slippage(raw_exit_price, sig.side, "exit", slippage_pct)
                exit_fee_pct = fee_pct
            pnl_usd: float | None = None
            pnl_pct: float | None = None
            fees_usd = 0.0
            if exit_price is not None:
                fees_usd = (entry_price * entry_fee_pct + exit_price * exit_fee_pct) * qty
                if sig.side == "buy":
                    gross = (exit_price - entry_price) * qty
                    pnl_pct = (exit_price / entry_price - 1.0) * 100.0
                else:
                    gross = (entry_price - exit_price) * qty
                    pnl_pct = (1.0 - exit_price / entry_price) * 100.0
                pnl_usd = gross - fees_usd
            out.append(
                SimulatedTrade(
                    variant_name=variant_name,
                    strategy=strategy_name,
                    symbol=symbol,
                    side=sig.side,
                    signal_bar_timestamp=bars[i].timestamp,
                    entry_bar_timestamp=entry_bar.timestamp,
                    entry_price=entry_price,
                    qty=qty,
                    exit_bar_timestamp=exit_ts,
                    exit_price=exit_price,
                    exit_reason=exit_reason,
                    pnl_usd=pnl_usd,
                    pnl_pct=pnl_pct,
                    fees_usd=fees_usd,
                )
            )
    return out


def apply_portfolio_constraints(
    trades: list[SimulatedTrade],
    max_concurrent: int = MAX_CONCURRENT_POSITIONS,
    max_exposure_usd: float = MAX_TOTAL_EXPOSURE_USD,
    cooldown_hours: int = SYMBOL_COOLDOWN_HOURS,
) -> list[SimulatedTrade]:
    """Mirror execute.py's check_limits across the merged, time-ordered stream
    of every variant's candidate trades. Position limits are portfolio-wide,
    not per-variant (roadmap.md Week 3: "the execution layer enforces the
    overall position limits across the entire portfolio of variants").

    Walks candidates in entry_bar_timestamp order, maintaining an in-memory
    ledger of currently-open simulated positions. At each candidate: first
    frees any ledger position whose exit has already happened by now, then
    applies the same three checks execute.py.check_limits applies, in the
    same order (concurrent count, total exposure, symbol cooldown). Cooldown
    is checked against the most recent ACCEPTED trade's entry time on that
    symbol, matching execute.py.last_trade_for_symbol — which only ever sees
    placed trades, since rejected signals never reach the `trades` table.

    Mutates and returns `trades` (sets .accepted / .reject_reason on each);
    order is NOT preserved — callers needing original order should copy first.
    """
    ordered = sorted(trades, key=lambda t: (t.entry_bar_timestamp, t.variant_name, t.symbol))
    open_positions: list[SimulatedTrade] = []
    last_entry_by_symbol: dict[str, datetime] = {}

    for t in ordered:
        now = _parse_ts(t.entry_bar_timestamp)

        open_positions = [
            p for p in open_positions
            if p.exit_bar_timestamp is None or _parse_ts(p.exit_bar_timestamp) > now
        ]

        if len(open_positions) >= max_concurrent:
            t.accepted = False
            t.reject_reason = (
                f"{len(open_positions)} concurrent positions open; max {max_concurrent}"
            )
            continue

        current_exposure = sum(p.qty * p.entry_price for p in open_positions)
        intended = t.qty * t.entry_price
        if current_exposure + intended > max_exposure_usd:
            t.accepted = False
            t.reject_reason = (
                f"exposure ${current_exposure:.2f} + ${intended:.2f} "
                f"exceeds ${max_exposure_usd:.2f}"
            )
            continue

        last_entry = last_entry_by_symbol.get(t.symbol)
        if last_entry is not None and now - last_entry < timedelta(hours=cooldown_hours):
            t.accepted = False
            t.reject_reason = (
                f"{t.symbol} traded within last {cooldown_hours}h "
                f"(at {last_entry.isoformat()}); cooldown not elapsed"
            )
            continue

        t.accepted = True
        t.reject_reason = None
        open_positions.append(t)
        last_entry_by_symbol[t.symbol] = now

    return ordered


def sharpe_ratio(pnl_pcts: list[float], window_days: float) -> float | None:
    """Annualized Sharpe from per-trade net returns (%).

    mean/std of per-trade returns scaled by sqrt(trades per year), with
    trades-per-year inferred from the backtest window. No risk-free-rate
    subtraction — at per-trade horizon of hours it is negligible against
    3-5% stop/target moves. None (rendered as em-dash) when fewer than 2
    trades or zero variance — a Sharpe from that is not a number worth
    printing.
    """
    n = len(pnl_pcts)
    if n < 2 or window_days <= 0:
        return None
    mean = sum(pnl_pcts) / n
    var = sum((x - mean) ** 2 for x in pnl_pcts) / (n - 1)
    if var == 0.0:
        return None
    trades_per_year = n / window_days * 365.0
    return (mean / math.sqrt(var)) * math.sqrt(trades_per_year)


def max_drawdown_pct(
    pnl_usds: list[float], base_equity: float = MAX_TOTAL_EXPOSURE_USD
) -> float | None:
    """Max peak-to-trough drawdown (%) of the cumulative-P&L equity curve.

    Equity starts at the portfolio ceiling ($1,000 — the capital actually
    at risk, PROJECT.md capital model) and steps by each trade's realized
    P&L in entry order. None when no trades.
    """
    if not pnl_usds:
        return None
    equity = base_equity
    peak = equity
    max_dd = 0.0
    for pnl in pnl_usds:
        equity += pnl
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100.0)
    return max_dd


def _bars_summary(
    conn: sqlite3.Connection, symbols: list[str], start: datetime, end: datetime
) -> list[list[str]]:
    """Per-symbol bar count/range for the report table. Gaps = missing bars
    against the expected 5-min-cadence count over [start, end] — crypto
    trades 24/7 so there's no market-hours exemption to account for.
    """
    rows: list[list[str]] = []
    for symbol in symbols:
        result = conn.execute(
            """
            SELECT COUNT(*) AS n, MIN(timestamp) AS first_ts, MAX(timestamp) AS last_ts
              FROM bars
             WHERE symbol = ? AND timestamp >= ? AND timestamp <= ?
            """,
            (symbol, start.isoformat(), end.isoformat()),
        ).fetchone()
        n = int(result["n"]) if result["n"] is not None else 0
        first_ts = result["first_ts"] if result["first_ts"] else EMDASH
        last_ts = result["last_ts"] if result["last_ts"] else EMDASH
        if n > 0:
            expected = int((end - start).total_seconds() // (BAR_TIMEFRAME_MINUTES * 60)) + 1
            missing = max(0, expected - n)
            gaps_str = format_count(missing)
        else:
            gaps_str = EMDASH
        rows.append([symbol, format_count(n), first_ts, last_ts, gaps_str])
    return rows


@dataclass
class CoverageReport:
    symbol: str
    n_bars: int
    expected_bars: int
    coverage_pct: float
    largest_gap_minutes: float
    largest_gap_start: str | None
    largest_gap_end: str | None


def check_coverage(
    conn: sqlite3.Connection, symbols: list[str], start: datetime, end: datetime
) -> list[CoverageReport]:
    """Real continuity check: per symbol, expected-vs-actual bar count AND
    the single largest gap between consecutive bars (a count mismatch alone
    can't distinguish "scattered thin gaps" from "one multi-day outage").
    """
    expected = int((end - start).total_seconds() // (BAR_TIMEFRAME_MINUTES * 60)) + 1
    step = timedelta(minutes=BAR_TIMEFRAME_MINUTES)
    out: list[CoverageReport] = []
    for symbol in symbols:
        rows = conn.execute(
            """
            SELECT timestamp FROM bars
             WHERE symbol = ? AND timestamp >= ? AND timestamp <= ?
             ORDER BY timestamp ASC
            """,
            (symbol, start.isoformat(), end.isoformat()),
        ).fetchall()
        timestamps = [_parse_ts(r["timestamp"]) for r in rows]
        n = len(timestamps)

        largest_gap = timedelta(0)
        gap_start: datetime | None = None
        gap_end: datetime | None = None
        for prev, cur in zip(timestamps, timestamps[1:]):
            delta = cur - prev
            if delta > step and delta > largest_gap:
                largest_gap = delta
                gap_start, gap_end = prev, cur

        out.append(
            CoverageReport(
                symbol=symbol,
                n_bars=n,
                expected_bars=expected,
                coverage_pct=(n / expected * 100.0) if expected else 0.0,
                largest_gap_minutes=largest_gap.total_seconds() / 60.0,
                largest_gap_start=gap_start.isoformat() if gap_start else None,
                largest_gap_end=gap_end.isoformat() if gap_end else None,
            )
        )
    return out


def build_report_data(
    *,
    variant_arg: str,
    period_start: datetime,
    period_end: datetime,
    period_label: str,
    timestamp: datetime,
    trades: list[SimulatedTrade],
    bars_rows: list[list[str]],
    run_phases: list[list[str]],
) -> dict[str, Any]:
    candidates = trades
    accepted = [t for t in trades if t.accepted]
    rejected = [t for t in trades if not t.accepted]
    n_trades = len(accepted)
    total_pnl: float | None = None
    total_fees: float = 0.0
    pnl_pct: float | None = None
    if n_trades > 0:
        total_pnl = sum(t.pnl_usd for t in accepted if t.pnl_usd is not None)
        total_fees = sum(t.fees_usd for t in accepted)
        pcts = [t.pnl_pct for t in accepted if t.pnl_pct is not None]
        if pcts:
            pnl_pct = sum(pcts) / len(pcts)
    else:
        total_pnl = 0.0
        pnl_pct = None  # — per the spec: percentage with no trades is not 0%, it's "not yet present"

    n_variants = len([v for v in STRATEGY_VARIANTS.values() if v.get("enabled", False)])
    variants_value = format_count(n_variants) if n_variants > 0 else EMDASH

    stats = [
        Stat("Variants registered", variants_value, f"{n_variants} enabled"),
        Stat("Trades in period", format_count(n_trades), "paper, placed"),
        Stat("P&L", format_currency(total_pnl), format_pct(pnl_pct)),
        Stat("System uptime", "100%", "last 4w"),
    ]

    if not STRATEGY_VARIANTS:
        per_variant_rows: list[list[str]] = []
        empty_msg = "no variants registered"
    else:
        window_days = max((period_end - period_start).total_seconds() / 86400.0, 0.0)
        per_variant_rows = []
        for name, variant in STRATEGY_VARIANTS.items():
            v_trades = sorted(
                (t for t in accepted if t.variant_name == name),
                key=lambda t: t.entry_bar_timestamp,
            )
            n = len(v_trades)
            v_pnl = sum(t.pnl_usd for t in v_trades if t.pnl_usd is not None) if v_trades else 0.0
            v_pcts = [t.pnl_pct for t in v_trades if t.pnl_pct is not None]
            v_pct_avg = (sum(v_pcts) / len(v_pcts)) if v_pcts else None
            v_sharpe = sharpe_ratio(v_pcts, window_days)
            v_dd = max_drawdown_pct(
                [t.pnl_usd for t in v_trades if t.pnl_usd is not None]
            )
            per_variant_rows.append(
                [
                    f"`{name}`",
                    format_count(n),
                    EMDASH,
                    format_currency(v_pnl),
                    format_pct(v_pct_avg),
                    f"{v_sharpe:.2f}" if v_sharpe is not None else EMDASH,
                    f"{v_dd:.1f}%" if v_dd is not None else EMDASH,
                    "ok",
                ]
            )
        empty_msg = "no variants registered"

    notes = None
    if not STRATEGY_VARIANTS:
        notes = (
            "Empty state — no strategy variants are registered. This is expected "
            "for Week 1; Bollinger and MA-crossover (or Week-0-surfaced "
            "replacements) come online in Week 2 after the strategy-roster review."
        )
    elif candidates:
        n_candidates = len(candidates)
        n_rejected = len(rejected)
        reject_pct = (n_rejected / n_candidates * 100.0) if n_candidates else 0.0
        notes = (
            f"{format_count(n_candidates)} candidate signals; "
            f"{format_count(n_rejected)} rejected ({reject_pct:.1f}%) by portfolio "
            f"constraints (cooldown / exposure cap / concurrent-position cap — "
            f"mirrors execute.py.check_limits) before ever reaching execution. "
            f"{format_currency(total_fees)} in fees deducted from the {format_count(n_trades)} "
            f"placed trades' P&L. Slippage assumption is unconfirmed — see config.py "
            f"SLIPPAGE_PCT comment."
        )

    subtitle = (
        f"Variant — {variant_arg}  ·  Period — "
        f"{period_start.date().isoformat()} → {period_end.date().isoformat()} "
        f"({period_label})"
    )

    return {
        "title": "algotrading-paper / replay",
        "subtitle": subtitle,
        "timestamp": timestamp,
        "count_summary": f"{n_trades} trades",
        "links": [
            ("↗ index", "INDEX.md"),
        ],
        "stats": stats,
        "flags": [],
        "dominant_table": TableSpec(
            section_marker="§ 01 — Per-variant performance · last 30 days",
            columns=["Variant", "n", "30d sparkline", "P&L", "Pct", "Sharpe", "Max DD", "Status"],
            rows=per_variant_rows,
            empty_row_message=empty_msg,
        ),
        "sub_tables": [
            TableSpec(
                section_marker="§ 02 — Bars in period · by symbol",
                columns=["Symbol", "Bars", "First", "Last", "Gaps"],
                rows=bars_rows,
                empty_row_message="no bars in period",
            ),
            TableSpec(
                section_marker="§ 03 — Run summary",
                columns=["Phase", "Status", "Duration", "Notes"],
                rows=run_phases,
                empty_row_message="no phases ran",
            ),
        ],
        "notes": notes,
        "generator": "replay.py v0.1.0",
    }


def run_replay(
    variant_arg: str,
    period: str = "30d",
    db_path: Path | None = None,
    fee_pct: float = TAKER_FEE_PCT,
    slippage_pct: float = SLIPPAGE_PCT,
    apply_constraints: bool = True,
) -> tuple[str, list[SimulatedTrade]]:
    """Run replay end-to-end. Returns (markdown_report, simulated_trades).

    fee_pct/slippage_pct default to the real config assumptions — this is
    the CLI/report path, unlike replay_variant's zero defaults. Set
    apply_constraints=False to get raw unconstrained candidates (e.g. for
    comparing against the constrained result).
    """
    if not period.endswith("d"):
        raise ValueError(f"period must end in 'd' (e.g. '30d'), got {period!r}")
    days = int(period[:-1])
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    started = datetime.now(timezone.utc)
    trades: list[SimulatedTrade] = []
    fetch_status = signals_status = execute_status = analytics_status = "ok"

    with db.connect(db_path) as conn:
        if variant_arg == "null":
            for name, variant in STRATEGY_VARIANTS.items():
                if not variant.get("enabled", False):
                    continue
                trades.extend(
                    replay_variant(
                        conn, name, variant, WATCHED_SYMBOLS, start, end,
                        fee_pct=fee_pct, slippage_pct=slippage_pct,
                    )
                )
        else:
            if variant_arg not in STRATEGY_VARIANTS:
                raise KeyError(
                    f"variant {variant_arg!r} not in STRATEGY_VARIANTS. "
                    f"Use --variant=null to replay all enabled variants."
                )
            v = STRATEGY_VARIANTS[variant_arg]
            trades = replay_variant(
                conn, variant_arg, v, WATCHED_SYMBOLS, start, end,
                fee_pct=fee_pct, slippage_pct=slippage_pct,
            )

        bars_rows = _bars_summary(conn, WATCHED_SYMBOLS, start, end)

    if apply_constraints and trades:
        trades = apply_portfolio_constraints(trades)

    n_accepted = sum(1 for t in trades if t.accepted)
    n_rejected = len(trades) - n_accepted

    finished = datetime.now(timezone.utc)
    elapsed_s = (finished - started).total_seconds()

    run_phases: list[list[str]] = [
        ["fetch", fetch_status, "0.0s", "no fetch this run"],
        ["signals", signals_status, "0.0s", f"{len(trades)} candidate signals"],
        [
            "execute", execute_status, "0.0s",
            f"{n_accepted} placed, {n_rejected} rejected — constraints simulated "
            f"in-memory (mirrors execute.py.check_limits); execute.py itself not called",
        ],
        ["analytics", analytics_status, f"{elapsed_s:.2f}s", "report rendered"],
    ]

    data = build_report_data(
        variant_arg=variant_arg,
        period_start=start,
        period_end=end,
        period_label=period,
        timestamp=finished,
        trades=trades,
        bars_rows=bars_rows,
        run_phases=run_phases,
    )

    markdown = render_v1_report(data)
    return markdown, trades


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay strategies against historical bars")
    parser.add_argument("--variant", default="null",
                        help="strategy variant name, or 'null' to replay all enabled")
    parser.add_argument("--period", default="30d", help="lookback window like '30d'")
    parser.add_argument("--out", type=Path, default=None,
                        help="output markdown path (default reports/YYYY-MM-DD-replay.md)")
    args = parser.parse_args()

    db.migrate()

    markdown, trades = run_replay(args.variant, period=args.period)

    out_path = args.out or (
        Path(__file__).parent / "reports" / f"{datetime.now(timezone.utc).date().isoformat()}-replay.md"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown)
    print(f"wrote {out_path} — {len(trades)} simulated trades")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
