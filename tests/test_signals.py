"""Tests for signals.py skeleton against an empty registry."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
import fetch
import signals
from config import StrategyVariant
from signals import BarRow, Signal, bollinger_strategy, macross_strategy, run_all_variants
from tests.fixtures.bars import FakeBarSource, make_bar_series


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


@pytest.fixture
def populated_bars_db(tmp_db: Path) -> Path:
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    btc = make_bar_series("BTC/USD", start, n=12, base_price=60000.0)
    source = FakeBarSource(bars=btc)
    fetch.fetch_window(source, ["BTC/USD"], start, start + timedelta(minutes=60), db_path=tmp_db)
    return tmp_db


def test_empty_registry_emits_zero_signals(populated_bars_db: Path) -> None:
    sigs = run_all_variants(
        symbols=["BTC/USD"], variants={}, db_path=populated_bars_db
    )
    assert sigs == []
    with db.connect(populated_bars_db) as conn:
        n = conn.execute("SELECT COUNT(*) AS c FROM signals").fetchone()["c"]
    assert n == 0


def test_registry_null_baseline_is_the_only_live_variant() -> None:
    from config import STRATEGY_VARIANTS
    retired = {
        "bollinger_default", "macross_default",
        "bollinger_tight", "bollinger_loose", "bollinger_long",
        "bollinger_quick", "bollinger_verytight",
        "macross_fast", "macross_slow", "macross_veryfast",
        "macross_veryslow", "macross_balanced",
    }
    candidates = {
        "liquidation_cascade_reclaim", "btc_leads_alt_lag_capture",
        "dead_zone_range_break", "volume_thrust_regime_shift",
        "weekend_illiquidity_momentum",
    }
    foundry_001 = {
        "entropy_collapse_impulse", "omori_aftershock_ladder",
        "failed_auction_rejection_wick", "round_number_overshoot_snap",
        "drawdown_regime_contrarian_gate",
    }
    foundry_002 = {
        "conditional_entropy_regime_expansion", "epidemic_r0_crossover_ignition",
        "absorption_shelf_breakout", "options_expiry_pin_release",
        "rejection_streak_gated_ignition",
    }
    foundry_003 = {
        "gap_fill_exhaustion_continuation", "asian_to_london_handoff_thrust",
        "slot_scarcity_conviction_gate", "post_shock_multiday_drift",
        "pullback_to_breakout_level_limit",
    }
    assert set(STRATEGY_VARIANTS.keys()) == (
        retired | candidates | foundry_001 | foundry_002 | foundry_003
        | {"null_baseline"}
    )
    assert all(
        STRATEGY_VARIANTS[n].get("enabled") is False
        for n in foundry_001 | foundry_002 | foundry_003
    ), "foundry rounds stay disabled pending their gauntlets"

    # The live roster: null placebo + the gauntlet's top 2 as A/B arms
    # (reports/gauntlet-2026-07-16.md; decision-log 2026-07-16). Not a
    # strategy zoo: exactly 3 live.
    live = {n for n, v in STRATEGY_VARIANTS.items() if v.get("enabled")}
    assert live == {
        "null_baseline", "weekend_illiquidity_momentum", "volume_thrust_regime_shift",
    }

    assert STRATEGY_VARIANTS["null_baseline"]["enabled"] is True, (
        "the placebo arm is permanent (phase1-review.md § 5 term 1)"
    )
    assert STRATEGY_VARIANTS["null_baseline"]["strategy"] == "null"
    assert all(
        STRATEGY_VARIANTS[name].get("enabled") is False for name in retired
    ), (
        "all 12 backtest variants stay disabled — retired per decision-log "
        "2026-07-02 roster call; entries kept only for replay reproducibility"
    )
    assert STRATEGY_VARIANTS["bollinger_default"]["params"] == {
        "period": 20, "stddev": 2.0, "tp": 0.05, "sl": 0.03, "time_exit_hours": 24,
    }


def test_run_variant_with_disabled_variant_skips(populated_bars_db: Path) -> None:
    disabled: dict[str, StrategyVariant] = {
        "fake_strategy": {
            "strategy": "noop",
            "params": {},
            "context_keys": [],
            "enabled": False,
            "phase_qualified": False,
        }
    }
    sigs = run_all_variants(
        symbols=["BTC/USD"], variants=disabled, db_path=populated_bars_db
    )
    assert sigs == []


def test_run_variant_with_unknown_strategy_raises(populated_bars_db: Path) -> None:
    bad: dict[str, StrategyVariant] = {
        "broken": {
            "strategy": "does_not_exist",
            "params": {},
            "context_keys": [],
            "enabled": True,
            "phase_qualified": False,
        }
    }
    with pytest.raises(KeyError, match="not registered"):
        run_all_variants(
            symbols=["BTC/USD"], variants=bad, db_path=populated_bars_db
        )


def test_signal_persistence(populated_bars_db: Path) -> None:
    """Sanity-check the persistence path with a hand-rolled strategy."""
    def trivial_buy(bars: list[BarRow], params: dict, context: dict) -> Signal | None:
        last = bars[-1]
        return Signal(
            symbol=last.symbol,
            variant_name="",
            strategy="trivial",
            side="buy",
            bar_timestamp=last.timestamp,
            price_at_signal=last.close,
            reasoning={"reason": "always buy on the last bar"},
        )

    signals.STRATEGY_REGISTRY["trivial"] = trivial_buy
    try:
        variants: dict[str, StrategyVariant] = {
            "trivial_default": {
                "strategy": "trivial",
                "params": {},
                "context_keys": [],
                "enabled": True,
                "phase_qualified": False,
            }
        }
        sigs = run_all_variants(
            symbols=["BTC/USD"], variants=variants, db_path=populated_bars_db
        )
        assert len(sigs) == 1
        with db.connect(populated_bars_db) as conn:
            row = conn.execute(
                "SELECT * FROM signals WHERE variant_name = ?", ("trivial_default",)
            ).fetchone()
        assert row is not None
        assert row["strategy"] == "trivial"
        assert row["side"] == "buy"
        assert "reason" in row["reasoning_json"]
    finally:
        del signals.STRATEGY_REGISTRY["trivial"]


def test_load_recent_bars_chronological_order(populated_bars_db: Path) -> None:
    with db.connect(populated_bars_db) as conn:
        bars = signals.load_recent_bars(conn, "BTC/USD", limit=12)
    timestamps = [b.timestamp for b in bars]
    assert timestamps == sorted(timestamps), "bars must be returned in ascending time order"


def _bars_from_closes(closes: list[float]) -> list[BarRow]:
    base = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    return [
        BarRow(
            symbol="BTC/USD",
            timestamp=(base + timedelta(minutes=5 * i)).isoformat(),
            open=c, high=c, low=c, close=c, volume=1.0,
        )
        for i, c in enumerate(closes)
    ]


class TestBollingerStrategy:
    def test_insufficient_bars_returns_none(self) -> None:
        bars = _bars_from_closes([10.0, 12.0])
        assert bollinger_strategy(bars, {"period": 3, "stddev": 1.0}, {}) is None

    def test_oversold_close_at_lower_band_buys(self) -> None:
        # mean=12, pstdev=sqrt(8/3)=1.633 -> lower=10.367; close=10 <= lower
        bars = _bars_from_closes([14.0, 12.0, 10.0])
        sig = bollinger_strategy(bars, {"period": 3, "stddev": 1.0}, {})
        assert sig is not None
        assert sig.side == "buy"
        assert sig.strategy == "bollinger"
        assert sig.price_at_signal == 10.0

    def test_overbought_close_at_upper_band_sells(self) -> None:
        # mean=12, pstdev=1.633 -> upper=13.633; close=14 >= upper
        bars = _bars_from_closes([10.0, 12.0, 14.0])
        sig = bollinger_strategy(bars, {"period": 3, "stddev": 1.0}, {})
        assert sig is not None
        assert sig.side == "sell"

    def test_close_inside_bands_emits_nothing(self) -> None:
        # mean=11, pstdev=0.8165 -> band [10.18, 11.82]; close=11 is inside
        bars = _bars_from_closes([10.0, 12.0, 11.0])
        assert bollinger_strategy(bars, {"period": 3, "stddev": 1.0}, {}) is None

    def test_default_params_used_when_missing(self) -> None:
        bars = _bars_from_closes([100.0 + i for i in range(20)])
        sig = bollinger_strategy(bars, {}, {})
        assert sig is None or sig.reasoning["period"] == 20


class TestMacrossStrategy:
    def test_fast_must_be_less_than_slow(self) -> None:
        # invalid config returns None rather than killing the cycle
        bars = _bars_from_closes([10.0] * 30)
        assert macross_strategy(bars, {"fast": 26, "slow": 12}, {}) is None

    def test_insufficient_bars_returns_none(self) -> None:
        bars = _bars_from_closes([10.0, 10.0, 10.0])  # need slow+1=4
        assert macross_strategy(bars, {"fast": 2, "slow": 3}, {}) is None

    def test_golden_cross_buys(self) -> None:
        bars = _bars_from_closes([10.0, 10.0, 10.0, 20.0])
        sig = macross_strategy(bars, {"fast": 2, "slow": 3}, {})
        assert sig is not None
        assert sig.side == "buy"
        assert sig.strategy == "macross"

    def test_death_cross_sells(self) -> None:
        bars = _bars_from_closes([10.0, 10.0, 10.0, 0.0])
        sig = macross_strategy(bars, {"fast": 2, "slow": 3}, {})
        assert sig is not None
        assert sig.side == "sell"

    def test_flat_prices_emit_nothing(self) -> None:
        bars = _bars_from_closes([10.0, 10.0, 10.0, 10.0])
        assert macross_strategy(bars, {"fast": 2, "slow": 3}, {}) is None

    def test_registered_in_strategy_registry(self) -> None:
        assert signals.STRATEGY_REGISTRY["bollinger"] is bollinger_strategy
        assert signals.STRATEGY_REGISTRY["macross"] is macross_strategy
        assert signals.STRATEGY_REGISTRY["null"] is signals.null_strategy


class TestNullStrategy:
    def _bar(self, symbol: str, ts: str) -> BarRow:
        return BarRow(symbol=symbol, timestamp=ts, open=100.0, high=100.0,
                      low=100.0, close=100.0, volume=1.0)

    def test_deterministic_per_bar(self) -> None:
        bars = [self._bar("BTC/USD", "2026-07-16T00:00:00+00:00")]
        results = [signals.null_strategy(bars, {"p": 0.5}, {}) for _ in range(5)]
        first = results[0]
        for r in results[1:]:
            if first is None:
                assert r is None
            else:
                assert r is not None and r.side == first.side

    def test_fire_rate_approximates_p(self) -> None:
        fired = 0
        for i in range(1000):
            bars = [self._bar("BTC/USD", f"2026-07-16T{i//60:02d}:{i%60:02d}:00+00:00")]
            if signals.null_strategy(bars, {"p": 0.10}, {}) is not None:
                fired += 1
        assert 60 <= fired <= 145, f"~10% expected over 1000 bars, got {fired}"

    def test_both_sides_occur(self) -> None:
        sides = set()
        for i in range(500):
            bars = [self._bar("ETH/USD", f"2026-07-{(i%28)+1:02d}T{i//60:02d}:{i%60:02d}:00+00:00")]
            sig = signals.null_strategy(bars, {"p": 1.0}, {})
            assert sig is not None  # p=1.0 always fires
            sides.add(sig.side)
        assert sides == {"buy", "sell"}

    def test_p_zero_never_fires(self) -> None:
        for i in range(100):
            bars = [self._bar("SOL/USD", f"2026-07-16T00:{i%60:02d}:00+00:00")]
            assert signals.null_strategy(bars, {"p": 0.0}, {}) is None

    def test_empty_bars_returns_none(self) -> None:
        assert signals.null_strategy([], {"p": 1.0}, {}) is None


# --- LLM-surfaced candidates (reviews/candidates-2026-07-16.md) ---------------


def _bar(symbol: str, ts: str, o: float, h: float, l: float, c: float, v: float) -> BarRow:
    return BarRow(symbol=symbol, timestamp=ts, open=o, high=h, low=l, close=c, volume=v)


def _flat_series(symbol: str, n: int, price: float = 100.0, vol: float = 100.0,
                 start_iso: str = "2026-07-13T00:00:00+00:00") -> list[BarRow]:
    from datetime import datetime, timedelta
    start = datetime.fromisoformat(start_iso)
    out = []
    for i in range(n):
        ts = (start + timedelta(minutes=5 * i)).isoformat()
        out.append(_bar(symbol, ts, price, price + 0.01, price - 0.01, price, vol))
    return out


class TestCascadeReclaim:
    def _setup(self, reclaim_close: float, last_vol: float = 200.0) -> list[BarRow]:
        bars = _flat_series("BTC/USD", 300)
        # inject mild noise so sigma > 0 but small
        for i in range(50, 250):
            b = bars[i]
            bars[i] = _bar(b.symbol, b.timestamp, 100.0, 100.06, 99.94,
                           100.0 + (0.03 if i % 2 else -0.03), 100.0)
        # cascade bar at -3: huge red bar, wide range
        b = bars[-3]
        bars[-3] = _bar(b.symbol, b.timestamp, 100.0, 100.5, 89.0, 90.0, 400.0)
        # pre-cascade bar high defines the reclaim level (~100.01)
        b = bars[-2]
        bars[-2] = _bar(b.symbol, b.timestamp, 90.0, 95.0, 89.5, 94.0, 150.0)
        b = bars[-1]
        bars[-1] = _bar(b.symbol, b.timestamp, 94.0, reclaim_close + 0.5,
                        93.5, reclaim_close, last_vol)
        return bars

    def test_fires_on_confirmed_reclaim(self) -> None:
        bars = self._setup(reclaim_close=101.0)
        sig = signals.liquidation_cascade_reclaim(bars, {}, {})
        assert sig is not None and sig.side == "buy"

    def test_silent_without_reclaim(self) -> None:
        bars = self._setup(reclaim_close=95.0)  # never reclaims pre-spike high
        assert signals.liquidation_cascade_reclaim(bars, {}, {}) is None

    def test_silent_without_volume(self) -> None:
        bars = self._setup(reclaim_close=101.0, last_vol=50.0)
        assert signals.liquidation_cascade_reclaim(bars, {}, {}) is None

    def test_silent_on_calm_series(self) -> None:
        assert signals.liquidation_cascade_reclaim(_flat_series("BTC/USD", 300), {}, {}) is None


class TestBtcLag:
    def _alt_and_btc(self, btc_jump: float, alt_jump: float, alt_vol: float = 200.0):
        alt = _flat_series("SOL/USD", 40, price=100.0)
        btc = _flat_series("BTC/USD", 40, price=60000.0)
        # BTC impulses over last 3 bars to a 6-bar closing high
        for k, mult in ((4, 1.0), (3, 1.004), (2, 1.008), (1, 1.0 + btc_jump)):
            b = btc[-k]
            px = 60000.0 * mult
            btc[-k] = _bar(b.symbol, b.timestamp, px, px + 5, px - 5, px, 100.0)
        a = alt[-1]
        alt_px = 100.0 * (1.0 + alt_jump)
        alt[-1] = _bar(a.symbol, a.timestamp, alt_px, alt_px + 0.1, alt_px - 0.1, alt_px, alt_vol)
        return alt, btc

    def test_fires_when_alt_lags_btc_impulse(self) -> None:
        alt, btc = self._alt_and_btc(btc_jump=0.015, alt_jump=0.002)
        sig = signals.btc_leads_alt_lag_capture(alt, {}, {"btc_bars": btc})
        assert sig is not None and sig.side == "buy"

    def test_silent_when_alt_already_moved(self) -> None:
        alt, btc = self._alt_and_btc(btc_jump=0.015, alt_jump=0.012)
        assert signals.btc_leads_alt_lag_capture(alt, {}, {"btc_bars": btc}) is None

    def test_silent_without_btc_context(self) -> None:
        alt, _ = self._alt_and_btc(btc_jump=0.015, alt_jump=0.002)
        assert signals.btc_leads_alt_lag_capture(alt, {}, {}) is None

    def test_silent_for_non_alt_symbols(self) -> None:
        alt, btc = self._alt_and_btc(btc_jump=0.015, alt_jump=0.002)
        eth = [_bar("ETH/USD", b.timestamp, b.open, b.high, b.low, b.close, b.volume) for b in alt]
        assert signals.btc_leads_alt_lag_capture(eth, {}, {"btc_bars": btc}) is None

    def test_no_lookahead_into_btc_future(self) -> None:
        alt, btc = self._alt_and_btc(btc_jump=0.015, alt_jump=0.002)
        # BTC bars strictly after the alt's latest timestamp must be ignored:
        from datetime import datetime, timedelta
        future_ts = (datetime.fromisoformat(alt[-1].timestamp) + timedelta(minutes=5)).isoformat()
        crazy = _bar("BTC/USD", future_ts, 90000.0, 90001.0, 89999.0, 90000.0, 100.0)
        sig_with = signals.btc_leads_alt_lag_capture(alt, {}, {"btc_bars": btc})
        sig_with_future = signals.btc_leads_alt_lag_capture(alt, {}, {"btc_bars": btc + [crazy]})
        assert (sig_with is None) == (sig_with_future is None)


class TestDeadzoneBreak:
    def _session(self, coil_pct: float = 0.01, break_close: float | None = None,
                 break_vol: float = 300.0):
        # bars from 00:00 to 08:00 UTC same day + enough history before
        from datetime import datetime, timedelta
        start = datetime.fromisoformat("2026-07-13T00:00:00+00:00") - timedelta(hours=24)
        bars = []
        i = 0
        t = start
        while t < datetime.fromisoformat("2026-07-14T08:05:00+00:00"):
            hour = t.hour
            day = t.date().isoformat()
            if day == "2026-07-14" and 0 <= hour < 6:
                lo, hi = 100.0, 100.0 * (1 + coil_pct)
                px = (lo + hi) / 2
                bars.append(_bar("ETH/USD", t.isoformat(), px, hi, lo, px, 40.0))  # thin
            else:
                bars.append(_bar("ETH/USD", t.isoformat(), 100.0, 100.4, 99.6, 100.0, 100.0))
            t += timedelta(minutes=5)
            i += 1
        if break_close is not None:
            last = bars[-1]
            bars[-1] = _bar("ETH/USD", last.timestamp, 100.0, break_close + 0.2,
                            99.9, break_close, break_vol)
        return bars

    def test_fires_on_clean_session_break(self) -> None:
        bars = self._session(coil_pct=0.01, break_close=102.0)
        sig = signals.dead_zone_range_break(bars, {}, {})
        assert sig is not None and sig.side == "buy"

    def test_silent_when_coil_too_wide(self) -> None:
        bars = self._session(coil_pct=0.03, break_close=104.0)
        assert signals.dead_zone_range_break(bars, {}, {}) is None

    def test_silent_without_volume_expansion(self) -> None:
        bars = self._session(coil_pct=0.01, break_close=102.0, break_vol=50.0)
        assert signals.dead_zone_range_break(bars, {}, {}) is None

    def test_silent_outside_session_window(self) -> None:
        bars = self._session(coil_pct=0.01, break_close=102.0)
        # shift everything +12h so the latest bar lands ~20:00 UTC
        from datetime import datetime, timedelta
        shifted = [
            _bar(b.symbol,
                 (datetime.fromisoformat(b.timestamp) + timedelta(hours=12)).isoformat(),
                 b.open, b.high, b.low, b.close, b.volume)
            for b in bars
        ]
        assert signals.dead_zone_range_break(shifted, {}, {}) is None


class TestVolThrust:
    def _setup(self, confirm_close: float, thrust_vol: float = 600.0):
        bars = _flat_series("LINK/USD", 300, price=100.0, vol=100.0)
        # natural volume noise so the z-score denominator is realistic
        for i in range(len(bars)):
            b = bars[i]
            bars[i] = _bar(b.symbol, b.timestamp, b.open, b.high, b.low, b.close,
                           100.0 + (i % 20))
        # rising drift so close > vwap at the end
        for i in range(250, 298):
            b = bars[i]
            px = 100.0 + (i - 250) * 0.02
            bars[i] = _bar(b.symbol, b.timestamp, px, px + 0.05, px - 0.05, px + 0.02,
                           100.0 + (i % 20))
        # thrust bar at -2: big volume, up body >= 0.8%
        b = bars[-2]
        bars[-2] = _bar(b.symbol, b.timestamp, 101.0, 102.2, 100.9, 102.0, thrust_vol)
        b = bars[-1]
        bars[-1] = _bar(b.symbol, b.timestamp, 102.0, confirm_close + 0.1,
                        101.8, confirm_close, 150.0)
        return bars

    def test_fires_on_confirmed_thrust(self) -> None:
        sig = signals.volume_thrust_regime_shift(self._setup(confirm_close=102.4), {}, {})
        assert sig is not None and sig.side == "buy"

    def test_silent_when_confirmation_rejects(self) -> None:
        assert signals.volume_thrust_regime_shift(self._setup(confirm_close=101.5), {}, {}) is None

    def test_silent_without_thrust_volume(self) -> None:
        assert signals.volume_thrust_regime_shift(
            self._setup(confirm_close=102.4, thrust_vol=120.0), {}, {}
        ) is None


class TestWeekendMomentum:
    def _setup(self, start_iso: str, mom: float = 0.02):
        # 2026-07-18 is a Saturday
        bars = _flat_series("AVAX/USD", 90, price=100.0, start_iso=start_iso)
        # strong steady climb over the last 13 bars, green persistence
        for k in range(13, 0, -1):
            i = len(bars) - k
            b = bars[i]
            px = 100.0 * (1 + mom * (13 - k) / 12)
            bars[i] = _bar(b.symbol, b.timestamp, px - 0.05, px + 0.05, px - 0.1, px, 100.0)
        return bars

    def test_fires_on_weekend_momentum(self) -> None:
        bars = self._setup("2026-07-18T00:00:00+00:00", mom=0.02)
        sig = signals.weekend_illiquidity_momentum(bars, {}, {})
        assert sig is not None and sig.side == "buy"

    def test_silent_on_weekday(self) -> None:
        bars = self._setup("2026-07-13T00:00:00+00:00", mom=0.02)  # Monday
        assert signals.weekend_illiquidity_momentum(bars, {}, {}) is None

    def test_silent_below_momentum_threshold(self) -> None:
        bars = self._setup("2026-07-18T00:00:00+00:00", mom=0.005)
        assert signals.weekend_illiquidity_momentum(bars, {}, {}) is None


def test_all_candidates_registered() -> None:
    for key in ("cascade_reclaim", "btc_lag", "deadzone_break", "vol_thrust", "weekend_momentum"):
        assert key in signals.STRATEGY_REGISTRY


# --- Foundry round 001 (smoke + gate tests) ----------------------------------


class TestFoundryRound001:
    def test_all_registered(self) -> None:
        for key in ("entropy_impulse", "omori_aftershock", "auction_wick",
                    "round_number_snap", "regime_gate_breakout"):
            assert key in signals.STRATEGY_REGISTRY

    def test_insufficient_bars_all_return_none(self) -> None:
        bars = _flat_series("BTC/USD", 30)
        ctx = {"system_state": {"null_win_rate": 0.2, "recent_stopouts": 0}}
        assert signals.entropy_collapse_impulse(bars, {}, {}) is None
        assert signals.omori_aftershock_ladder(bars, {}, {}) is None
        assert signals.failed_auction_rejection_wick(bars, {}, {}) is None
        assert signals.round_number_overshoot_snap(bars, {}, {}) is None
        assert signals.drawdown_regime_contrarian_gate(bars, {}, ctx) is None

    def test_flat_series_no_fires(self) -> None:
        bars = _flat_series("ETH/USD", 500)
        ctx = {"system_state": {"null_win_rate": 0.2, "recent_stopouts": 0}}
        assert signals.entropy_collapse_impulse(bars, {}, {}) is None
        assert signals.omori_aftershock_ladder(bars, {}, {}) is None
        assert signals.failed_auction_rejection_wick(bars, {}, {}) is None
        assert signals.round_number_overshoot_snap(bars, {}, {}) is None
        assert signals.drawdown_regime_contrarian_gate(bars, {}, ctx) is None

    def _breakout_bars(self) -> list[BarRow]:
        bars = _flat_series("SOL/USD", 100, price=100.0, vol=100.0)
        last = bars[-1]
        bars[-1] = _bar(last.symbol, last.timestamp, 100.0, 103.2, 99.9, 103.0, 300.0)
        return bars

    def test_regime_gate_fires_only_when_gate_open(self) -> None:
        bars = self._breakout_bars()
        open_gate = {"system_state": {"null_win_rate": 0.20, "recent_stopouts": 0}}
        sig = signals.drawdown_regime_contrarian_gate(bars, {}, open_gate)
        assert sig is not None and sig.side == "buy"

    def test_regime_gate_suppressed_when_null_winning(self) -> None:
        bars = self._breakout_bars()
        shut = {"system_state": {"null_win_rate": 0.50, "recent_stopouts": 0}}
        assert signals.drawdown_regime_contrarian_gate(bars, {}, shut) is None

    def test_regime_gate_suppressed_in_drawdown_cluster(self) -> None:
        bars = self._breakout_bars()
        shut = {"system_state": {"null_win_rate": 0.20, "recent_stopouts": 3}}
        assert signals.drawdown_regime_contrarian_gate(bars, {}, shut) is None

    def test_regime_gate_none_without_context(self) -> None:
        assert signals.drawdown_regime_contrarian_gate(self._breakout_bars(), {}, {}) is None

    def test_round_number_snap_up_spike_rejected(self) -> None:
        # SOL grid = $10. Spike through 110 to 110.6 (0.55% overshoot), close back at 109.5
        bars = _flat_series("SOL/USD", 100, price=108.0, vol=100.0)
        last = bars[-1]
        bars[-1] = _bar(last.symbol, last.timestamp, 109.0, 110.6, 108.9, 109.5, 300.0)
        sig = signals.round_number_overshoot_snap(bars, {}, {})
        assert sig is not None and sig.side == "sell"

    def test_round_number_snap_needs_fresh_level(self) -> None:
        bars = _flat_series("SOL/USD", 100, price=108.0, vol=100.0)
        # a prior bar already straddles 110 → level not fresh
        b = bars[-10]
        bars[-10] = _bar(b.symbol, b.timestamp, 109.9, 110.2, 109.8, 109.9, 100.0)
        last = bars[-1]
        bars[-1] = _bar(last.symbol, last.timestamp, 109.0, 110.6, 108.9, 109.5, 300.0)
        assert signals.round_number_overshoot_snap(bars, {}, {}) is None

    def test_auction_wick_short_on_rejected_fresh_high(self) -> None:
        bars = _flat_series("LINK/USD", 100, price=100.0, vol=100.0)
        last = bars[-1]
        # fresh high 103, huge upper wick, close back INSIDE the prior
        # range (prior high ~100.01)
        bars[-1] = _bar(last.symbol, last.timestamp, 100.05, 103.0, 99.95, 100.0, 300.0)
        sig = signals.failed_auction_rejection_wick(bars, {}, {})
        assert sig is not None and sig.side == "sell"

    def test_omori_continuation_fires(self) -> None:
        bars = _flat_series("AVAX/USD", 200, price=100.0, vol=100.0)
        # gentle noise so sigma is small but nonzero
        for i in range(50, 190):
            b = bars[i]
            px = 100.0 + (0.02 if i % 2 else -0.02)
            bars[i] = _bar(b.symbol, b.timestamp, 100.0, px + 0.05, px - 0.05, px, 100.0)
        # mainshock at -3: +4% bar on 5x volume
        b = bars[-3]
        bars[-3] = _bar(b.symbol, b.timestamp, 100.0, 104.2, 99.9, 104.0, 500.0)
        # aftershock continuation: closes beyond mainshock close on elevated volume
        b = bars[-2]
        bars[-2] = _bar(b.symbol, b.timestamp, 104.0, 104.6, 103.8, 104.4, 200.0)
        b = bars[-1]
        bars[-1] = _bar(b.symbol, b.timestamp, 104.4, 105.1, 104.2, 104.9, 200.0)
        sig = signals.omori_aftershock_ladder(bars, {}, {})
        assert sig is not None and sig.side == "buy"


def test_load_system_state_from_trades(tmp_db: Path) -> None:
    with db.connect(tmp_db) as conn:
        for i, (variant, pnl, reason) in enumerate([
            ("null_baseline", -2.0, "stop_loss"),
            ("null_baseline", -1.0, "time_exit"),
            ("null_baseline", 3.0, "take_profit"),
            ("other_arm", -2.0, "stop_loss"),
        ]):
            conn.execute(
                "INSERT INTO signals (symbol, variant_name, strategy, side, bar_timestamp,"
                " price_at_signal, reasoning_json, emitted_at)"
                " VALUES ('BTC/USD', ?, 's', 'buy', ?, 100.0, '{}', 't')",
                (variant, f"2026-07-16T0{i}:00:00+00:00"),
            )
            conn.execute(
                "INSERT INTO trades (signal_id, variant_name, symbol, side, qty, entry_price,"
                " entry_time, exit_time, exit_reason, pnl_usd, is_real_money, status)"
                " VALUES (?, ?, 'BTC/USD', 'buy', 1.0, 100.0, ?, ?, ?, ?, 0, 'closed')",
                (i + 1, variant, f"2026-07-16T0{i}:00:00+00:00",
                 f"2026-07-16T1{i}:00:00+00:00", reason, pnl),
            )
        state = signals.load_system_state(
            conn, now=datetime(2026, 7, 16, 20, 0, tzinfo=timezone.utc)
        )
    assert state["null_win_rate"] == pytest.approx(1 / 3)
    assert state["recent_stopouts"] == 2  # null + other_arm stop-outs both count


# --- Foundry round 002 (smoke + gate tests) ----------------------------------


class TestFoundryRound002:
    def test_all_registered(self) -> None:
        for key in ("cond_entropy_expansion", "r0_ignition", "absorption_shelf",
                    "expiry_pin_release", "rejection_gated_ignition"):
            assert key in signals.STRATEGY_REGISTRY

    def test_insufficient_bars_all_return_none(self) -> None:
        bars = _flat_series("BTC/USD", 20)
        ctx = {"system_state": {"rejection_rate": 0.9, "placebo_stop_rate": 0.9}}
        assert signals.conditional_entropy_regime_expansion(bars, {}, {}) is None
        assert signals.epidemic_r0_crossover_ignition(bars, {}, {}) is None
        assert signals.absorption_shelf_breakout(bars, {}, {}) is None
        assert signals.options_expiry_pin_release(bars, {}, {}) is None
        assert signals.rejection_streak_gated_ignition(bars, {}, ctx) is None

    def test_flat_series_no_fires(self) -> None:
        bars = _flat_series("ETH/USD", 500)
        ctx = {"system_state": {"rejection_rate": 0.9, "placebo_stop_rate": 0.9}}
        assert signals.conditional_entropy_regime_expansion(bars, {}, {}) is None
        assert signals.epidemic_r0_crossover_ignition(bars, {}, {}) is None
        assert signals.absorption_shelf_breakout(bars, {}, {}) is None
        assert signals.options_expiry_pin_release(bars, {}, {}) is None
        assert signals.rejection_streak_gated_ignition(bars, {}, ctx) is None

    # -- idea 1: conditional entropy surge -----------------------------------

    def _entropy_surge_bars(self) -> list[BarRow]:
        import math as _m
        # 48 strictly alternating small returns (order-2 predictable),
        # then a messy 12-return tail ending in two big up bars.
        rets = [0.002 if i % 2 == 0 else -0.002 for i in range(48)]
        # tail signs chosen so every order-2 context's next sign is ~50/50
        # (high conditional entropy), ending in two big same-sign bars
        tail_signs = [1, 0, 1, 0, 0, 0, 1, 1, 0, 1]
        rets += [0.002 if s else -0.002 for s in tail_signs] + [0.02, 0.02]
        closes = [100.0]
        for r in rets:
            closes.append(closes[-1] * _m.exp(r))
        bars = _flat_series("BTC/USD", len(closes) + 10)
        out = list(bars[:10])
        prev = closes[0]
        for i, c in enumerate(closes):
            b = bars[10 + i]
            out.append(_bar(b.symbol, b.timestamp, prev, max(prev, c) + 0.01,
                            min(prev, c) - 0.01, c, 100.0))
            prev = c
        return out

    def test_entropy_surge_fires_buy(self) -> None:
        bars = self._entropy_surge_bars()
        sig = signals.conditional_entropy_regime_expansion(bars, {}, {})
        assert sig is not None and sig.side == "buy"

    def test_entropy_no_fire_without_vol_spike(self) -> None:
        bars = self._entropy_surge_bars()
        sig = signals.conditional_entropy_regime_expansion(
            bars, {"vol_mult": 50.0}, {})
        assert sig is None

    # -- idea 2: R0 ignition --------------------------------------------------

    def _r0_ignition_bars(self) -> list[BarRow]:
        bars = _flat_series("SOL/USD", 100)  # dojis: signed volume 0
        def up(b, vol):
            return _bar(b.symbol, b.timestamp, 100.0, 100.15, 99.95, 100.1, vol)
        for i in range(88, 94):   # t-11..t-6: moderate steady up-flow
            bars[i] = up(bars[i], 200.0)
        for i in range(94, 99):   # t-5..t-1: flow dying (R0 < 1 at t-1)
            bars[i] = up(bars[i], 10.0)
        bars[99] = up(bars[99], 5000.0)  # t: ignition
        return bars

    def test_r0_ignition_fires_buy_on_crossover(self) -> None:
        sig = signals.epidemic_r0_crossover_ignition(self._r0_ignition_bars(), {}, {})
        assert sig is not None and sig.side == "buy"

    def test_r0_no_fire_without_crossover(self) -> None:
        bars = self._r0_ignition_bars()
        b = bars[99]
        bars[99] = _bar(b.symbol, b.timestamp, 100.0, 100.15, 99.95, 100.1, 10.0)
        assert signals.epidemic_r0_crossover_ignition(bars, {}, {}) is None

    # -- idea 3: absorption shelf ---------------------------------------------

    def _shelf_bars(self) -> list[BarRow]:
        bars = []
        flat = _flat_series("ETH/USD", 100)
        for b in flat:
            # body 0.2, range 1.0, vol 100 — never a shelf bar (vol too low)
            bars.append(_bar(b.symbol, b.timestamp, 100.2, 100.75, 99.75, 100.4, 100.0))
        for i in range(93, 99):  # shelf: high volume, tiny body, overlapping
            b = bars[i]
            bars[i] = _bar(b.symbol, b.timestamp, 100.4, 101.0, 100.0, 100.6, 200.0)
        b = bars[99]  # break: close > shelf_high 101.0 + 0.5*ATR(~1.0)
        bars[99] = _bar(b.symbol, b.timestamp, 100.6, 101.9, 100.5, 101.8, 200.0)
        return bars

    def test_shelf_break_fires_buy(self) -> None:
        sig = signals.absorption_shelf_breakout(self._shelf_bars(), {}, {})
        assert sig is not None and sig.side == "buy"

    def test_no_fire_when_break_lacks_volume(self) -> None:
        bars = self._shelf_bars()
        b = bars[99]
        bars[99] = _bar(b.symbol, b.timestamp, 100.6, 101.9, 100.5, 101.8, 100.0)
        assert signals.absorption_shelf_breakout(bars, {}, {}) is None

    # -- idea 4: expiry pin release -------------------------------------------

    def _pin_bars(self) -> list[BarRow]:
        from datetime import datetime, timedelta, timezone
        start = datetime(2026, 7, 10, 3, 40, tzinfo=timezone.utc)
        bars = []
        for i in range(55):  # 03:40 .. 08:10
            ts = (start + timedelta(minutes=5 * i)).isoformat()
            bars.append(_bar("BTC/USD", ts, 100.1, 100.3, 100.0, 100.2, 100.0))
        # last bar is 08:10; bars 07:00-07:55 are the pin (span 0.3 < 0.8%)
        b = bars[-1]
        bars[-1] = _bar(b.symbol, b.timestamp, 100.2, 100.9, 100.1, 100.8, 200.0)
        return bars

    def test_pin_release_fires_buy(self) -> None:
        sig = signals.options_expiry_pin_release(self._pin_bars(), {}, {})
        assert sig is not None and sig.side == "buy"

    def test_no_fire_outside_release_window(self) -> None:
        from datetime import datetime, timedelta, timezone
        start = datetime(2026, 7, 10, 9, 40, tzinfo=timezone.utc)  # afternoon
        bars = []
        for i in range(55):
            ts = (start + timedelta(minutes=5 * i)).isoformat()
            bars.append(_bar("BTC/USD", ts, 100.1, 100.3, 100.0, 100.2, 100.0))
        b = bars[-1]
        bars[-1] = _bar(b.symbol, b.timestamp, 100.2, 100.9, 100.1, 100.8, 200.0)
        assert signals.options_expiry_pin_release(bars, {}, {}) is None

    # -- idea 5: rejection-streak gate on the R0 engine -----------------------

    def test_gated_ignition_fires_when_gate_open(self) -> None:
        bars = self._r0_ignition_bars()
        ctx = {"system_state": {"rejection_rate": 0.8, "placebo_stop_rate": 0.7}}
        sig = signals.rejection_streak_gated_ignition(bars, {}, ctx)
        assert sig is not None and sig.side == "buy"

    def test_gated_ignition_suppressed_when_gate_shut(self) -> None:
        bars = self._r0_ignition_bars()
        for state in (
            {"rejection_rate": 0.2, "placebo_stop_rate": 0.7},   # low rejections
            {"rejection_rate": 0.8, "placebo_stop_rate": 0.2},   # placebo fine
            {"rejection_rate": None, "placebo_stop_rate": 0.7},  # no data yet
        ):
            assert signals.rejection_streak_gated_ignition(
                bars, {}, {"system_state": state}) is None

    def test_gated_ignition_none_without_context(self) -> None:
        assert signals.rejection_streak_gated_ignition(
            self._r0_ignition_bars(), {}, {}) is None


# --- Foundry round 003 (smoke + gate tests) ----------------------------------


class TestFoundryRound003:
    def test_all_registered(self) -> None:
        for key in ("gap_exhaustion", "asian_london_handoff", "slot_scarcity_gate",
                    "post_shock_drift", "breakout_retest_limit"):
            assert key in signals.STRATEGY_REGISTRY

    def test_insufficient_bars_all_return_none(self) -> None:
        bars = _flat_series("BTC/USD", 20)
        ctx = {"system_state": {"stop_out_rate": 0.2}}
        assert signals.gap_fill_exhaustion_continuation(bars, {}, {}) is None
        assert signals.asian_to_london_handoff_thrust(bars, {}, {}) is None
        assert signals.slot_scarcity_conviction_gate(bars, {}, ctx) is None
        assert signals.post_shock_multiday_drift(bars, {}, {}) is None
        assert signals.pullback_to_breakout_level_limit(bars, {}, {}) is None

    def test_flat_series_no_fires(self) -> None:
        bars = _flat_series("ETH/USD", 500)
        ctx = {"system_state": {"stop_out_rate": 0.2}}
        assert signals.gap_fill_exhaustion_continuation(bars, {}, {}) is None
        assert signals.asian_to_london_handoff_thrust(bars, {}, {}) is None
        assert signals.slot_scarcity_conviction_gate(bars, {}, ctx) is None
        assert signals.post_shock_multiday_drift(bars, {}, {}) is None
        assert signals.pullback_to_breakout_level_limit(bars, {}, {}) is None

    # -- idea 1: held gap ----------------------------------------------------

    def _gap_bars(self) -> list[BarRow]:
        bars = _flat_series("BTC/USD", 100)  # closes 100, bodies 0, vol 100
        b = bars[-1]  # gap up 0.5%, closes through open, big body + volume
        bars[-1] = _bar(b.symbol, b.timestamp, 100.5, 101.1, 100.4, 101.0, 300.0)
        return bars

    def test_gap_held_fires_buy(self) -> None:
        sig = signals.gap_fill_exhaustion_continuation(self._gap_bars(), {}, {})
        assert sig is not None and sig.side == "buy"

    def test_gap_faded_no_fire(self) -> None:
        bars = self._gap_bars()
        b = bars[-1]  # gap up but closes back BELOW open — faded, not held
        bars[-1] = _bar(b.symbol, b.timestamp, 100.5, 100.6, 99.9, 100.1, 300.0)
        assert signals.gap_fill_exhaustion_continuation(bars, {}, {}) is None

    # -- idea 2: Asian-range break in the London window ----------------------

    def _london_bars(self, break_out: bool = True) -> list[BarRow]:
        from datetime import datetime, timedelta, timezone
        start = datetime(2026, 7, 10, 0, 0, tzinfo=timezone.utc)  # Friday
        bars = []
        for i in range(91):  # 00:00 .. 07:30, range 99.8-100.2
            ts = (start + timedelta(minutes=5 * i)).isoformat()
            bars.append(_bar("BTC/USD", ts, 100.0, 100.2, 99.8, 100.0, 100.0))
        b = bars[-1]  # 07:30 bar
        if break_out:
            bars[-1] = _bar(b.symbol, b.timestamp, 100.1, 100.8, 100.0, 100.7, 300.0)
        return bars

    def test_london_break_fires_buy(self) -> None:
        sig = signals.asian_to_london_handoff_thrust(self._london_bars(), {}, {})
        assert sig is not None and sig.side == "buy"

    def test_no_fire_on_weekend(self) -> None:
        from datetime import datetime, timedelta, timezone
        start = datetime(2026, 7, 11, 0, 0, tzinfo=timezone.utc)  # Saturday
        bars = []
        for i in range(91):
            ts = (start + timedelta(minutes=5 * i)).isoformat()
            bars.append(_bar("BTC/USD", ts, 100.0, 100.2, 99.8, 100.0, 100.0))
        b = bars[-1]
        bars[-1] = _bar(b.symbol, b.timestamp, 100.1, 100.8, 100.0, 100.7, 300.0)
        assert signals.asian_to_london_handoff_thrust(bars, {}, {}) is None

    # -- idea 3: stop-rate gate on the gap engine ----------------------------

    def test_gate_open_fires(self) -> None:
        ctx = {"system_state": {"stop_out_rate": 0.2}}
        sig = signals.slot_scarcity_conviction_gate(self._gap_bars(), {}, ctx)
        assert sig is not None and sig.side == "buy"

    def test_gate_shut_or_missing_suppresses(self) -> None:
        bars = self._gap_bars()
        assert signals.slot_scarcity_conviction_gate(
            bars, {}, {"system_state": {"stop_out_rate": 0.8}}) is None
        assert signals.slot_scarcity_conviction_gate(
            bars, {}, {"system_state": {"stop_out_rate": None}}) is None
        assert signals.slot_scarcity_conviction_gate(bars, {}, {}) is None

    # -- idea 4: post-shock drift --------------------------------------------

    def test_shock_fires_buy_with_multiday_exits(self) -> None:
        bars = _flat_series("SOL/USD", 150)
        b = bars[-1]  # +3.5% body on 4x volume
        bars[-1] = _bar(b.symbol, b.timestamp, 100.0, 103.8, 99.9, 103.5, 400.0)
        sig = signals.post_shock_multiday_drift(bars, {}, {})
        assert sig is not None and sig.side == "buy"

    def test_shock_without_volume_no_fire(self) -> None:
        bars = _flat_series("SOL/USD", 150)
        b = bars[-1]
        bars[-1] = _bar(b.symbol, b.timestamp, 100.0, 103.8, 99.9, 103.5, 150.0)
        assert signals.post_shock_multiday_drift(bars, {}, {}) is None

    # -- idea 5: breakout retest ---------------------------------------------

    def _retest_bars(self) -> list[BarRow]:
        bars = _flat_series("ETH/USD", 130)  # high 100.2 everywhere
        i_brk = 126  # breakout bar: close 101 > 100.2 * 1.005, vol 300
        b = bars[i_brk]
        bars[i_brk] = _bar(b.symbol, b.timestamp, 100.1, 101.2, 100.0, 101.0, 300.0)
        for i in (127, 128):  # holds above the level — no touch yet
            b = bars[i]
            bars[i] = _bar(b.symbol, b.timestamp, 101.0, 101.3, 100.8, 101.1, 100.0)
        b = bars[129]  # retest: low touches the broken level (100.01)
        bars[129] = _bar(b.symbol, b.timestamp, 100.9, 101.0, 100.0, 100.4, 100.0)
        return bars

    def test_retest_fires_buy_at_level(self) -> None:
        sig = signals.pullback_to_breakout_level_limit(self._retest_bars(), {}, {})
        assert sig is not None and sig.side == "buy"
        assert sig.reasoning["level"] == pytest.approx(100.01)  # flat-series high

    def test_no_chase_without_retest(self) -> None:
        bars = self._retest_bars()
        b = bars[129]  # stays high — armed but never touches the level
        bars[129] = _bar(b.symbol, b.timestamp, 101.0, 101.4, 100.9, 101.2, 100.0)
        assert signals.pullback_to_breakout_level_limit(bars, {}, {}) is None
