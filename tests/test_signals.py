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


def test_default_registry_has_the_two_defaults_plus_ten_sweep_variants() -> None:
    from config import STRATEGY_VARIANTS
    expected = {
        "bollinger_default", "macross_default",
        "bollinger_tight", "bollinger_loose", "bollinger_long",
        "bollinger_quick", "bollinger_verytight",
        "macross_fast", "macross_slow", "macross_veryfast",
        "macross_veryslow", "macross_balanced",
    }
    assert set(STRATEGY_VARIANTS.keys()) == expected, (
        "registry should hold the 2 PROJECT.md defaults plus the 10 Week-3 "
        "parameter-sweep variants (12 total)"
    )
    assert len(STRATEGY_VARIANTS) == 12
    assert STRATEGY_VARIANTS["bollinger_default"]["params"] == {
        "period": 20, "stddev": 2.0, "tp": 0.05, "sl": 0.03, "time_exit_hours": 24,
    }
    assert STRATEGY_VARIANTS["macross_default"]["params"] == {
        "fast": 12, "slow": 26, "tp": 0.05, "sl": 0.03,
    }
    assert all(v.get("enabled") is False for v in STRATEGY_VARIANTS.values()), (
        "all 12 variants must be disabled — retired per decision-log "
        "2026-07-02 roster call; entries kept only for replay reproducibility"
    )
    assert all(v["strategy"] in ("bollinger", "macross") for v in STRATEGY_VARIANTS.values())


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
        bars = _bars_from_closes([10.0] * 5)
        with pytest.raises(ValueError, match="must be <"):
            macross_strategy(bars, {"fast": 26, "slow": 12}, {})

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
