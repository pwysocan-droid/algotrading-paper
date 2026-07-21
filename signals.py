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
    if fast_n >= slow_n or fast_n <= 0:
        return None  # invalid config must not kill the cycle (audit 2026-07-17)
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
        if window[i - 1].close > 0 and window[i].close > 0
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

    if btc[-1 - btc_look].close <= 0 or bars[-1 - btc_look].close <= 0:
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

    if bars[-1 - mom_look].close <= 0:
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
        for i in range(1, len(window))
        if window[i - 1].close > 0 and window[i].close > 0
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
        if bars[i - 1].close > 0 and bars[i].close > 0
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
            for j in range(1, len(base))
            if base[j - 1].close > 0 and base[j].close > 0
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


# ── Foundry round 002 (reviews/foundry/round-002.md) ────────────────────
# Round thesis: invert each dead polarity — trade phase TRANSITIONS as
# continuation (entropy delta not level, contagion growth not decay,
# absorption breaks not wick fades, named expiry releases not generic
# coils) and remount the proven meta-gate on a strong engine.


def _sign(x: float) -> int:
    return 1 if x > 0 else 0


def _conditional_entropy(signs: list[int], order: int = 2) -> float | None:
    """H(next sign | previous `order` signs), in bits. None when there are
    no transitions to estimate from."""
    if len(signs) <= order:
        return None
    ctx_counts: dict[tuple[int, ...], dict[int, int]] = {}
    for i in range(order, len(signs)):
        ctx = tuple(signs[i - order: i])
        ctx_counts.setdefault(ctx, {}).setdefault(signs[i], 0)
        ctx_counts[ctx][signs[i]] += 1
    total = sum(sum(d.values()) for d in ctx_counts.values())
    if total == 0:
        return None
    h = 0.0
    for d in ctx_counts.values():
        n_ctx = sum(d.values())
        p_ctx = n_ctx / total
        h_ctx = -sum((c / n_ctx) * math.log2(c / n_ctx) for c in d.values())
        h += p_ctx * h_ctx
    return h


def conditional_entropy_regime_expansion(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-002 idea 1 — trade the SURGE in conditional entropy of the
    sign sequence (information arrival breaking a predictable regime) as
    continuation in the surprising bar's direction. Inverts the dead
    entropy_collapse_impulse, which traded low entropy LEVEL."""
    jump = float(params.get("entropy_jump", 0.35))
    vol_mult = float(params.get("vol_mult", 2.2))
    order = int(params.get("cond_order", 2))
    long_w = int(params.get("long_window", 60))
    short_w = int(params.get("short_window", 12))

    if len(bars) < long_w + order + 2:
        return None
    window = bars[-(long_w + 1):]
    rets = [
        math.log(window[i].close / window[i - 1].close)
        for i in range(1, len(window))
        if window[i - 1].close > 0 and window[i].close > 0
    ]
    if len(rets) < long_w:
        return None
    signs = [_sign(r) for r in rets]
    h_long = _conditional_entropy(signs, order)
    h_short = _conditional_entropy(signs[-short_w:], order)
    if h_long is None or h_short is None or (h_short - h_long) <= jump:
        return None
    mean_abs = sum(abs(r) for r in rets) / len(rets)
    if mean_abs <= 0 or abs(rets[-1]) <= vol_mult * mean_abs:
        return None
    if _sign(rets[-1]) != _sign(rets[-2]):  # last two bars share a sign
        return None
    last = bars[-1]
    return Signal(
        symbol=last.symbol, variant_name="", strategy="cond_entropy_expansion",
        side="buy" if rets[-1] > 0 else "sell",
        bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"h_short": h_short, "h_long": h_long, "r_t": rets[-1]},
    )


def _signed_volume(b: BarRow) -> float:
    """sv = volume * sign(close - open); a doji carries no direction."""
    if b.close > b.open:
        return b.volume
    if b.close < b.open:
        return -b.volume
    return 0.0


def _r0_at(bars: list[BarRow], idx: int, decay: float, window: int) -> tuple[float, float]:
    """(R0, IP_cur) at bars[idx]: reproduction ratio of signed volume.
    IP_cur decays over the last `window` bars; the prior window's pressure
    is naturally decayed by its distance in the same kernel."""
    ip_cur = sum(_signed_volume(bars[idx - k]) * (decay ** k) for k in range(window))
    ip_prev = sum(
        _signed_volume(bars[idx - k]) * (decay ** k)
        for k in range(window, 2 * window)
    )
    r0 = abs(ip_cur) / (abs(ip_prev) + 1e-9)
    return r0, ip_cur


def _r0_ignition_trigger(
    bars: list[BarRow], r0_thresh: float, consistency_bars: int,
    decay: float = 0.85, window: int = 6, median_window: int = 60,
) -> tuple[str, float] | None:
    """Shared engine for round-002 ideas 2 and 5: signed-volume R0 crossing
    from <1 to >r0_thresh with directional consistency and above-median
    6-bar flow. Returns (side, r0) or None."""
    need = median_window + 2 * window + 2
    if len(bars) < need:
        return None
    last_i = len(bars) - 1
    r0_now, ip_cur = _r0_at(bars, last_i, decay, window)
    r0_prev, _ = _r0_at(bars, last_i - 1, decay, window)
    if not (r0_prev < 1.0 and r0_now > r0_thresh):
        return None
    direction = 1 if ip_cur > 0 else -1
    same = sum(
        1 for k in range(window)
        if _signed_volume(bars[last_i - k]) * direction > 0
    )
    if same < consistency_bars:
        return None
    def six_sum(idx: int) -> float:
        return abs(sum(_signed_volume(bars[idx - k]) for k in range(window)))
    hist = sorted(six_sum(last_i - j) for j in range(1, median_window + 1))
    med = hist[len(hist) // 2]
    if six_sum(last_i) <= med:
        return None
    return ("buy" if direction > 0 else "sell", r0_now)


def epidemic_r0_crossover_ignition(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-002 idea 2 — epidemiology's GROWTH phase: fire when the
    signed-volume reproduction number crosses from <1 (impulses dying)
    to >r0_thresh (self-amplifying contagion). Inverts dead Omori decay."""
    trig = _r0_ignition_trigger(
        bars,
        r0_thresh=float(params.get("r0_thresh", 1.5)),
        consistency_bars=int(params.get("consistency_bars", 5)),
        decay=float(params.get("decay_lambda", 0.85)),
        window=int(params.get("window", 6)),
        median_window=int(params.get("median_window", 60)),
    )
    if trig is None:
        return None
    side, r0 = trig
    last = bars[-1]
    return Signal(
        symbol=last.symbol, variant_name="", strategy="r0_ignition",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"r0": r0},
    )


def absorption_shelf_breakout(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-002 idea 3 — high-volume/low-progress shelf (iceberg being
    eaten) breaking on expansion: continuation, the inverse of the dead
    wick fade. Documented approximation: the break may come up to 3 bars
    after the shelf ends; intermediate bars must not already have broken
    (first-break-only), and per-event dedup leans on the 1h cooldown."""
    shelf_len = int(params.get("shelf_len", 6))
    vol_mult = float(params.get("vol_mult", 1.3))
    body_frac = float(params.get("body_frac", 0.4))
    span_frac = float(params.get("span_frac", 1.2))
    break_atr = float(params.get("break_atr", 0.5))
    atr_w = int(params.get("atr_window", 14))
    med_w = 60
    max_gap = 3  # bars between shelf end and break

    if len(bars) < med_w + shelf_len + atr_w + max_gap + 2:
        return None
    last = bars[-1]
    last_i = len(bars) - 1

    med_vol = statistics.median(b.volume for b in bars[-1 - med_w: -1])
    if med_vol <= 0 or last.volume <= vol_mult * med_vol:
        return None

    tr = []
    for k in range(1, atr_w + 1):
        b, prev = bars[last_i - k], bars[last_i - k - 1]
        tr.append(max(b.high - b.low, abs(b.high - prev.close), abs(b.low - prev.close)))
    atr = sum(tr) / len(tr)
    if atr <= 0:
        return None

    for gap in range(max_gap + 1):
        end = last_i - 1 - gap  # last shelf bar
        shelf = bars[end - shelf_len + 1: end + 1]
        if len(shelf) < shelf_len:
            continue
        ok = True
        for b in shelf:
            rng = b.high - b.low
            if rng <= 0 or b.volume <= vol_mult * med_vol or abs(b.close - b.open) >= body_frac * rng:
                ok = False
                break
        if not ok:
            continue
        span = max(b.high for b in shelf) - min(b.low for b in shelf)
        avg_rng = sum(b.high - b.low for b in shelf) / shelf_len
        if span >= span_frac * avg_rng:
            continue
        shelf_high = max(b.high for b in shelf)
        shelf_low = min(b.low for b in shelf)
        up_lvl = shelf_high + break_atr * atr
        dn_lvl = shelf_low - break_atr * atr
        between = bars[end + 1: last_i]
        if any(b.close > up_lvl or b.close < dn_lvl for b in between):
            continue  # not the first break
        if last.close > up_lvl:
            side = "buy"
        elif last.close < dn_lvl:
            side = "sell"
        else:
            continue
        return Signal(
            symbol=last.symbol, variant_name="", strategy="absorption_shelf",
            side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
            reasoning={"shelf_high": shelf_high, "shelf_low": shelf_low, "atr": atr},
        )
    return None


def options_expiry_pin_release(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-002 idea 4 — post-08:00-UTC pin release: gamma/funding
    pinning compresses the pre-settlement range; trade the first
    qualifying break after the suppressor is removed. Documented
    approximation: friday_weight is not implementable on a fixed-$200
    platform (no position sizing), so Fridays get no extra weight."""
    pin_span = float(params.get("pin_span_pct", 0.8)) / 100.0
    brk = float(params.get("break_frac_pct", 0.35)) / 100.0
    vol_mult = float(params.get("vol_mult", 1.5))
    pre_w = int(params.get("pre_window", 12))
    post_min = int(params.get("post_window_min", 60))

    if len(bars) < pre_w + 20:
        return None
    last = bars[-1]
    t = _ts(last)
    release = t.replace(hour=8, minute=0, second=0, microsecond=0)
    if not (release + timedelta(minutes=5) <= t < release + timedelta(minutes=5 + post_min)):
        return None

    pin = [b for b in bars[:-1] if release - timedelta(minutes=5 * pre_w) <= _ts(b) < release]
    if len(pin) < pre_w:
        return None
    pin_high = max(b.high for b in pin)
    pin_low = min(b.low for b in pin)
    ref = pin[-1].close
    if ref <= 0 or (pin_high - pin_low) >= pin_span * ref:
        return None
    med_vol = statistics.median(b.volume for b in pin)
    if med_vol <= 0 or last.volume <= vol_mult * med_vol:
        return None

    up_lvl = pin_high * (1.0 + brk)
    dn_lvl = pin_low * (1.0 - brk)
    post = [b for b in bars[:-1] if release <= _ts(b) < t]
    if any(b.close > up_lvl or b.close < dn_lvl for b in post):
        return None  # not the first break of the released pin
    if last.close > up_lvl:
        side = "buy"
    elif last.close < dn_lvl:
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="expiry_pin_release",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"pin_high": pin_high, "pin_low": pin_low, "release": release.isoformat()},
    )


def rejection_streak_gated_ignition(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-002 idea 5 — the prescribed successor to the dead
    drawdown_regime_contrarian_gate: the same self-referential saturation
    gate (system rejection rate + placebo stop rate via system_state)
    mounted on the strong R0-ignition engine instead of a weak breakout.
    Returns None without the context feed rather than guess."""
    gate_rej = float(params.get("gate_rej", 0.6))
    gate_stop = float(params.get("gate_stop", 0.5))

    state = context.get("system_state")
    if not state:
        return None
    rej = state.get("rejection_rate")
    stop = state.get("placebo_stop_rate")
    if rej is None or stop is None or rej <= gate_rej or stop <= gate_stop:
        return None

    trig = _r0_ignition_trigger(
        bars,
        r0_thresh=float(params.get("r0_thresh", 1.5)),
        consistency_bars=int(params.get("consistency_bars", 5)),
    )
    if trig is None:
        return None
    side, r0 = trig
    last = bars[-1]
    return Signal(
        symbol=last.symbol, variant_name="", strategy="rejection_gated_ignition",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"r0": r0, "rejection_rate": rej, "placebo_stop_rate": stop},
    )


# ── Foundry round 003 (reviews/foundry/round-003.md) ────────────────────
# Premise-checked 2026-07-17 against research_bars (BTC, 50k bars):
# gap>0.4% fires 0.1/day (spec said 8-15 — 100x miss), shock 3%+3xvol
# 0.04/day (spec 0.3-0.8), breakout+0.5% ~0.4/day both sides. All exist
# in the data; all far rarer than predicted. Recorded for the epitaphs.


def _gap_exhaustion_trigger(bars: list[BarRow], params: dict[str, Any]) -> str | None:
    """Shared engine for round-003 ideas 1 and 3: a 5-min open gap held
    through the bar (close-through-open in gap direction) with
    above-median body and volume."""
    gap_th = float(params.get("gap_threshold", 0.004))
    body_w = int(params.get("body_lookback", 50))
    vol_w = int(params.get("volume_lookback", 50))
    if len(bars) < max(body_w, vol_w) + 2:
        return None
    last, prev = bars[-1], bars[-2]
    if prev.close <= 0:
        return None
    gap = (last.open - prev.close) / prev.close
    if abs(gap) <= gap_th:
        return None
    direction = 1 if gap > 0 else -1
    body = last.close - last.open
    if direction > 0 and body <= 0:
        return None
    if direction < 0 and body >= 0:
        return None
    med_body = statistics.median(abs(b.close - b.open) for b in bars[-1 - body_w: -1])
    med_vol = statistics.median(b.volume for b in bars[-1 - vol_w: -1])
    if med_vol <= 0 or abs(body) <= med_body or last.volume <= med_vol:
        return None
    return "buy" if direction > 0 else "sell"


def gap_fill_exhaustion_continuation(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-003 idea 1 — a >0.4% open gap that HOLDS through the bar is
    initiative flow, traded as continuation."""
    side = _gap_exhaustion_trigger(bars, params)
    if side is None:
        return None
    last = bars[-1]
    return Signal(
        symbol=last.symbol, variant_name="", strategy="gap_exhaustion",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"gap": (last.open - bars[-2].close) / bars[-2].close},
    )


def asian_to_london_handoff_thrust(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-003 idea 2 — first qualified break of the Asian-session
    range (00:00-06:00 UTC) during the London handoff window, weekdays.
    One fire per symbol per day (first break only + platform cooldown)."""
    a_start = int(params.get("asian_start_utc", 0))
    a_end = int(params.get("asian_end_utc", 6))
    w_start = int(params.get("london_window_start_utc", 7))
    w_end = int(params.get("london_window_end_utc", 9))
    body_w = int(params.get("body_lookback", 50))
    vol_w = int(params.get("volume_lookback", 50))

    if len(bars) < max(body_w, vol_w) + 20:
        return None
    last = bars[-1]
    t = _ts(last)
    if t.weekday() >= 5 or not (w_start <= t.hour < w_end):
        return None
    day0 = t.replace(hour=0, minute=0, second=0, microsecond=0)
    asian = [
        b for b in bars[:-1]
        if day0 + timedelta(hours=a_start) <= _ts(b) < day0 + timedelta(hours=a_end)
    ]
    if len(asian) < (a_end - a_start) * 12 - 12:  # tolerate one missing bar-hour
        return None
    hi = max(b.high for b in asian)
    lo = min(b.low for b in asian)
    window_prior = [
        b for b in bars[:-1] if day0 + timedelta(hours=w_start) <= _ts(b) < t
    ]
    if any(b.close > hi or b.close < lo for b in window_prior):
        return None  # not the first break today
    med_body = statistics.median(abs(b.close - b.open) for b in bars[-1 - body_w: -1])
    med_vol = statistics.median(b.volume for b in bars[-1 - vol_w: -1])
    if med_vol <= 0 or abs(last.close - last.open) <= med_body or last.volume <= med_vol:
        return None
    if last.close > hi:
        side = "buy"
    elif last.close < lo:
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="asian_london_handoff",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"asian_high": hi, "asian_low": lo},
    )


def slot_scarcity_conviction_gate(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-003 idea 3 — the gap engine armed only when the system's
    recent closed trades are NOT clustering at the stop (follow-through
    regime). Returns None without the context feed rather than guess."""
    gate = float(params.get("stop_rate_gate", 0.5))
    state = context.get("system_state")
    if not state:
        return None
    stop_rate = state.get("stop_out_rate")
    if stop_rate is None or stop_rate > gate:
        return None
    side = _gap_exhaustion_trigger(bars, params)
    if side is None:
        return None
    last = bars[-1]
    return Signal(
        symbol=last.symbol, variant_name="", strategy="slot_scarcity_gate",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"stop_out_rate": stop_rate},
    )


def post_shock_multiday_drift(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-003 idea 4 — a single-bar shock (>3% body on 3x volume)
    entered WITH the shock, held for days (tp 12% / sl 5% / 120h): the
    horizon lever applied to information arrival."""
    shock_th = float(params.get("shock_threshold", 0.03))
    vol_mult = float(params.get("volume_mult", 3.0))
    vol_w = int(params.get("volume_lookback", 100))
    if len(bars) < vol_w + 2:
        return None
    last = bars[-1]
    if last.open <= 0:
        return None
    move = (last.close - last.open) / last.open
    if abs(move) <= shock_th:
        return None
    med = statistics.median(b.volume for b in bars[-1 - vol_w: -1])
    if med <= 0 or last.volume <= vol_mult * med:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="post_shock_drift",
        side="buy" if move > 0 else "sell",
        bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"move": move, "vol_ratio": last.volume / med},
    )


def pullback_to_breakout_level_limit(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-003 idea 5 — breakout, then enter on the RETEST of the
    broken level (price comes to you; limit-friendly, pairs with the
    maker fill model). Documented approximations: the signal fires on
    the first bar that touches the level after the most recent qualified
    breakout in the window; entry executes at the platform's next-bar
    price (or rests as a limit under fill_model='maker')."""
    lvl_w = int(params.get("level_lookback", 48))
    margin = float(params.get("breakout_margin", 0.005))
    vol_w = int(params.get("volume_lookback", 50))
    retest_w = int(params.get("retest_window_bars", 24))
    if len(bars) < lvl_w + vol_w + retest_w + 2:
        return None
    last = bars[-1]
    last_i = len(bars) - 1
    for k in range(1, retest_w + 1):  # most recent breakout wins
        j = last_i - k
        if j < max(lvl_w, vol_w) + 1:
            return None
        brk = bars[j]
        med_vol = statistics.median(b.volume for b in bars[j - vol_w: j])
        if med_vol <= 0 or brk.volume <= med_vol:
            continue
        hi = max(b.high for b in bars[j - lvl_w: j])
        lo = min(b.low for b in bars[j - lvl_w: j])
        if brk.close > hi * (1.0 + margin):
            level, side = hi, "buy"
        elif brk.close < lo * (1.0 - margin):
            level, side = lo, "sell"
        else:
            continue
        between = bars[j + 1: last_i]
        touched = (
            any(b.low <= level for b in between) if side == "buy"
            else any(b.high >= level for b in between)
        )
        if touched:
            return None  # retest already happened (or level consumed)
        now_touch = last.low <= level if side == "buy" else last.high >= level
        if not now_touch:
            return None  # armed, still waiting — no chase
        return Signal(
            symbol=last.symbol, variant_name="", strategy="breakout_retest_limit",
            side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
            reasoning={"level": level, "breakout_ts": brk.timestamp},
        )
    return None


# ── Foundry round 004 (reviews/foundry/round-004.md) ────────────────────
# Round thesis: invert-and-time-earlier — round-number breach not snap,
# one-sided expansion not absorption, Hawkes loading-phase not the
# visible impulse, magnitude-compressibility not sign-entropy, and the
# proven regime gate remounted on a genuine momentum-persistence engine.
#
# Premise-checked 2026-07-18 against research_bars (BTC, 50k bars, raw
# engines, gate conditions excluded since they read the live trades
# table): idea1 (fresh-extreme+vol-expansion, gate unchecked) fires
# 5.17/sym/day vs spec's 0.5-1.0 (~5x over); idea2 (magnitude surprise)
# fires 0.74/sym/day vs spec's 0.05-0.15 (~5-10x over) and the required
# pre-check passes — p99 surprise is 4.6, comfortably above the 3.0
# threshold, so magnitude headroom exists unlike sign-entropy; idea3
# (Hawkes intensity crossing 1.5 with low cum-displacement) fires
# 29.7/sym/day vs spec's 0.05-0.15 (~200-600x over) — the 1.5x-median
# event definition is met by ~35% of bars, so the "loading phase" is
# common, not rare; idea4 (one-sided range expansion) fires 1.37/sym/day
# vs spec's 0.5-1.5 (matches); idea5 (round-number coil-then-breach,
# BTC $1000 grid) fires 4.46/sym/day vs spec's 0.06-0.15 (~30-70x over).
# None starved — every idea exists in the data, all far MORE common than
# predicted (the inverse of round-003's under-firing miss). Implemented
# as specified; the gauntlet will show whether the excess fire rate
# dilutes armed/loading-phase selectivity into noise.


def _closed_trade_win_rate(rows: list[Any]) -> float | None:
    closed = [r for r in rows if r["pnl_usd"] is not None]
    if not closed:
        return None
    wins = sum(1 for r in closed if r["pnl_usd"] > 0)
    return wins / len(closed)


def _stopout_cluster_index(
    rows: list[Any], bar_minutes: int = 5, cluster_bars: int = 3
) -> float | None:
    """Fraction of the given (most-recent-first) closed exits that are
    stop-losses landing within `cluster_bars` bars of another stop-loss
    exit in the same set — round-004 idea 1's regime-arming signal."""
    if not rows:
        return None
    times = [datetime.fromisoformat(r["exit_time"]) for r in rows]
    stop_times = [t for r, t in zip(rows, times) if r["exit_reason"] == "stop_loss"]
    window = timedelta(minutes=bar_minutes * cluster_bars)
    clustered = sum(
        1 for t in stop_times
        if any(t != other and abs((t - other).total_seconds()) <= window.total_seconds()
               for other in stop_times)
    )
    return clustered / len(rows)


def trend_persistence_regime_gated_engine(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-004 idea 1 — the proven self-referential gate (null-arm
    win rate over its trailing 100 closed trades + stop-out clustering)
    remounted on a momentum-persistence engine (fresh Donchian extreme
    with volatility expansion and a strong close) instead of a bare
    breakout. Returns None without the context feed rather than guess."""
    donchian_w = int(params.get("donchian_lookback", 24))
    vol_w = int(params.get("vol_window", 12))
    vol_base_w = int(params.get("vol_baseline_window", 96))
    vol_mult = float(params.get("vol_expansion_mult", 1.3))
    close_pos_pct = float(params.get("close_position_pct", 0.2))
    wr_thresh = float(params.get("null_winrate_thresh", 0.38))
    cluster_thresh = float(params.get("stopcluster_thresh", 0.5))

    state = context.get("system_state")
    if not state:
        return None
    wr = state.get("null_win_rate_100")
    cluster = state.get("stopout_cluster_index")
    if wr is None or cluster is None or wr >= wr_thresh or cluster <= cluster_thresh:
        return None

    need = vol_base_w + vol_w + donchian_w + 2
    if len(bars) < need:
        return None
    last = bars[-1]
    prior = bars[-1 - donchian_w: -1]

    def realized_vol(end: int) -> float | None:
        window = bars[end - vol_w: end]
        if len(window) < vol_w:
            return None
        rets = [
            math.log(window[i].close / window[i - 1].close)
            for i in range(1, len(window))
            if window[i - 1].close > 0 and window[i].close > 0
        ]
        return statistics.pstdev(rets) if len(rets) >= 2 else None

    last_i = len(bars) - 1
    cur_vol = realized_vol(last_i + 1)
    baseline = [
        v for j in range(last_i - vol_base_w, last_i - vol_w + 1)
        for v in [realized_vol(j)] if v is not None
    ]
    if cur_vol is None or not baseline:
        return None
    base_med = statistics.median(baseline)
    if base_med <= 0 or cur_vol <= vol_mult * base_med:
        return None

    rng = last.high - last.low
    if rng <= 0:
        return None
    close_pos_val = (last.close - last.low) / rng
    if last.close > max(b.high for b in prior) and close_pos_val >= 1.0 - close_pos_pct:
        side = "buy"
    elif last.close < min(b.low for b in prior) and close_pos_val <= close_pos_pct:
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="trend_persistence_gated",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"null_win_rate_100": wr, "stopout_cluster_index": cluster,
                   "cur_vol": cur_vol, "baseline_vol": base_med},
    )


def return_magnitude_compressibility_break(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-004 idea 2 — a magnitude-sequence novelty detector: fire
    when the current bar's |return| is a 3-sigma surprise against the
    trailing 48-bar magnitude distribution, but the prior 24 bars stayed
    quiet (max surprise < 1.5) — the birth of a volatility cluster, not
    its confirmed middle. Direction is the sign of the surprising bar."""
    mag_w = int(params.get("mag_window", 48))
    surprise_th = float(params.get("surprise_thresh", 3.0))
    quiet_w = int(params.get("prior_quiet_window", 24))
    quiet_max = float(params.get("prior_quiet_max", 1.5))
    close_pos_pct = float(params.get("close_position_pct", 0.25))

    need = mag_w + quiet_w + 2
    if len(bars) < need:
        return None

    def surprise_at(i: int) -> float | None:
        window = bars[i - mag_w: i]
        if len(window) < mag_w or bars[i - 1].close <= 0 or bars[i].close <= 0:
            return None
        mags = [abs(math.log(window[k].close / window[k - 1].close))
                for k in range(1, len(window)) if window[k - 1].close > 0 and window[k].close > 0]
        if len(mags) < mag_w - 1:
            return None
        mu = sum(mags) / len(mags)
        sigma = statistics.pstdev(mags)
        if sigma <= 0:
            return None
        cur = abs(math.log(bars[i].close / bars[i - 1].close))
        return (cur - mu) / sigma

    last_i = len(bars) - 1
    surprise_now = surprise_at(last_i)
    if surprise_now is None or surprise_now <= surprise_th:
        return None
    prior_surprises = [
        s for k in range(last_i - quiet_w, last_i) for s in [surprise_at(k)] if s is not None
    ]
    if not prior_surprises or max(prior_surprises) >= quiet_max:
        return None

    last, prev = bars[last_i], bars[last_i - 1]
    if prev.close <= 0:
        return None
    ret = math.log(last.close / prev.close)
    rng = last.high - last.low
    if rng <= 0:
        return None
    close_pos_val = (last.close - last.low) / rng
    if ret > 0 and close_pos_val >= 1.0 - close_pos_pct:
        side = "buy"
    elif ret < 0 and close_pos_val <= close_pos_pct:
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="magnitude_surprise_break",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"surprise": surprise_now, "prior_max_surprise": max(prior_surprises)},
    )


def hawkes_self_excitation_intensity_entry(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-004 idea 3 — a Hawkes-style event intensity (large bars,
    time-decay kernel) crossing its excitation threshold WHILE cumulative
    displacement is still small: the branching birth, timed before the
    move Omori and R0-ignition chased on the visible impulse."""
    event_mult = float(params.get("event_mult", 1.5))
    median_w = int(params.get("median_window", 96))
    decay = float(params.get("kernel_decay", 0.3))
    intensity_w = int(params.get("intensity_window", 12))
    intensity_th = float(params.get("intensity_thresh", 1.5))
    cum_disp_max = float(params.get("cum_disp_max_pct", 1.0)) / 100.0

    need = median_w + intensity_w + 2
    if len(bars) < need:
        return None

    def log_ret(i: int) -> float | None:
        if bars[i - 1].close <= 0 or bars[i].close <= 0:
            return None
        return math.log(bars[i].close / bars[i - 1].close)

    def intensity_at(i: int) -> tuple[float, float] | None:
        """(lambda, median_magnitude) at index i, or None if underfilled."""
        mags = [abs(r) for k in range(i - median_w, i) for r in [log_ret(k)] if r is not None]
        if len(mags) < median_w - 1:
            return None
        med_mag = statistics.median(mags)
        if med_mag <= 0:
            return None
        lam = 0.0
        for k in range(intensity_w):
            r = log_ret(i - k)
            if r is not None and abs(r) > event_mult * med_mag:
                lam += math.exp(-decay * k)
        return lam, med_mag

    last_i = len(bars) - 1
    now = intensity_at(last_i)
    prev = intensity_at(last_i - 1)
    if now is None or prev is None:
        return None
    lam_now, med_mag = now
    lam_prev, _ = prev
    if not (lam_prev < intensity_th <= lam_now):
        return None

    disp = sum(
        r for k in range(intensity_w) for r in [log_ret(last_i - k)] if r is not None
    )
    if abs(disp) >= cum_disp_max:
        return None

    net_flow = sum(
        (1 if r > 0 else -1)
        for k in range(intensity_w)
        for r in [log_ret(last_i - k)]
        if r is not None and abs(r) > event_mult * med_mag
    )
    if net_flow == 0:
        return None
    last = bars[last_i]
    return Signal(
        symbol=last.symbol, variant_name="", strategy="hawkes_intensity_entry",
        side="buy" if net_flow > 0 else "sell",
        bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"intensity": lam_now, "cum_displacement": disp, "net_flow": net_flow},
    )


def one_sided_range_expansion_thrust(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-004 idea 4 — the inversion of dead absorption: high volume
    AND a large body (positively correlated, unlike absorption's empty
    set) with the close pinned at the extreme and minimal opposing wick —
    a cleared-book continuation thrust, not a fade."""
    body_mult = float(params.get("body_mult", 2.0))
    vol_mult = float(params.get("vol_mult", 1.5))
    med_w = int(params.get("median_window", 96))
    same_wick_max = float(params.get("same_dir_wick_max", 0.15))
    opp_wick_max = float(params.get("opp_wick_max", 0.4))
    extreme_w = int(params.get("extreme_lookback", 12))

    need = med_w + extreme_w + 2
    if len(bars) < need:
        return None
    last = bars[-1]
    window = bars[-1 - med_w: -1]
    med_body = statistics.median(abs(b.close - b.open) for b in window)
    med_vol = statistics.median(b.volume for b in window)
    if med_body <= 0 or med_vol <= 0:
        return None
    body = last.close - last.open
    if abs(body) <= body_mult * med_body or last.volume <= vol_mult * med_vol:
        return None

    prior_extreme = bars[-1 - extreme_w: -1]
    if body > 0:
        same_wick = last.high - last.close
        opp_wick = last.open - last.low
        if same_wick >= same_wick_max * abs(body) or opp_wick >= opp_wick_max * abs(body):
            return None
        if last.close <= max(b.high for b in prior_extreme):
            return None
        side = "buy"
    else:
        same_wick = last.open - last.low
        opp_wick = last.high - last.close
        if same_wick >= same_wick_max * abs(body) or opp_wick >= opp_wick_max * abs(body):
            return None
        if last.close >= min(b.low for b in prior_extreme):
            return None
        side = "sell"
    return Signal(
        symbol=last.symbol, variant_name="", strategy="one_sided_expansion_thrust",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"body": body, "med_body": med_body, "vol_ratio": last.volume / med_vol},
    )


_ROUND_NUMBER_GRID: dict[str, float] = {
    "BTC/USD": 1000.0, "ETH/USD": 100.0, "SOL/USD": 10.0,
    "LINK/USD": 1.0, "AVAX/USD": 1.0,
}


def round_number_breach_continuation(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-004 idea 5 — the continuation inverse of dead
    round_number_overshoot_snap: price coils near a round level, then
    decisively breaches it on volume — a stop cascade on the far side
    fuels the move rather than snapping back. Not a clock-time coil (the
    4-for-4 named-time deaths), a price-level order-flow reservoir."""
    proximity = float(params.get("proximity_pct", 0.3)) / 100.0
    coil_required = int(params.get("coil_bars_required", 6))
    coil_w = int(params.get("coil_window", 12))
    breach = float(params.get("breach_pct", 0.4)) / 100.0
    vol_mult = float(params.get("vol_mult", 1.3))
    close_pos_pct = float(params.get("close_position_pct", 0.25))
    vol_w = 96

    need = coil_w + vol_w + 2
    if len(bars) < need:
        return None
    last = bars[-1]
    grid = _ROUND_NUMBER_GRID.get(last.symbol)
    if not grid:
        return None

    coil = bars[-1 - coil_w: -1]
    level = round(coil[-1].close / grid) * grid
    if level <= 0:
        return None
    near = sum(1 for b in coil if abs(b.close - level) / level <= proximity)
    if near < coil_required:
        return None

    med_vol = statistics.median(b.volume for b in bars[-1 - vol_w: -1])
    if med_vol <= 0 or last.volume <= vol_mult * med_vol:
        return None
    rng = last.high - last.low
    if rng <= 0:
        return None
    close_pos_val = (last.close - last.low) / rng
    if last.close > level * (1.0 + breach) and close_pos_val >= 1.0 - close_pos_pct:
        side = "buy"
    elif last.close < level * (1.0 - breach) and close_pos_val <= close_pos_pct:
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="round_number_breach",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"level": level, "grid": grid, "coil_count": near},
    )


# ── Foundry round 005 (reviews/foundry/round-005.json) ──────────────────
# Round thesis: two structural moves — every meta-gate is now a SINGLE
# scalar threshold (never the r001-r004 conjunctions that starved four
# straight samples), and three of five ideas relocate to the multi-day
# regime where the fee floor is a rounding error.
#
# Pre-mortem (reviews/foundry/premortem-005.md) verdicts: idea 1 SKIP
# (re-tests r001's already-falsified gate+weak-breakout-engine shape at
# n=460, and its maker-fee claim doesn't match a chase-style entry),
# ideas 2/3/5 IMPLEMENT (no fatal flaw found), idea 4 REDESIGN (the
# family's calibration record has never once landed a comfortable
# armed sample — every prior gate idea missed its fire-rate estimate by
# 3x-166x — and idea 4's own arithmetic carries only a 2.5x cushion,
# thinner than the smallest miss ever recorded for this family). Per
# the round policy every idea is implemented regardless of verdict so
# the gauntlet — not paper review alone — is the arbiter; idea 4 carries
# the one redesign the spec accommodates: placebo_floor widened from
# the spec's 0.30 to 0.40, loosening the gate open-rate to buy back the
# cushion the pre-mortem demanded, without touching the core single-
# scalar-gate + multi-day-engine hypothesis under test.
#
# Premise-checked 2026-07-19 against research_bars (all 5 symbols, daily
# and 5-min bars, live trades-table gate inputs excluded since they read
# the trading system's own history, not the bars table): idea 5's
# lag-1 |daily-return| autocorrelation over a rolling 21-day window
# clears persistence_min=0.25 on only 8-16% of symbol-days (BTC 12.2%,
# ETH 8.1%, SOL 16.2%, LINK 16.4%, AVAX 10.7%) versus the spec's claimed
# "~40%+" — a real miss, but the conjunction with the trend condition
# was never the bottleneck claim, so it stays implemented and the
# gauntlet gets to measure the true rate directly rather than trust the
# estimate. Ideas 2/4's weekly cross-sectional rank engine (shared
# across the basket, 7-day return, top/bottom of 5): leader qualifies
# (>10%) on 29.3% of symbol-days and trailer qualifies (<-10%) on 23.8%,
# versus the spec's assumed 55-65%/40% — over-estimated but the combined
# ~0.53 fires/day still projects to n>=490 over 930 days, comfortably
# decidable. Idea 3's weekly-uptrend gate (7d return > 8%) is true on
# 17.7% of symbol-days (spec assumed ~30%) but the pullback-touch rate
# given an uptrend is 62.5% (spec assumed ~40%, an under-estimate in the
# other direction) — the two errors partially cancel: ~0.55 fires/day
# for the basket, matching the spec's own 0.6/day arithmetic almost
# exactly. Idea 1's ungated engine (dominant-sign trend continuation)
# fires on 26.9% of BTC bars, matching the spec's ~25% estimate; its
# gate-open fraction (and idea 4's) cannot be premise-checked against
# research_bars alone — that gate reads the live trades table's
# null_baseline history, a data source this database does not carry.


def _bar_at_or_before(bars: list[BarRow], cutoff: datetime) -> BarRow | None:
    """Latest bar with timestamp <= cutoff, scanning newest-first (bars
    is chronological, oldest-first) — the round-005 multi-day ideas'
    calendar-time lookback, robust to gaps and to bar-frequency
    assumptions that hour*bars-per-hour arithmetic would get wrong."""
    for b in reversed(bars):
        if _ts(b) <= cutoff:
            return b
    return None


def _daily_closes(bars: list[BarRow]) -> list[float]:
    """One close per UTC calendar day (the day's last bar), oldest-first."""
    by_day: dict[Any, float] = {}
    for b in bars:
        by_day[_ts(b).date()] = b.close
    return [by_day[d] for d in sorted(by_day)]


def _lag1_autocorr(xs: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mu = sum(xs) / n
    den = sum((x - mu) ** 2 for x in xs)
    if den <= 0:
        return None
    num = sum((xs[i] - mu) * (xs[i + 1] - mu) for i in range(n - 1))
    return num / den


def _weekly_rank_signal(
    bars: list[BarRow], basket: dict[str, list[BarRow]],
    rank_hours: int, min_leader_return: float,
) -> tuple[str, dict[str, float]] | None:
    """Shared cross-sectional rank engine for round-005 ideas 2 and 4:
    long the basket's trailing rank_hours return leader, short the
    laggard, evaluated once per day on the 00:00 UTC bar."""
    last = bars[-1]
    if _ts(last).hour != 0:
        return None
    returns: dict[str, float] = {}
    for sym, sym_bars in basket.items():
        if not sym_bars:
            continue
        sym_last = sym_bars[-1]
        start = _bar_at_or_before(sym_bars[:-1], _ts(sym_last) - timedelta(hours=rank_hours))
        if start is None or start.close <= 0:
            continue
        returns[sym] = sym_last.close / start.close - 1.0
    if last.symbol not in returns or len(returns) < 2:
        return None
    leader = max(returns, key=returns.get)
    trailer = min(returns, key=returns.get)
    if last.symbol == leader and returns[leader] > min_leader_return:
        return "buy", returns
    if last.symbol == trailer and returns[trailer] < -min_leader_return:
        return "sell", returns
    return None


def placebo_losing_streak_single_gate_trend(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-005 idea 1 (premortem-005.md: SKIP — re-tests r001's
    already-falsified gate+weak-breakout-engine shape at n=460, and the
    fee_survival maker-fee claim doesn't match this chase-style entry.
    Implemented anyway per the round policy: the gauntlet, not the paper
    review, is the arbiter). A single scalar gate — the trailing
    null_baseline hit rate over its last placebo_window trades — arms a
    plain dominant-sign trend-continuation entry."""
    window = int(params.get("placebo_window", 20))
    floor = float(params.get("placebo_floor", 0.3))
    trend_lookback = int(params.get("trend_lookback", 12))

    state = context.get("system_state")
    if not state:
        return None
    hitrate = state.get(f"null_win_rate_{window}")
    if hitrate is None or hitrate > floor:
        return None

    if len(bars) < trend_lookback + 2:
        return None
    last, prior = bars[-1], bars[-2]
    trend_window = bars[-1 - trend_lookback: -1]
    dominant = sum((b.close - b.open) / b.open for b in trend_window if b.open > 0)
    if dominant > 0 and last.close > prior.high:
        side = "buy"
    elif dominant < 0 and last.close < prior.low:
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="placebo_gate_trend_continuation",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"placebo_hitrate": hitrate, "dominant_sign_sum": dominant},
    )


def trailing_return_rank_persistence_hold(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-005 idea 2 — cross-sectional momentum persistence: long the
    basket's 7-day-return leader, short the laggard, held for days. The
    edge lives at a horizon (weekly rebalancing flow) 5-min bots cannot
    hold through. Requires context_keys=['basket_bars']."""
    rank_hours = int(params.get("rank_lookback_hours", 168))
    min_leader_return = float(params.get("min_leader_return", 0.10))
    basket = context.get("basket_bars")
    if not basket:
        return None
    result = _weekly_rank_signal(bars, basket, rank_hours, min_leader_return)
    if result is None:
        return None
    side, returns = result
    last = bars[-1]
    return Signal(
        symbol=last.symbol, variant_name="", strategy="return_rank_persistence_hold",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"rank_return": returns[last.symbol], "basket_returns": returns},
    )


def weekly_pullback_limit_into_uptrend(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-005 idea 3 — the multi-day inversion of dead
    pullback_to_breakout_level_limit (r003, worst Sharpe ever): a
    pullback within an established WEEKLY uptrend is trend-breathing,
    not breakout-failure. Long-only: a resting limit at 3% below the
    trailing 24h high, filled only within a 7-day (>8%) uptrend and
    above the 200-bar close-mean."""
    uptrend_min = float(params.get("uptrend_min", 0.08))
    pullback_depth = float(params.get("pullback_depth", 0.03))
    limit_life_hours = int(params.get("limit_life_hours", 12))
    uptrend_lookback_hours = 168
    ma_window = 200
    pullback_high_lookback_hours = 24

    last = bars[-1]
    if len(bars) < ma_window + 1:
        return None
    trend_start = _bar_at_or_before(bars[:-1], _ts(last) - timedelta(hours=uptrend_lookback_hours))
    if trend_start is None or trend_start.close <= 0:
        return None
    weekly_return = last.close / trend_start.close - 1.0
    if weekly_return <= uptrend_min:
        return None
    ma = sum(b.close for b in bars[-ma_window - 1: -1]) / ma_window
    if last.close <= ma:
        return None

    cutoff = _ts(last) - timedelta(hours=pullback_high_lookback_hours)
    window = [b for b in bars[:-1] if _ts(b) >= cutoff]
    if not window:
        return None
    high_24h = max(b.high for b in window)
    level = high_24h * (1.0 - pullback_depth)

    limit_cutoff = _ts(last) - timedelta(hours=limit_life_hours)
    recent = [b for b in bars[:-1] if _ts(b) > limit_cutoff]
    if any(b.low <= level for b in recent):
        return None  # already touched earlier within its life — no chase
    if last.low > level:
        return None  # not touched yet
    return Signal(
        symbol=last.symbol, variant_name="", strategy="weekly_pullback_limit",
        side="buy", bar_timestamp=last.timestamp, price_at_signal=level,
        reasoning={"weekly_return": weekly_return, "level": level, "high_24h": high_24h},
    )


def placebo_streak_gated_weekly_trend_engine(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-005 idea 4 (premortem-005.md: REDESIGN — placebo_floor
    widened from the spec's 0.30 to 0.40, loosening the gate open-rate
    for the 5-10x armed-sample cushion the pre-mortem demanded over the
    family's thinnest-ever prior miss of 2.5x; the core hypothesis is
    unchanged). The single-scalar self-referential gate from idea 1
    arms the weekly cross-sectional rank engine from idea 2 — the first
    gate pairing with both a single-condition gate and a multi-day
    engine. Requires context_keys=['system_state', 'basket_bars']."""
    window = int(params.get("placebo_window", 20))
    floor = float(params.get("placebo_floor", 0.4))
    rank_hours = 168
    min_leader_return = float(params.get("gate_engine_min", 0.10))

    state = context.get("system_state")
    if not state:
        return None
    hitrate = state.get(f"null_win_rate_{window}")
    if hitrate is None or hitrate > floor:
        return None
    basket = context.get("basket_bars")
    if not basket:
        return None
    result = _weekly_rank_signal(bars, basket, rank_hours, min_leader_return)
    if result is None:
        return None
    side, returns = result
    last = bars[-1]
    return Signal(
        symbol=last.symbol, variant_name="", strategy="placebo_gated_weekly_trend",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"placebo_hitrate": hitrate, "rank_return": returns[last.symbol]},
    )


def multiday_magnitude_persistence_directional_hold(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-005 idea 5 — the fix for both prior information-theory
    deaths (r002, r004): the info signal names a REGIME, never a
    direction. Daily |return| lag-1 autocorrelation qualifies a symbol
    as a genuine volatility-clustering regime; direction comes from the
    168h trend, never from entropy/magnitude."""
    mag_w = int(params.get("mag_window", 21))
    persistence_min = float(params.get("persistence_min", 0.25))
    trend_min = float(params.get("regime_trend_min", 0.06))
    trend_lookback_hours = 168

    last = bars[-1]
    if _ts(last).hour != 0:
        return None
    closes = _daily_closes(bars)
    if len(closes) < mag_w + 2:
        return None
    daily_rets = [
        math.log(closes[i] / closes[i - 1])
        for i in range(1, len(closes))
        if closes[i - 1] > 0 and closes[i] > 0
    ]
    if len(daily_rets) < mag_w + 1:
        return None
    mags = [abs(r) for r in daily_rets[-(mag_w + 1):]]
    persistence = _lag1_autocorr(mags)
    if persistence is None or persistence < persistence_min:
        return None

    trend_start = _bar_at_or_before(bars[:-1], _ts(last) - timedelta(hours=trend_lookback_hours))
    if trend_start is None or trend_start.close <= 0:
        return None
    trend_ret = last.close / trend_start.close - 1.0
    if trend_ret > trend_min:
        side = "buy"
    elif trend_ret < -trend_min:
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="magnitude_persistence_directional_hold",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"mag_persistence": persistence, "trend_return": trend_ret},
    )


# ── Foundry round 006 (reviews/foundry/round-006.json) ──────────────────
# Round thesis: the two dead-lens reattempts (microstructure candle-geometry,
# calendar-timestamp coils) get their SKIP confirmed by the pre-mortem; the
# gate family reopens on a genuinely cross-sectional (not own-outcome)
# mechanism; cross_domain and multi_day_horizon get honest shots at open
# territory. Per round policy every idea is implemented regardless of
# verdict so the gauntlet, not paper review alone, is the arbiter.
#
# Pre-mortem (reviews/foundry/premortem-006.md) verdicts: idea 1 REDESIGN
# (re-derive the volume-monotonic-decline conditional probability against
# real data before spending a slot — the spec's own 0.25-0.35 claim is
# higher than the naive 1/6 baseline despite arguing "lower"), idea 2 SKIP
# (still pure OHLCV TR/close-position geometry — same data source as the
# 4-for-4-dead microstructure lens, wrapped in a two-phase sequence, plus
# an independent ceiling conflict), idea 3 SKIP (calendar timestamp +
# OHLCV return only, no new data source; bets on monthly-return
# continuation in the exact epoch measured at -12.4%/0-9; hedges its own
# directional sign post hoc), idea 4 REDESIGN (legitimately reopens the
# closed gate family on a real cross-sectional mechanism, but premise-check
# the joint freshest-breakout-in-sync-window frequency before trusting the
# arithmetic — it matches the shape of the two worst historical misses),
# idea 5 IMPLEMENT (correctly occupies the explicitly-open 2-week TSMOM
# band, required to beat drift not zero, least fragile base-rate math in
# the round).
#
# Premise-checked 2026-07-21 against research_bars (all 5 symbols, full
# ~2.5y history, daily/5-min bars as each idea's own resolution requires):
#
# Idea 1: direct histogram of sign(vol_day[-1]-vol_day[-2]) etc. conditioned
# on 3 consecutive daily up-closes gives P(vol monotonic decline | 3
# up-days) = 0.162 (84/519) — essentially the naive combinatorial baseline
# of 1/6=0.167, NOT the spec's claimed 0.25-0.35, confirming the
# pre-mortem's arithmetic-error finding (the direction is right — very
# slightly below baseline, consistent with a weak negative pairing — but
# the magnitude the spec assumed was never real). Full-conjunction fire
# count (3 up-days AND vol decline AND 3d gain in [2%,12%]) across the
# entire 5-symbol history: n=64 — BELOW the n>=100 decidability floor.
# Implemented unchanged per spec (no parameter rescue attempted, matching
# the r005-idea-5 precedent of letting the gauntlet measure the true rate
# rather than hand-tuning after a miss): this idea may return an
# inconclusive-starved sample, and the gauntlet write-up should say so
# plainly rather than reading a sub-100 n as a verdict either way.
#
# Idea 4: direct count of "this symbol's breakout bar is the current bar
# AND >=3-of-5 symbols broke out within the trailing 12 bars" against the
# full 5-symbol bar history: 22,118 joint-qualifying events out of 31,892
# raw breakout events (69.3% co-occurrence) — far ABOVE the spec's assumed
# 25-40% fraction, the OPPOSITE direction from the pre-mortem's fragility
# fear (the two historical 166x/186x misses under-fired; this over-fires
# if anything, because crypto breakouts are more synchronized than the
# spec's own correlation-adjusted estimate assumed). Comfortably decidable
# with no parameter change; cooldown will cut the realized rate well below
# this raw count but nowhere near the n>=100 floor.
#
# Idea 2 (SKIP, implemented anyway): raw pre-cooldown fire count ~295
# across the full basket-history (~0.068/sym/day) — decidable on count
# alone; the SKIP rests on the closed-lens/ceiling argument, not sample
# size.
#
# Idea 3 (SKIP, implemented anyway): |prior calendar-month return| > 5%
# holds on 73-80% of symbol-months (spec assumed ~70%) — comfortably
# clears n>=100; the SKIP rests on the closed-lens/regime-conflict/
# post-hoc-sign argument, not sample size. Implemented with the clean
# symmetric sign rule the spec itself states (LONG on prior return >
# +threshold, SHORT on prior return < -threshold) — the spec's own hedge
# ("test long-only if short arm degenerate") is exactly the post-hoc
# sign-fitting the pre-mortem flagged, so it is deliberately NOT carried
# into the implementation; the gauntlet gets to see both arms honestly.
#
# Idea 5: non-overlapping weekly |R14|>6% qualification rate measured at
# 47-71% per symbol (BTC 47%, ETH 63%, SOL 71%, LINK 71%, AVAX 71%) against
# the spec's assumed 55-65% — matches within the calibration scatter this
# project already expects; comfortably decidable.


def _is_last_bar_of_day(ts: datetime) -> bool:
    """True if the next 5-min bar would roll into a new UTC calendar day —
    round-006 idea 1's 'daily bucket completes' trigger, computed from the
    current bar's own timestamp so no look-ahead into bar N+1 is needed."""
    return (ts + timedelta(minutes=5)).date() != ts.date()


def _daily_close_volume(bars: list[BarRow]) -> tuple[list[float], list[float]]:
    """One (close, summed volume) pair per UTC calendar day, oldest-first.
    Only called when the current bar is a day's last bar (see
    _is_last_bar_of_day), so every day in the result is a complete day —
    never the r005-idea-5 partial-day trap of a single 00:00 bar posing as
    a full day's close/volume."""
    closes: dict[Any, float] = {}
    vols: dict[Any, float] = {}
    for b in bars:
        d = _ts(b).date()
        closes[d] = b.close
        vols[d] = vols.get(d, 0.0) + b.volume
    days = sorted(closes.keys())
    return [closes[d] for d in days], [vols[d] for d in days]


def predator_prey_volume_depletion_rebound(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-006 idea 1 (premortem-006.md: REDESIGN — premise-checked
    against research_bars; see the round-006 header comment above for the
    measured n=64, below the n>=100 floor, kept unchanged per spec).
    Ecology's predator-prey depletion trough: 3 consecutive daily up-closes
    on MONOTONICALLY DECLINING daily volume (supply exhaustion), gated to a
    2-12% cumulative 3-day gain band. Enters on the bar that completes the
    third daily bucket."""
    up_days_required = int(params.get("up_days_required", 3))
    min_gain = float(params.get("min_3d_gain", 0.02))
    max_gain = float(params.get("max_3d_gain", 0.12))

    last = bars[-1]
    if not _is_last_bar_of_day(_ts(last)):
        return None
    closes, vols = _daily_close_volume(bars)
    if len(closes) < up_days_required + 1:
        return None
    if not all(closes[-1 - k] > closes[-2 - k] for k in range(up_days_required)):
        return None
    if not all(vols[-1 - k] < vols[-2 - k] for k in range(up_days_required - 1)):
        return None
    gain = closes[-1] / closes[-1 - up_days_required] - 1.0
    if not (min_gain <= gain <= max_gain):
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="predator_prey_depletion_rebound",
        side="buy", bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"three_day_gain": gain, "daily_volumes": vols[-up_days_required:]},
    )


def range_compression_then_directional_expansion_gap(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-006 idea 2 (premortem-006.md: SKIP — still pure OHLCV TR/
    close-position geometry, the 4-for-4-dead microstructure lens's exact
    data source; implemented anyway per the round policy). Multi-bar TR
    compression (N bars below the trailing distribution's 40th percentile)
    followed by a decisive expansion bar (TR > expansion_mult * trailing
    mean) closing at its own range's extreme resolves the direction."""
    compression_bars = int(params.get("compression_bars", 6))
    tr_lookback = int(params.get("tr_lookback", 96))
    compression_pct = float(params.get("compression_pct", 0.4))
    expansion_mult = float(params.get("expansion_mult", 2.0))
    close_extreme_frac = float(params.get("close_extreme_frac", 0.2))

    n = len(bars)
    needed = tr_lookback + compression_bars + 1
    if n < needed + 1:
        return None

    def _tr_at(i: int) -> float:
        b, prev_close = bars[i], bars[i - 1].close
        return max(b.high - b.low, abs(b.high - prev_close), abs(b.low - prev_close))

    window_trs = [_tr_at(i) for i in range(n - 1 - tr_lookback, n - 1)]
    sorted_trs = sorted(window_trs)
    pct_val = sorted_trs[min(int(len(sorted_trs) * compression_pct), len(sorted_trs) - 1)]
    mean_tr = sum(window_trs) / len(window_trs)
    if not all(_tr_at(n - 2 - k) < pct_val for k in range(compression_bars)):
        return None
    if _tr_at(n - 1) <= expansion_mult * mean_tr:
        return None

    last = bars[-1]
    rng = last.high - last.low
    if rng <= 0:
        return None
    close_pos = (last.close - last.low) / rng
    if close_pos >= 1.0 - close_extreme_frac:
        side = "buy"
    elif close_pos <= close_extreme_frac:
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="tr_compression_expansion_gap",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"close_position": close_pos, "expansion_tr": _tr_at(n - 1), "mean_tr": mean_tr},
    )


def month_end_rebalance_flow_directional_persistence(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-006 idea 3 (premortem-006.md: SKIP — calendar timestamp +
    OHLCV return only, no new data source; bets on monthly continuation in
    the epoch measured at -12.4%/0-9; implemented anyway per the round
    policy, WITHOUT the spec's own post-hoc sign hedge that the pre-mortem
    flagged as curve-fitting). At UTC month-start, the prior calendar
    month's return sets a symmetric directional entry: long after a strong
    up-month, short after a strong down-month."""
    threshold = float(params.get("prior_month_return_threshold", 0.05))
    entry_window = int(params.get("entry_window_bars_after_month_start", 12))

    last = bars[-1]
    ts = _ts(last)
    month_start = ts.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    bars_since_start = int((ts - month_start).total_seconds() // 300)
    if bars_since_start < 0 or bars_since_start >= entry_window:
        return None
    prior_month_start = (month_start - timedelta(days=1)).replace(day=1)
    start_bar = _bar_at_or_before(bars, prior_month_start)
    end_bar = _bar_at_or_before(bars, month_start - timedelta(minutes=5))
    if start_bar is None or end_bar is None or start_bar.close <= 0:
        return None
    prior_return = end_bar.close / start_bar.close - 1.0
    if prior_return > threshold:
        side = "buy"
    elif prior_return < -threshold:
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="month_end_rebalance_flow",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"prior_month_return": prior_return},
    )


def constraint_rejection_pressure_release_engine(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-006 idea 4 (premortem-006.md: REDESIGN — premise-checked
    against research_bars; see the round-006 header comment above for the
    measured 69.3% co-occurrence, comfortably decidable, no parameter
    change made). Reopens the closed self-referential GATE family on a
    genuinely cross-sectional mechanism: a fresh breakout is armed only
    when >=sync_count_min of the basket broke out within the same trailing
    window — a synchronized-beta signal absent from any single symbol's
    own trade stream. Requires context_keys=['basket_bars']."""
    breakout_lookback = int(params.get("breakout_lookback", 48))
    sync_window = int(params.get("sync_window_bars", 12))
    sync_count_min = int(params.get("sync_count_min", 3))

    last = bars[-1]
    if len(bars) < breakout_lookback + 1:
        return None
    prior_high = max(b.high for b in bars[-1 - breakout_lookback: -1])
    if last.close <= prior_high:
        return None  # this symbol's own breakout isn't fresh on the current bar

    basket = context.get("basket_bars")
    if not basket:
        return None

    def _recent_breakout(sym_bars: list[BarRow]) -> bool:
        n = len(sym_bars)
        lo = max(breakout_lookback, n - sync_window)
        for i in range(lo, n):
            window = sym_bars[i - breakout_lookback: i]
            if window and sym_bars[i].close > max(b.high for b in window):
                return True
        return False

    sync_count = sum(1 for sym_bars in basket.values() if sym_bars and _recent_breakout(sym_bars))
    if sync_count < sync_count_min:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="constraint_rejection_pressure_release",
        side="buy", bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"sync_count": sync_count, "prior_high": prior_high},
    )


def multiweek_directional_regime_persistence_hold(
    bars: list[BarRow], params: dict[str, Any], context: dict[str, Any]
) -> Signal | None:
    """Round-006 idea 5 (premortem-006.md: IMPLEMENT — no fatal flaw
    found; the round's mandated continuation canary). Symmetric long/short
    on the trailing 14-day return sign, evaluated once per symbol per UTC
    week (Monday 00:00) and held 7 days — occupies the 2-week TSMOM band
    the archive explicitly flagged OPEN, distinct from the reverting
    monthly scale. A sign-flip in its own results IS the regime-flip
    alarm, not just a failure."""
    threshold = float(params.get("threshold", 0.06))
    lookback_hours = 336  # 14 days

    last = bars[-1]
    ts = _ts(last)
    if ts.weekday() != 0 or ts.hour != 0 or ts.minute != 0:
        return None
    start = _bar_at_or_before(bars[:-1], ts - timedelta(hours=lookback_hours))
    if start is None or start.close <= 0:
        return None
    r14 = last.close / start.close - 1.0
    if r14 > threshold:
        side = "buy"
    elif r14 < -threshold:
        side = "sell"
    else:
        return None
    return Signal(
        symbol=last.symbol, variant_name="", strategy="multiweek_directional_regime_hold",
        side=side, bar_timestamp=last.timestamp, price_at_signal=last.close,
        reasoning={"r14_return": r14},
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
    "cond_entropy_expansion": conditional_entropy_regime_expansion,
    "r0_ignition": epidemic_r0_crossover_ignition,
    "absorption_shelf": absorption_shelf_breakout,
    "expiry_pin_release": options_expiry_pin_release,
    "rejection_gated_ignition": rejection_streak_gated_ignition,
    "gap_exhaustion": gap_fill_exhaustion_continuation,
    "asian_london_handoff": asian_to_london_handoff_thrust,
    "slot_scarcity_gate": slot_scarcity_conviction_gate,
    "post_shock_drift": post_shock_multiday_drift,
    "breakout_retest_limit": pullback_to_breakout_level_limit,
    "trend_persistence_gated": trend_persistence_regime_gated_engine,
    "magnitude_surprise_break": return_magnitude_compressibility_break,
    "hawkes_intensity_entry": hawkes_self_excitation_intensity_entry,
    "one_sided_expansion_thrust": one_sided_range_expansion_thrust,
    "round_number_breach": round_number_breach_continuation,
    "placebo_gate_trend_continuation": placebo_losing_streak_single_gate_trend,
    "return_rank_persistence_hold": trailing_return_rank_persistence_hold,
    "weekly_pullback_limit": weekly_pullback_limit_into_uptrend,
    "placebo_gated_weekly_trend": placebo_streak_gated_weekly_trend_engine,
    "magnitude_persistence_directional_hold": multiday_magnitude_persistence_directional_hold,
    "predator_prey_depletion_rebound": predator_prey_volume_depletion_rebound,
    "tr_compression_expansion_gap": range_compression_then_directional_expansion_gap,
    "month_end_rebalance_flow": month_end_rebalance_flow_directional_persistence,
    "constraint_rejection_pressure_release": constraint_rejection_pressure_release_engine,
    "multiweek_directional_regime_hold": multiweek_directional_regime_persistence_hold,
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
    # Round-002 gate inputs: the constraint layer's own recent behavior.
    dec = conn.execute(
        """
        SELECT action FROM decisions ORDER BY decided_at DESC LIMIT 50
        """
    ).fetchall()
    rejection_rate = (
        sum(1 for d in dec if d["action"] == "rejected") / len(dec) if dec else None
    )
    nulls = conn.execute(
        """
        SELECT exit_reason FROM trades
         WHERE variant_name = 'null_baseline' AND status = 'closed'
         ORDER BY exit_time DESC LIMIT 10
        """
    ).fetchall()
    placebo_stop_rate = (
        sum(1 for r in nulls if r["exit_reason"] == "stop_loss") / len(nulls)
        if nulls else None
    )
    all_recent = conn.execute(
        """
        SELECT exit_reason FROM trades WHERE status = 'closed'
         ORDER BY exit_time DESC LIMIT 10
        """
    ).fetchall()
    stop_out_rate = (
        sum(1 for r in all_recent if r["exit_reason"] == "stop_loss") / len(all_recent)
        if all_recent else None
    )
    # Round-004 idea 1 gate inputs: count-based (not time-windowed) so the
    # gate stays informative even across the 24h lookback boundary.
    null_100 = conn.execute(
        """
        SELECT pnl_usd, exit_reason, exit_time FROM trades
         WHERE variant_name = 'null_baseline' AND status = 'closed'
         ORDER BY exit_time DESC LIMIT 100
        """
    ).fetchall()
    last_20 = conn.execute(
        """
        SELECT exit_reason, exit_time FROM trades
         WHERE status = 'closed' ORDER BY exit_time DESC LIMIT 20
        """
    ).fetchall()
    # Round-005 ideas 1/4 gate inputs: the trailing placebo hit rate over
    # the last N null_baseline closed trades (a single scalar, not the
    # r001-r004 conjunctive gates) — one query per idea's declared window.
    null_20 = conn.execute(
        """
        SELECT pnl_usd, exit_reason, exit_time FROM trades
         WHERE variant_name = 'null_baseline' AND status = 'closed'
         ORDER BY exit_time DESC LIMIT 20
        """
    ).fetchall()
    null_40 = conn.execute(
        """
        SELECT pnl_usd, exit_reason, exit_time FROM trades
         WHERE variant_name = 'null_baseline' AND status = 'closed'
         ORDER BY exit_time DESC LIMIT 40
        """
    ).fetchall()
    return {
        "null_win_rate": (wins / closed) if closed else None,
        "recent_stopouts": stopouts,
        "rejection_rate": rejection_rate,
        "placebo_stop_rate": placebo_stop_rate,
        "stop_out_rate": stop_out_rate,  # last 10 closed, ALL arms (r003)
        "null_win_rate_100": _closed_trade_win_rate(null_100),
        "stopout_cluster_index": _stopout_cluster_index(last_20),
        "null_win_rate_20": _closed_trade_win_rate(null_20),
        "null_win_rate_40": _closed_trade_win_rate(null_40),
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
    force: bool = False,
) -> list[Signal]:
    """Run a single variant across all symbols, persist any emitted signals.

    force=True runs a DISABLED variant (shadow mode): its signals are
    persisted for forward-test evidence but execute.process_pending
    refuses to trade them — see the shadow-arm guard there."""
    if not variant.get("enabled", False) and not force:
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
    # Round-005 ideas 2/4's cross-sectional rank engine needs every
    # basket symbol's own bars, not just the symbol currently being
    # evaluated — 2200 bars (~7.6 days of 5-min bars) comfortably covers
    # the 168h rank lookback plus the prior-bar buffer it needs.
    if "basket_bars" in variant.get("context_keys", []) and "basket_bars" not in ctx:
        ctx["basket_bars"] = {s: load_recent_bars(conn, s, limit=2200) for s in symbols}

    emitted: list[Signal] = []
    bar_limit = max(400, int(params.get("window_bars", 0)))
    for symbol in symbols:
        bars = load_recent_bars(conn, symbol, limit=bar_limit)
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
    include_shadow: bool = False,
) -> list[Signal]:
    """Iterate every enabled variant in the registry, emit signals.

    include_shadow=True (the live cycle) ALSO runs every disabled
    variant in shadow mode: signals are computed and persisted but
    never traded (execute refuses disabled variants). Live time is the
    scarcest resource in the project — shadow arms turn the one live
    stream into forward-test evidence for the WHOLE research roster:
    real fire rates, sim-to-live calibration, and out-of-sample
    outcomes for every idea ever built, at zero capital risk
    (learning-quality audit 2026-07-18).
    """
    registry = variants if variants is not None else STRATEGY_VARIANTS
    all_signals: list[Signal] = []
    with db.connect(db_path) as conn:
        for name, variant in registry.items():
            shadow = not variant.get("enabled", False)
            if shadow and not include_shadow:
                continue
            try:
                sigs = run_variant(conn, name, variant, symbols,
                                   context=context, force=shadow)
            except KeyError:
                raise  # unknown strategy is a config error — keep loud
            except Exception as exc:
                # One misbehaving variant must not silence the rest
                # (audit 2026-07-17); strategies should return None, not
                # raise, but a poisoned bar must never kill the cycle.
                print(f"ERROR variant {name}: {type(exc).__name__}: {exc}")
                continue
            all_signals.extend(sigs)
    return all_signals
