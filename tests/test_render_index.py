"""Tests for render_index.py."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
import render_index


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "reports").mkdir()
    (repo / "reports" / "ab").mkdir()
    (repo / "recommendations").mkdir()
    (repo / "reviews").mkdir()
    return repo


def test_uptime_returns_none_with_no_runs(tmp_db: Path) -> None:
    now = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        assert render_index.system_uptime_pct(conn, now) is None


def test_uptime_calculation(tmp_db: Path) -> None:
    now = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        for i in range(10):
            conn.execute(
                "INSERT INTO runs (started_at, status) VALUES (?, 'ok')",
                ((now - timedelta(hours=i)).isoformat(),),
            )
        for i in range(2):
            conn.execute(
                "INSERT INTO runs (started_at, status) VALUES (?, 'failed')",
                ((now - timedelta(hours=i + 100)).isoformat(),),
            )
    with db.connect(tmp_db) as conn:
        pct = render_index.system_uptime_pct(conn, now)
    assert pct is not None
    assert abs(pct - (10 / 12) * 100.0) < 0.01


def test_phase_2_gates_all_zero_in_week_1(tmp_db: Path) -> None:
    now = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        n, gates = render_index.phase_2_gates_passed(conn, now)
    assert n == 0
    assert gates == [False, False, False]


def test_days_to_phase_1_review() -> None:
    now = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
    target = datetime(2026, 6, 28, 12, 0, tzinfo=timezone.utc)
    days = render_index.days_to_phase_1_review(now, target)
    assert days == 57


def test_days_to_phase_1_review_clamps_to_zero() -> None:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
    target = datetime(2026, 6, 28, 12, 0, tzinfo=timezone.utc)
    assert render_index.days_to_phase_1_review(now, target) == 0


def test_discover_surfaces_empty_repo(tmp_repo: Path) -> None:
    surfaces = render_index.discover_surfaces(tmp_repo)
    assert len(surfaces) == 7
    for s in surfaces:
        assert s.filename is None
        assert s.generated is None


def test_discover_surfaces_finds_replay(tmp_repo: Path) -> None:
    rpath = tmp_repo / "reports" / "2026-05-02-replay.md"
    rpath.write_text("# replay")
    surfaces = render_index.discover_surfaces(tmp_repo)
    replay = next(s for s in surfaces if s.surface == "replay")
    assert replay.filename == "reports/2026-05-02-replay.md"
    assert replay.status == "ok"


def test_assemble_index_state_week_1_empty(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 2, 16, 6, 29, tzinfo=timezone.utc)
    state = render_index.assemble_index_state(
        now=now, db_path=tmp_db, repo_root=tmp_repo, phase_label="Phase 1", week=1
    )
    assert state["phase"] == "Phase 1"
    assert state["week"] == 1
    assert state["timestamp"] == now
    assert len(state["stats"]) == 4
    assert len(state["surfaces"]) == 7
    assert state["flags"] == []


def test_write_index_idempotent(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 2, 16, 6, 29, tzinfo=timezone.utc)
    out_path = tmp_repo / "INDEX.md"
    render_index.write_index(out_path, now=now, db_path=tmp_db, repo_root=tmp_repo)
    first = out_path.read_text()
    render_index.write_index(out_path, now=now, db_path=tmp_db, repo_root=tmp_repo)
    second = out_path.read_text()
    assert first == second


def test_write_index_produces_v1_pattern(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 2, 16, 6, 29, tzinfo=timezone.utc)
    out_path = tmp_repo / "INDEX.md"
    render_index.write_index(out_path, now=now, db_path=tmp_db, repo_root=tmp_repo,
                             week=1, phase_label="Phase 1")
    text = out_path.read_text()
    assert "# algotrading-paper" in text
    assert "Phase 1" in text
    assert "Week 1" in text
    assert "**—**" in text, "uptime is em-dash when no runs have happened"
    assert "**0**" in text, "trades this week is explicitly 0"
    assert "**0 / 3**" in text, "0 of 3 phase 2 gates passed"
    assert "§ 01 — Surfaces" in text
    assert "§ 02 — Reading order" in text
    assert "§ 03 — Foundational documents" in text
    assert "§ Flags · none" in text
    assert "PROJECT.md" in text
    assert "philosophy.md" in text
    assert "no data yet" not in text


def test_trades_this_week_zero_in_empty_db(tmp_db: Path) -> None:
    now = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        n = render_index.trades_this_week(conn, now)
    assert n == 0
