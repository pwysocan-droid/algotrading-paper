"""Tests for compare.py — the gate-2 A/B instrument."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

import compare
import db


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


def _seed_closed_trades(
    db_path: Path, variant: str, pnl_pcts: list[float], entry_price: float = 100.0
) -> None:
    with db.connect(db_path) as conn:
        for i, pct in enumerate(pnl_pcts):
            cur = conn.execute(
                "INSERT INTO signals (symbol, variant_name, strategy, side, bar_timestamp,"
                " price_at_signal, reasoning_json, emitted_at)"
                " VALUES ('BTC/USD', ?, 'test', 'buy', ?, ?, '{}', ?)",
                (variant, f"2026-07-01T{i//60:02d}:{i%60:02d}:00+00:00", entry_price,
                 "2026-07-01T00:00:00+00:00"),
            )
            conn.execute(
                "INSERT INTO trades (signal_id, variant_name, symbol, side, qty, entry_price,"
                " entry_time, exit_price, exit_time, exit_reason, pnl_usd, pnl_pct,"
                " is_real_money, status)"
                " VALUES (?, ?, 'BTC/USD', 'buy', 2.0, ?, ?, ?, ?, 'time_exit', ?, ?, 0, 'closed')",
                (cur.lastrowid, variant, entry_price,
                 f"2026-07-01T{i//60:02d}:{i%60:02d}:00+00:00",
                 entry_price * (1 + pct / 100),
                 f"2026-07-02T{i//60:02d}:{i%60:02d}:00+00:00",
                 entry_price * pct / 100 * 2.0, pct),
            )


def test_insufficient_below_min_trades(tmp_db: Path) -> None:
    _seed_closed_trades(tmp_db, "cand", [1.0] * 50)
    _seed_closed_trades(tmp_db, "null_baseline", [-0.5] * 200)

    result = compare.compare("cand", "null_baseline", db_path=tmp_db)

    assert result.verdict == "INSUFFICIENT"
    assert result.p_value is None
    assert "wait for more data" in result.detail
    assert result.a.n == 50 and result.b.n == 200


def test_clear_winner_detected(tmp_db: Path) -> None:
    rng = random.Random(42)
    _seed_closed_trades(tmp_db, "cand", [rng.gauss(0.8, 0.5) for _ in range(150)])
    _seed_closed_trades(tmp_db, "null_baseline", [rng.gauss(-0.2, 0.5) for _ in range(150)])

    result = compare.compare("cand", "null_baseline", db_path=tmp_db)

    assert result.verdict == "A_WINS"
    assert result.p_value < 0.05
    assert result.a.mean_pct > result.b.mean_pct


def test_no_difference_between_identical_distributions(tmp_db: Path) -> None:
    rng = random.Random(7)
    _seed_closed_trades(tmp_db, "cand", [rng.gauss(0.1, 1.0) for _ in range(150)])
    _seed_closed_trades(tmp_db, "null_baseline", [rng.gauss(0.1, 1.0) for _ in range(150)])

    result = compare.compare("cand", "null_baseline", db_path=tmp_db)

    assert result.verdict == "NO_DIFFERENCE"
    assert result.p_value >= 0.05


def test_b_wins_when_baseline_is_better(tmp_db: Path) -> None:
    rng = random.Random(3)
    _seed_closed_trades(tmp_db, "cand", [rng.gauss(-0.6, 0.4) for _ in range(120)])
    _seed_closed_trades(tmp_db, "null_baseline", [rng.gauss(0.4, 0.4) for _ in range(120)])

    result = compare.compare("cand", "null_baseline", db_path=tmp_db)

    assert result.verdict == "B_WINS"


def test_open_trades_excluded(tmp_db: Path) -> None:
    _seed_closed_trades(tmp_db, "cand", [1.0] * 100)
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO trades (signal_id, variant_name, symbol, side, qty, entry_price,"
            " entry_time, is_real_money, status)"
            " VALUES (1, 'cand', 'BTC/USD', 'buy', 2.0, 100.0, '2026-07-03T00:00:00+00:00', 0, 'open')"
        )
    result = compare.compare("cand", "cand", db_path=tmp_db)
    assert result.a.n == 100  # the open trade is not counted


def test_welch_identical_constant_samples() -> None:
    t, p = compare.welch_t([1.0] * 10, [1.0] * 10)
    assert t == 0.0
    assert p == 1.0


def test_report_renders_verdict_and_table(tmp_db: Path) -> None:
    rng = random.Random(42)
    _seed_closed_trades(tmp_db, "cand", [rng.gauss(0.8, 0.5) for _ in range(150)])
    _seed_closed_trades(tmp_db, "null_baseline", [rng.gauss(-0.2, 0.5) for _ in range(150)])

    result = compare.compare("cand", "null_baseline", db_path=tmp_db)
    report = compare.render_report(result)

    assert "**Verdict: A_WINS**" in report
    assert "| `cand` | 150 |" in report
    assert "| `null_baseline` | 150 |" in report
    assert "Welch t" in report


def test_report_insufficient_uses_emdash_for_stats(tmp_db: Path) -> None:
    _seed_closed_trades(tmp_db, "cand", [1.0] * 5)
    _seed_closed_trades(tmp_db, "null_baseline", [1.0] * 5)
    result = compare.compare("cand", "null_baseline", db_path=tmp_db)
    report = compare.render_report(result)
    assert "**Verdict: INSUFFICIENT**" in report
    assert "Welch t = —" in report
