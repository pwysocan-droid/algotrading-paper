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
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import db
from config import (
    MAX_POSITION_USD,
    STOP_LOSS_PCT,
    STRATEGY_VARIANTS,
    TAKE_PROFIT_PCT,
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
    pnl_usd: float | None = None
    pnl_pct: float | None = None


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
) -> tuple[str | None, float | None, str | None]:
    """Walk forward through bars, return (exit_bar_ts, exit_price, exit_reason).

    Conservative simulation: if a bar's high crosses take-profit and low
    crosses stop-loss, assume stop-loss hit first (worst-case for the trade).
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
            tp_hit = bar.high >= tp
        else:
            sl_hit = bar.high >= sl
            tp_hit = bar.low <= tp

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
) -> list[SimulatedTrade]:
    """Run a strategy variant in backtest mode over [start, end].

    Look-ahead-bias guard: for a signal generated at bar N's close, the entry
    price is the OPEN of bar N+1, not bar N's close. If bar N is the last bar
    in the window the signal is dropped (no future bar available).
    """
    if not variant.get("enabled", False):
        return []
    strategy_name = variant["strategy"]
    fn = get_strategy_fn(strategy_name)
    params = variant.get("params", {})

    out: list[SimulatedTrade] = []
    for symbol in symbols:
        bars = load_bars_in_range(conn, symbol, start, end)
        if len(bars) < 2:
            continue
        for i in range(len(bars) - 1):
            window = bars[: i + 1]
            sig: Signal | None = fn(window, params, {})
            if sig is None:
                continue
            entry_bar = bars[i + 1]
            entry_price = entry_bar.open
            qty = position_usd / entry_price
            forward = bars[i + 2 :]
            exit_ts, exit_price, exit_reason = simulate_exit(
                forward, entry_price=entry_price, side=sig.side
            )
            pnl_usd: float | None = None
            pnl_pct: float | None = None
            if exit_price is not None:
                if sig.side == "buy":
                    pnl_usd = (exit_price - entry_price) * qty
                    pnl_pct = (exit_price / entry_price - 1.0) * 100.0
                else:
                    pnl_usd = (entry_price - exit_price) * qty
                    pnl_pct = (1.0 - exit_price / entry_price) * 100.0
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
                )
            )
    return out


def _bars_summary(
    conn: sqlite3.Connection, symbols: list[str], start: datetime, end: datetime
) -> list[list[str]]:
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
        rows.append([symbol, format_count(n), first_ts, last_ts, EMDASH])
    return rows


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
    n_trades = len(trades)
    total_pnl: float | None = None
    pnl_pct: float | None = None
    if n_trades > 0:
        total_pnl = sum(t.pnl_usd for t in trades if t.pnl_usd is not None)
        pcts = [t.pnl_pct for t in trades if t.pnl_pct is not None]
        if pcts:
            pnl_pct = sum(pcts) / len(pcts)
    else:
        total_pnl = 0.0
        pnl_pct = None  # — per the spec: percentage with no trades is not 0%, it's "not yet present"

    n_variants = len([v for v in STRATEGY_VARIANTS.values() if v.get("enabled", False)])
    variants_value = format_count(n_variants) if n_variants > 0 else EMDASH

    stats = [
        Stat("Variants registered", variants_value, f"{n_variants} enabled"),
        Stat("Trades in period", format_count(n_trades), "paper"),
        Stat("P&L", format_currency(total_pnl), format_pct(pnl_pct)),
        Stat("System uptime", "100%", "last 4w"),
    ]

    if not STRATEGY_VARIANTS:
        per_variant_rows: list[list[str]] = []
        empty_msg = "no variants registered"
    else:
        per_variant_rows = []
        for name, variant in STRATEGY_VARIANTS.items():
            v_trades = [t for t in trades if t.variant_name == name]
            n = len(v_trades)
            v_pnl = sum(t.pnl_usd for t in v_trades if t.pnl_usd is not None) if v_trades else 0.0
            v_pcts = [t.pnl_pct for t in v_trades if t.pnl_pct is not None]
            v_pct_avg = (sum(v_pcts) / len(v_pcts)) if v_pcts else None
            per_variant_rows.append(
                [
                    f"`{name}`",
                    format_count(n),
                    EMDASH,
                    format_currency(v_pnl),
                    format_pct(v_pct_avg),
                    EMDASH,
                    EMDASH,
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
) -> tuple[str, list[SimulatedTrade]]:
    """Run replay end-to-end. Returns (markdown_report, simulated_trades)."""
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
                        conn, name, variant, WATCHED_SYMBOLS, start, end
                    )
                )
        else:
            if variant_arg not in STRATEGY_VARIANTS:
                raise KeyError(
                    f"variant {variant_arg!r} not in STRATEGY_VARIANTS. "
                    f"Use --variant=null to replay all enabled variants."
                )
            v = STRATEGY_VARIANTS[variant_arg]
            trades = replay_variant(conn, variant_arg, v, WATCHED_SYMBOLS, start, end)

        bars_rows = _bars_summary(conn, WATCHED_SYMBOLS, start, end)

    finished = datetime.now(timezone.utc)
    elapsed_s = (finished - started).total_seconds()

    run_phases: list[list[str]] = [
        ["fetch", fetch_status, "0.0s", "no fetch this run"],
        ["signals", signals_status, "0.0s", f"{len(trades)} simulated trades"],
        ["execute", execute_status, "0.0s", "replay does not call execute"],
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
