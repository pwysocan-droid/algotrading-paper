"""Signal layer — runs each enabled variant against latest bars.

For Week 1, STRATEGY_VARIANTS is empty per the curriculum. The signal
driver runs cleanly against zero variants and emits zero signals. The
strategy interface and Signal dataclass are defined here so Week 2's
strategy-roster review has a stable shape to register against.

Each strategy is a pure function: (bars, params, context) -> Signal | None.
No side effects. The driver below is what writes Signal rows to the DB.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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


def bollinger_strategy(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Textbook Bollinger Bands, mean-reversion (PROJECT.md line 311-312
    confirms the reading: oversold = buy, overbought = sell).

    Band = SMA(period) +/- stddev_mult * population-stdev(period). Buy when
    the latest close is at or below the lower band; sell when at or above
    the upper band. Population stdev (ddof=0), matching the common
    charting-platform convention for this indicator.
    """
    period = int(params.get("period", 20))
    stddev_mult = float(params.get("stddev", 2.0))
    if len(bars) < period:
        return None

    closes = [b.close for b in bars[-period:]]
    mean = sum(closes) / period
    std = statistics.pstdev(closes)
    upper = mean + stddev_mult * std
    lower = mean - stddev_mult * std

    last = bars[-1]
    if last.close <= lower:
        side = "buy"
    elif last.close >= upper:
        side = "sell"
    else:
        return None

    return Signal(
        symbol=last.symbol,
        variant_name="",
        strategy="bollinger",
        side=side,
        bar_timestamp=last.timestamp,
        price_at_signal=last.close,
        reasoning={
            "period": period,
            "stddev_mult": stddev_mult,
            "mean": mean,
            "std": std,
            "upper": upper,
            "lower": lower,
            "close": last.close,
        },
    )


def macross_strategy(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Textbook moving-average crossover.

    Buy on a golden cross (fast SMA crosses above slow SMA); sell on a
    death cross (fast crosses below slow). Needs slow+1 bars so the
    crossing bar can be compared against the bar before it.
    """
    fast_n = int(params.get("fast", 12))
    slow_n = int(params.get("slow", 26))
    if fast_n >= slow_n:
        raise ValueError(f"fast period ({fast_n}) must be < slow period ({slow_n})")
    if len(bars) < slow_n + 1:
        return None

    closes = [b.close for b in bars]

    def sma(values: list[float], n: int) -> float:
        return sum(values[-n:]) / n

    fast_now = sma(closes, fast_n)
    slow_now = sma(closes, slow_n)
    fast_prev = sma(closes[:-1], fast_n)
    slow_prev = sma(closes[:-1], slow_n)

    if fast_prev <= slow_prev and fast_now > slow_now:
        side = "buy"
    elif fast_prev >= slow_prev and fast_now < slow_now:
        side = "sell"
    else:
        return None

    last = bars[-1]
    return Signal(
        symbol=last.symbol,
        variant_name="",
        strategy="macross",
        side=side,
        bar_timestamp=last.timestamp,
        price_at_signal=last.close,
        reasoning={
            "fast": fast_n,
            "slow": slow_n,
            "fast_now": fast_now,
            "slow_now": slow_now,
            "fast_prev": fast_prev,
            "slow_prev": slow_prev,
        },
    )


def null_strategy(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """The placebo arm (roadmap.md "Permanent null variant"; phase1-review.md
    § 5 term 1). Random buy/sell signals with no market information — any
    candidate strategy must beat this under identical constraints, or its
    edge is noise wearing a thesis.

    Deterministic pseudo-randomness from (symbol, bar_timestamp), NOT
    random(): the same bar always produces the same decision, so re-running
    a cycle is idempotent (paired with the signals table's UNIQUE constraint)
    and backtests over the same window are reproducible.
    """
    p = float(params.get("p", 0.10))
    if not bars:
        return None
    last = bars[-1]

    digest = hashlib.sha256(f"{last.symbol}|{last.timestamp}".encode()).digest()
    roll = int.from_bytes(digest[:8], "big") / 2**64  # uniform [0, 1)
    if roll >= p:
        return None
    side = "buy" if digest[8] % 2 == 0 else "sell"

    return Signal(
        symbol=last.symbol,
        variant_name="",
        strategy="null",
        side=side,
        bar_timestamp=last.timestamp,
        price_at_signal=last.close,
        reasoning={"p": p, "roll": roll, "placebo": True},
    )


# ── LLM-surfaced candidates (reviews/candidates-2026-07-16.md) ──────────
# Implemented verbatim from the synthesis specs. All BUY-only; all rely on
# the platform's fixed exits (+5%/-3%/24h) and 1h per-symbol cooldown —
# per-strategy "cooldown_bars" style dedup in the specs is enforced by
# execute.py / apply_portfolio_constraints, not re-implemented here.


def _ts(bar: BarRow) -> datetime:
    dt = datetime.fromisoformat(bar.timestamp)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def liquidation_cascade_reclaim(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Candidate 1 — buy the confirmed reclaim after a 4-sigma panic bar."""
    lookback = int(params.get("lookback_bars", 288))
    sigma_mult = float(params.get("sigma_mult", 4.0))
    min_range = float(params.get("min_range_pct", 0.02))
    search = int(params.get("cascade_search_bars", 6))
    vol_mult = float(params.get("vol_mult", 1.5))
    if len(bars) < lookback + 2:
        return None

    window = bars[-lookback:]
    rets = [
        math.log(window[i].close / window[i - 1].close)
        for i in range(1, len(window))
        if window[i - 1].close > 0
    ]
    if len(rets) < 2:
        return None
    sigma = statistics.pstdev(rets)
    if sigma == 0:
        return None
    avg_vol = sum(b.volume for b in window) / len(window)

    last = bars[-1]
    # cascade bar among the bars preceding the latest (reclaim can't be
    # the cascade bar itself)
    for k in range(2, search + 2):  # bars[-2] .. bars[-(search+1)]
        i = len(bars) - k
        if i < 1:
            break
        bar = bars[i]
        prev = bars[i - 1]
        if prev.close <= 0 or bar.close <= 0:
            continue
        r = math.log(bar.close / prev.close)
        wide = (bar.high - bar.low) / bar.close >= min_range
        if r <= -sigma_mult * sigma and wide:
            p_pre = prev.high
            if last.close > p_pre and last.volume > vol_mult * avg_vol:
                return Signal(
                    symbol=last.symbol, variant_name="",
                    strategy="cascade_reclaim", side="buy",
                    bar_timestamp=last.timestamp, price_at_signal=last.close,
                    reasoning={"cascade_r": r, "sigma": sigma, "p_pre": p_pre,
                               "cascade_ts": bar.timestamp},
                )
    return None


def btc_leads_alt_lag_capture(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Candidate 2 — buy SOL/LINK/AVAX lagging a fresh BTC impulse.

    Needs context['btc_bars'] (driver provides it for variants declaring
    context_keys=['btc_bars']); returns None without it rather than guess.
    """
    window_n = int(params.get("window_bars", 36))
    btc_look = int(params.get("btc_lookback_bars", 3))
    impulse = float(params.get("btc_impulse_pct", 0.012))
    lag_ratio = float(params.get("lag_ratio", 0.5))
    vol_mult = float(params.get("alt_vol_mult", 1.2))
    traded = params.get("traded_symbols", ["SOL", "LINK", "AVAX"])

    if len(bars) < window_n + 1:
        return None
    last = bars[-1]
    if not any(last.symbol.startswith(t) for t in traded):
        return None
    btc_bars: list[BarRow] = context.get("btc_bars") or []
    # use only BTC bars at or before the alt's latest bar (no look-ahead)
    btc = [b for b in btc_bars if b.timestamp <= last.timestamp]
    if len(btc) < max(btc_look + 1, 6):
        return None

    btc_ret = btc[-1].close / btc[-1 - btc_look].close - 1.0
    alt_ret = bars[-1].close / bars[-1 - btc_look].close - 1.0
    alt_window = bars[-window_n:]
    avg_vol = sum(b.volume for b in alt_window) / len(alt_window)
    btc_6high = max(b.close for b in btc[-6:])

    if (
        btc_ret >= impulse
        and alt_ret < lag_ratio * btc_ret
        and last.volume > vol_mult * avg_vol
        and btc[-1].close >= btc_6high
    ):
        return Signal(
            symbol=last.symbol, variant_name="",
            strategy="btc_lag", side="buy",
            bar_timestamp=last.timestamp, price_at_signal=last.close,
            reasoning={"btc_ret": btc_ret, "alt_ret": alt_ret},
        )
    return None


def dead_zone_range_break(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Candidate 3 — overnight-coil breakout on session-open volume."""
    window_n = int(params.get("window_bars", 288))
    dz_start = int(params.get("deadzone_start_utc", 0))
    dz_end = int(params.get("deadzone_end_utc", 6))
    max_coil = float(params.get("max_coil_range", 0.015))
    dz_vol_ratio = float(params.get("deadzone_vol_ratio", 0.6))
    buffer = float(params.get("break_buffer", 0.001))
    vol_exp = float(params.get("vol_expansion_mult", 2.0))
    sess_lo, sess_hi = params.get("session_window_utc", [7, 12])

    if len(bars) < window_n:
        return None
    last = bars[-1]
    last_dt = _ts(last)
    if not (sess_lo <= last_dt.hour < sess_hi):
        return None

    day = last_dt.date()
    dz = [
        b for b in bars
        if _ts(b).date() == day and dz_start <= _ts(b).hour < dz_end
    ]
    if len(dz) < 24:  # need a substantially-covered dead zone (2h+ of bars)
        return None
    dz_high = max(b.high for b in dz)
    dz_low = min(b.low for b in dz)
    if dz_low <= 0:
        return None
    coil = (dz_high - dz_low) / dz_low
    dz_avg_vol = sum(b.volume for b in dz) / len(dz)
    window = bars[-window_n:]
    avg_vol = sum(b.volume for b in window) / len(window)

    if coil > max_coil or dz_avg_vol >= dz_vol_ratio * avg_vol:
        return None
    break_level = dz_high * (1.0 + buffer)
    if last.close <= break_level or last.volume < vol_exp * dz_avg_vol:
        return None
    # first break of the session only
    for b in bars[:-1]:
        b_dt = _ts(b)
        if b_dt.date() == day and sess_lo <= b_dt.hour < sess_hi and b.close > break_level:
            return None
    return Signal(
        symbol=last.symbol, variant_name="",
        strategy="deadzone_break", side="buy",
        bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"coil": coil, "dz_high": dz_high, "dz_avg_vol": dz_avg_vol},
    )


def volume_thrust_regime_shift(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Candidate 4 — initiation thrust (3-sigma volume, directional body,
    VWAP-aligned) confirmed by a non-rejecting follow-through bar."""
    window_n = int(params.get("window_bars", 288))
    vol_z_min = float(params.get("vol_zscore", 3.0))
    body_min = float(params.get("thrust_body_pct", 0.008))
    search = int(params.get("thrust_search_bars", 3))

    if len(bars) < window_n + 1:
        return None
    window = bars[-window_n:]
    vols = [b.volume for b in window]
    mean_v = sum(vols) / len(vols)
    std_v = statistics.pstdev(vols)
    if std_v == 0:
        return None
    denom = sum(b.volume for b in window)
    if denom <= 0:
        return None
    vwap = sum(b.close * b.volume for b in window) / denom

    last = bars[-1]
    for k in range(2, search + 2):  # thrust precedes the confirmation bar
        i = len(bars) - k
        if i < 0:
            break
        t = bars[i]
        if t.open <= 0:
            continue
        vol_z = (t.volume - mean_v) / std_v
        body = (t.close - t.open) / t.open
        if vol_z >= vol_z_min and t.close > t.open and body >= body_min:
            bearish_engulf = last.close < last.open and last.open >= t.close and last.close <= t.open
            if last.close > t.close and last.close > vwap and not bearish_engulf:
                return Signal(
                    symbol=last.symbol, variant_name="",
                    strategy="vol_thrust", side="buy",
                    bar_timestamp=last.timestamp, price_at_signal=last.close,
                    reasoning={"vol_z": vol_z, "thrust_ts": t.timestamp, "vwap": vwap},
                )
    return None


def weekend_illiquidity_momentum(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Candidate 5 — weekend momentum persistence in thin liquidity. The
    synthesis's own flagged regime bet: designed to fail fast in replay
    if the edge has decayed."""
    window_n = int(params.get("window_bars", 72))
    mom_look = int(params.get("mom_lookback_bars", 12))
    mom_min = float(params.get("mom_threshold", 0.015))
    signif = float(params.get("signif_ratio", 2.0))
    persist = int(params.get("persistence_bars", 3))

    if len(bars) < window_n + mom_look:
        return None
    last = bars[-1]
    if _ts(last).weekday() not in (5, 6):  # Sat, Sun
        return None

    mom = last.close / bars[-1 - mom_look].close - 1.0
    if mom < mom_min:
        return None
    window = bars[-window_n:]
    hourly = [
        window[i].close / window[i - mom_look].close - 1.0
        for i in range(mom_look, len(window))
        if window[i - mom_look].close > 0
    ]
    if len(hourly) < 2:
        return None
    sigma_h = statistics.pstdev(hourly)
    if sigma_h == 0 or mom / sigma_h < signif:
        return None
    if not all(b.close > b.open for b in bars[-persist:]):
        return None
    return Signal(
        symbol=last.symbol, variant_name="",
        strategy="weekend_momentum", side="buy",
        bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"mom": mom, "sigma_h": sigma_h},
    )


# ── Foundry round 001 (reviews/foundry/round-001.md) ────────────────────
# Implemented from the round specs. Documented approximations are noted
# per strategy; per-coil/per-event dedup leans on the platform's 1h
# cooldown as with the earlier candidates.


_ENTROPY_CACHE: dict[tuple[str, str], float] = {}


def _entropy_at(bars: list[BarRow], idx: int, n_bins: int = 5,
                sym_window: int = 48, ent_window: int = 24) -> float | None:
    """Shannon entropy (bits) of the 5-bin return-symbol distribution over
    the ent_window returns ending at bars[idx]. Cached by (symbol, ts) —
    each bar's H is computed once per process, which keeps the rolling-
    percentile scan tractable over multi-year replays."""
    key = (bars[idx].symbol, bars[idx].timestamp)
    if key in _ENTROPY_CACHE:
        return _ENTROPY_CACHE[key]
    if idx + 1 < sym_window + 1:
        return None
    window = bars[idx + 1 - sym_window: idx + 1]
    rets = [
        math.log(window[i].close / window[i - 1].close)
        for i in range(1, len(window)) if window[i - 1].close > 0
    ]
    if len(rets) < ent_window:
        return None
    mags = sorted(abs(r) for r in rets)
    t1 = mags[len(mags) // 3]
    t2 = mags[2 * len(mags) // 3]

    def symbol(r: float) -> int:
        a = abs(r)
        if a <= t1:
            return 2  # flat-ish
        big = a > t2
        if r > 0:
            return 4 if big else 3
        return 0 if big else 1

    tail = rets[-ent_window:]
    counts: dict[int, int] = {}
    for r in tail:
        s = symbol(r)
        counts[s] = counts.get(s, 0) + 1
    h = -sum((c / ent_window) * math.log2(c / ent_window) for c in counts.values())
    _ENTROPY_CACHE[key] = h
    return h


def entropy_collapse_impulse(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-001 idea 1. Approximations vs spec, documented: the 15th-
    percentile test uses a linear count against the trailing hist_window
    H values (no sort), the same threshold is applied to all coil_min_bars
    bars, and one-entry-per-coil is enforced by requiring the previous bar
    not to have been a qualifying surprise (plus the platform cooldown)."""
    ent_window = int(params.get("entropy_window", 24))
    pctile = float(params.get("coil_percentile", 15))
    coil_min = int(params.get("coil_min_bars", 6))
    sigma_mult = float(params.get("surprise_sigma", 2.5))
    hist = int(params.get("hist_window", 288))

    need = hist + coil_min + 48 + 2
    if len(bars) < need:
        return None
    last_i = len(bars) - 1

    h_hist = []
    for k in range(hist):
        h = _entropy_at(bars, last_i - 1 - coil_min - k)
        if h is None:
            return None
        h_hist.append(h)
    cut_rank = int(len(h_hist) * pctile / 100)

    def below_threshold(h_val: float) -> bool:
        return sum(1 for x in h_hist if x < h_val) < cut_rank

    for j in range(1, coil_min + 1):  # bars[-2] .. bars[-1-coil_min]
        h = _entropy_at(bars, last_i - j)
        if h is None or not below_threshold(h):
            return None

    rets = [
        math.log(bars[i].close / bars[i - 1].close)
        for i in range(last_i - ent_window + 1, last_i + 1)
        if bars[i - 1].close > 0
    ]
    if len(rets) < 2:
        return None
    prior = rets[:-1]
    mu = sum(prior) / len(prior)
    sd = math.sqrt(sum((r - mu) ** 2 for r in prior) / len(prior))
    if sd == 0:
        return None
    r_t = rets[-1]
    if abs(r_t) <= sigma_mult * sd:
        return None
    # one-entry-per-coil dedup: previous bar must not already have surprised
    if len(rets) >= 3 and abs(rets[-2]) > sigma_mult * sd:
        return None

    last = bars[-1]
    return Signal(
        symbol=last.symbol, variant_name="", strategy="entropy_impulse",
        side="buy" if r_t > 0 else "sell",
        bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"r_t": r_t, "sigma": sd},
    )


def omori_aftershock_ladder(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-001 idea 2 — trade WITH the mainshock during its aftershock
    decay window, unless the window already retraced (exhaustion)."""
    ms_sigma = float(params.get("mainshock_sigma", 4.0))
    ms_vol = float(params.get("mainshock_vol_mult", 3.0))
    std_w = int(params.get("std_window", 96))
    after_w = int(params.get("aftershock_window", 12))
    retrace_pct = float(params.get("retrace_skip_pct", 50)) / 100.0
    vol_w = int(params.get("aftershock_vol_window", 24))

    if len(bars) < std_w + after_w + 2:
        return None
    last = bars[-1]

    for k in range(2, after_w + 2):  # mainshock strictly before the latest bar
        i = len(bars) - k
        ms = bars[i]
        prev = bars[i - 1]
        if prev.close <= 0 or ms.close <= 0:
            continue
        base = bars[i - std_w: i]
        if len(base) < std_w:
            break
        rets = [
            math.log(base[j].close / base[j - 1].close)
            for j in range(1, len(base)) if base[j - 1].close > 0
        ]
        sd = statistics.pstdev(rets) if len(rets) > 1 else 0.0
        med_vol = statistics.median(b.volume for b in base)
        if sd == 0 or med_vol <= 0:
            continue
        r_ms = math.log(ms.close / prev.close)
        if abs(r_ms) <= ms_sigma * sd or ms.volume <= ms_vol * med_vol:
            continue
        direction = 1 if r_ms > 0 else -1
        ms_range = ms.high - ms.low
        if ms_range <= 0:
            continue
        after = bars[i + 1:]
        if direction > 0:
            worst = min((b.low for b in after), default=ms.close)
            retraced = (ms.close - worst) > retrace_pct * ms_range
            beyond = last.close > ms.close
        else:
            worst = max((b.high for b in after), default=ms.close)
            retraced = (worst - ms.close) > retrace_pct * ms_range
            beyond = last.close < ms.close
        recent_med = statistics.median(b.volume for b in bars[-vol_w:])
        if retraced or not beyond or last.volume <= recent_med:
            continue
        return Signal(
            symbol=last.symbol, variant_name="", strategy="omori_aftershock",
            side="buy" if direction > 0 else "sell",
            bar_timestamp=last.timestamp, price_at_signal=last.close,
            reasoning={"mainshock_ts": ms.timestamp, "r_ms": r_ms},
        )
    return None


def failed_auction_rejection_wick(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-001 idea 3 — fresh-extreme, high-volume rejection bar; trade
    the trapped side's forced cover away from the rejected extreme."""
    ext_w = int(params.get("extreme_window", 48))
    wick_body = float(params.get("wick_body_mult", 2.0))
    wick_frac = float(params.get("wick_range_frac", 0.6))
    vol_mult = float(params.get("vol_mult", 2.5))

    if len(bars) < ext_w + 2:
        return None
    rej = bars[-1]
    prior = bars[-1 - ext_w: -1]
    rng = rej.high - rej.low
    body = abs(rej.close - rej.open)
    if rng <= 0:
        return None
    med_vol = statistics.median(b.volume for b in prior)
    if med_vol <= 0 or rej.volume <= vol_mult * med_vol:
        return None
    prior_high = max(b.high for b in prior)
    prior_low = min(b.low for b in prior)

    upper_wick = rej.high - max(rej.open, rej.close)
    lower_wick = min(rej.open, rej.close) - rej.low

    if (rej.high > prior_high and upper_wick >= wick_body * body
            and upper_wick >= wick_frac * rng and rej.close < prior_high):
        side = "sell"
    elif (rej.low < prior_low and lower_wick >= wick_body * body
            and lower_wick >= wick_frac * rng and rej.close > prior_low):
        side = "buy"
    else:
        return None
    return Signal(
        symbol=rej.symbol, variant_name="", strategy="auction_wick",
        side=side, bar_timestamp=rej.timestamp, price_at_signal=rej.close,
        reasoning={"upper_wick": upper_wick, "lower_wick": lower_wick, "range": rng},
    )


def round_number_overshoot_snap(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-001 idea 4 — stop-hunt overshoot through a fresh round level,
    rejected within the bar; enter the reversion."""
    over_frac = float(params.get("overshoot_frac", 0.004))
    vol_mult = float(params.get("vol_mult", 2.0))
    vol_w = int(params.get("vol_window", 48))
    fresh_w = int(params.get("fresh_level_window", 24))

    if len(bars) < max(vol_w, fresh_w) + 2:
        return None
    last = bars[-1]
    if last.symbol.startswith("BTC"):
        grid = 1000.0
    elif last.symbol.startswith("ETH"):
        grid = 100.0
    else:
        grid = 10.0

    med_vol = statistics.median(b.volume for b in bars[-1 - vol_w: -1])
    if med_vol <= 0 or last.volume <= vol_mult * med_vol:
        return None

    lo_level = math.floor(last.low / grid) * grid
    for level in (lo_level + grid * k for k in range(0, 3)):
        if not (last.low < level < last.high):
            continue
        opened_below = last.open < level
        closed_below = last.close < level
        if opened_below and closed_below and (last.high - level) >= over_frac * level:
            side = "sell"  # up-spike through level, rejected back down
        elif not opened_below and not closed_below and (level - last.low) >= over_frac * level:
            side = "buy"  # down-spike through level, rejected back up
        else:
            continue
        fresh = all(
            not (b.low < level < b.high) for b in bars[-1 - fresh_w: -1]
        )
        if not fresh:
            continue
        return Signal(
            symbol=last.symbol, variant_name="", strategy="round_number_snap",
            side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
            reasoning={"level": level, "grid": grid},
        )
    return None


def drawdown_regime_contrarian_gate(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-001 idea 5 — the system observing itself: a 24-bar breakout
    armed ONLY when context['system_state'] says the null arm is failing
    (directional regime) and the portfolio isn't in a stop-out cluster.
    Returns None without the context feed rather than guess."""
    brk_w = int(params.get("breakout_window", 24))
    vol_mult = float(params.get("vol_mult", 1.5))
    vol_w = int(params.get("vol_window", 48))
    gate_wr = float(params.get("null_winrate_gate", 0.35))
    dd_max = int(params.get("drawdown_cluster_max", 2))

    state = context.get("system_state")
    if not state:
        return None
    wr = state.get("null_win_rate")
    stopouts = state.get("recent_stopouts", 0)
    if wr is None or wr >= gate_wr or stopouts >= dd_max:
        return None

    if len(bars) < max(brk_w, vol_w) + 2:
        return None
    last = bars[-1]
    prior = bars[-1 - brk_w: -1]
    med_vol = statistics.median(b.volume for b in bars[-1 - vol_w: -1])
    if med_vol <= 0 or last.volume <= vol_mult * med_vol:
        return None
    if last.close > max(b.high for b in prior):
        side = "buy"
    elif last.close < min(b.low for b in prior):
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="regime_gate_breakout",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"null_win_rate": wr, "recent_stopouts": stopouts},
    )


STRATEGY_REGISTRY: dict[str, StrategyFn] = {
    "bollinger": bollinger_strategy,
    "macross": macross_strategy,
    "null": null_strategy,
    "cascade_reclaim": liquidation_cascade_reclaim,
    "btc_lag": btc_leads_alt_lag_capture,
    "deadzone_break": dead_zone_range_break,
    "vol_thrust": volume_thrust_regime_shift,
    "weekend_momentum": weekend_illiquidity_momentum,
    "entropy_impulse": entropy_collapse_impulse,
    "omori_aftershock": omori_aftershock_ladder,
    "auction_wick": failed_auction_rejection_wick,
    "round_number_snap": round_number_overshoot_snap,
    "regime_gate_breakout": drawdown_regime_contrarian_gate,
}


def get_strategy_fn(name: str) -> StrategyFn:
    if name not in STRATEGY_REGISTRY:
        raise KeyError(
            f"strategy {name!r} not registered. Known strategies: "
            f"{sorted(STRATEGY_REGISTRY.keys())!r}"
        )
    return STRATEGY_REGISTRY[name]


def load_recent_bars(
    conn: sqlite3.Connection, symbol: str, limit: int = 400
) -> list[BarRow]:
    """Default 400 matches replay's window_cap — sim-to-live parity. The
    old 200 silently starved any strategy needing more (vol_thrust needs
    289: it could NEVER fire live — found designing the parity check)."""
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


def load_system_state(
    conn: sqlite3.Connection, now: datetime | None = None, lookback_hours: int = 24
) -> dict[str, Any]:
    """The meta context feed (context_keys=['system_state']): the null
    arm's realized win rate and the portfolio's stop-out count over the
    trailing window — the system's own outcomes as a regime signal."""
    ts = now or datetime.now(timezone.utc)
    since = (ts - timedelta(hours=lookback_hours)).isoformat()
    row = conn.execute(
        """
        SELECT SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) AS wins,
               COUNT(*) AS closed
          FROM trades
         WHERE variant_name = 'null_baseline' AND status = 'closed'
           AND exit_time >= ?
        """,
        (since,),
    ).fetchone()
    wins, closed = row["wins"] or 0, row["closed"] or 0
    stopouts = conn.execute(
        """
        SELECT COUNT(*) AS n FROM trades
         WHERE status = 'closed' AND exit_reason = 'stop_loss' AND exit_time >= ?
        """,
        (since,),
    ).fetchone()["n"]
    return {
        "null_win_rate": (wins / closed) if closed else None,
        "recent_stopouts": stopouts,
    }


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
    ctx = dict(context or {})
    # context_keys is the declared-dependency mechanism (PROJECT.md
    # strategy registry); 'btc_bars' gives cross-symbol lead-lag
    # strategies the BTC window alongside the traded symbol's bars.
    if "btc_bars" in variant.get("context_keys", []) and "btc_bars" not in ctx:
        ctx["btc_bars"] = load_recent_bars(conn, "BTC/USD", limit=300)
    if "system_state" in variant.get("context_keys", []) and "system_state" not in ctx:
        ctx["system_state"] = load_system_state(conn)

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
