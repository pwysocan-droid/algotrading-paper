"""Tests for signals.py skeleton against an empty registry."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
import fetch
import signals
from config import StrategyVariant
from signals import BarRow, Signal, run_all_variants
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


def test_default_registry_is_empty_for_week_1() -> None:
    from config import STRATEGY_VARIANTS
    assert STRATEGY_VARIANTS == {}, (
        "Week 1 expects an empty STRATEGY_VARIANTS — strategies land in Week 2"
    )


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
