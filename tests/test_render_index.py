"""Tests for render_index.py."""

from __future__ import annotations

import subprocess
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


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
            "HOME": str(repo),
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
        },
    )


@pytest.fixture
def git_repo(tmp_repo: Path) -> Path:
    _git(tmp_repo, "init", "-q", "-b", "main")
    return tmp_repo


def test_uptime_returns_none_with_no_runs(tmp_db: Path) -> None:
    now = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        assert render_index.system_uptime_pct(conn, now) is None


def test_uptime_calculation_against_expected_denominator(tmp_db: Path) -> None:
    """Uptime is ok_count / expected_runs_in_window — not ok_count / actual_runs.

    With 4 weeks of expected runs at 5-min cadence (288 * 28 = 8064), seeding
    4000 successful and 32 failed runs yields ~49.6% uptime, not ~99%.
    """
    now = datetime(2026, 5, 30, 0, 0, tzinfo=timezone.utc)
    expected_in_window = render_index.EXPECTED_RUNS_PER_DAY * 4 * 7
    with db.connect(tmp_db) as conn:
        for i in range(4000):
            conn.execute(
                "INSERT INTO runs (started_at, status) VALUES (?, 'ok')",
                ((now - timedelta(minutes=(i + 1) * 5)).isoformat(),),
            )
        for i in range(32):
            conn.execute(
                "INSERT INTO runs (started_at, status) VALUES (?, 'failed')",
                ((now - timedelta(minutes=(4000 + i + 1) * 5)).isoformat(),),
            )
    with db.connect(tmp_db) as conn:
        pct = render_index.system_uptime_pct(conn, now)
    assert pct is not None
    assert abs(pct - (4000 / expected_in_window) * 100.0) < 0.5


def test_uptime_with_one_run_does_not_read_as_full(tmp_db: Path) -> None:
    """Regression: previously 1 ok run / 1 total run = 100% — vacuously true.

    The fix uses expected as the denominator; 1 ok run / 8064 expected ≈ 0.012%.
    """
    now = datetime(2026, 5, 3, 0, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'ok')",
            ((now - timedelta(hours=1)).isoformat(),),
        )
    with db.connect(tmp_db) as conn:
        pct = render_index.system_uptime_pct(conn, now)
    assert pct is not None
    assert pct < 1.0, f"1 run should not read as full uptime; got {pct}%"


def test_gate_1_fails_with_insufficient_runs_even_if_all_ok(tmp_db: Path) -> None:
    """Even at trivially 100% uptime, gate 1 requires GATE_1_MIN_RUNS history."""
    now = datetime(2026, 5, 3, 0, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'ok')",
            ((now - timedelta(hours=1)).isoformat(),),
        )
    with db.connect(tmp_db) as conn:
        n, gates = render_index.phase_2_gates_passed(conn, now)
    assert gates[0] is False, (
        "1 successful run is not enough cron history; the trivial-100% case "
        "must not count as gate 1 pass"
    )
    assert n == 0


def test_gate_1_passes_with_full_cron_history_and_high_uptime(tmp_db: Path) -> None:
    now = datetime(2026, 5, 30, 0, 0, tzinfo=timezone.utc)
    expected = render_index.EXPECTED_RUNS_PER_DAY * 4 * 7  # 8064
    n_ok = int(expected * 0.97)
    with db.connect(tmp_db) as conn:
        for i in range(n_ok):
            conn.execute(
                "INSERT INTO runs (started_at, status) VALUES (?, 'ok')",
                ((now - timedelta(minutes=(i + 1) * 5)).isoformat(),),
            )
    with db.connect(tmp_db) as conn:
        n, gates = render_index.phase_2_gates_passed(conn, now)
    assert gates[0] is True, (
        "8064 expected, ~97% ok runs across 4 weeks should satisfy gate 1"
    )


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
    assert "§ 01 — Recently changed" in text
    assert "§ 02 — Pending decisions" in text
    assert "§ 03 — Read-me-when-lost" in text
    assert "§ 04 — Surfaces" in text
    assert "§ 05 — Reading order" in text
    assert "§ 06 — Foundational documents" in text
    assert "§ Flags · none" in text
    assert "PROJECT.md" in text
    assert "philosophy.md" in text
    assert "no data yet" not in text


def test_trades_this_week_zero_in_empty_db(tmp_db: Path) -> None:
    now = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        n = render_index.trades_this_week(conn, now)
    assert n == 0


# ─────────────────────── § Pending decisions ────────────────────────────


def test_read_pending_items_missing_file_returns_empty(tmp_repo: Path) -> None:
    assert not (tmp_repo / "pending.md").exists()
    assert render_index.read_pending_items(tmp_repo) == []


def test_read_pending_items_empty_file_returns_empty(tmp_repo: Path) -> None:
    (tmp_repo / "pending.md").write_text("")
    assert render_index.read_pending_items(tmp_repo) == []


def test_read_pending_items_no_bullet_lines_returns_empty(tmp_repo: Path) -> None:
    (tmp_repo / "pending.md").write_text(
        "# Pending decisions\n\nSome prose explaining the file.\n"
    )
    assert render_index.read_pending_items(tmp_repo) == []


def test_read_pending_items_parses_bullet_lines(tmp_repo: Path) -> None:
    (tmp_repo / "pending.md").write_text(
        "# Header\n\nIntro prose.\n\n"
        "▸ first item — with em-dash\n\n"
        "▸ second item.\n\n"
        "Some non-bullet prose to ignore.\n\n"
        "▸ third item with multiple words and punctuation, here.\n"
    )
    items = render_index.read_pending_items(tmp_repo)
    assert len(items) == 3
    assert items[0] == "first item — with em-dash"
    assert items[1] == "second item."
    assert items[2].startswith("third item")


def test_pending_decisions_rendered_in_index(tmp_db: Path, tmp_repo: Path) -> None:
    (tmp_repo / "pending.md").write_text(
        "▸ Test pending item one.\n\n▸ Test pending item two.\n"
    )
    now = datetime(2026, 5, 2, 16, 6, 29, tzinfo=timezone.utc)
    out_path = tmp_repo / "INDEX.md"
    render_index.write_index(out_path, now=now, db_path=tmp_db, repo_root=tmp_repo)
    text = out_path.read_text()
    assert "§ 02 — Pending decisions · 2 items" in text
    assert "▸ Test pending item one." in text
    assert "▸ Test pending item two." in text


def test_pending_decisions_empty_collapses_in_index(tmp_db: Path, tmp_repo: Path) -> None:
    """No pending.md → § 02 collapses to · none, fully-formed but quiet."""
    now = datetime(2026, 5, 2, 16, 6, 29, tzinfo=timezone.utc)
    out_path = tmp_repo / "INDEX.md"
    render_index.write_index(out_path, now=now, db_path=tmp_db, repo_root=tmp_repo)
    text = out_path.read_text()
    assert "§ 02 — Pending decisions · none" in text


# ─────────────────────── § Recently changed ─────────────────────────────


def test_recently_changed_empty_repo_no_git_history(tmp_repo: Path) -> None:
    """In a non-git directory the function should not crash; returns []."""
    rows = render_index.discover_recently_changed(tmp_repo)
    assert rows == []


def test_recently_changed_git_repo_sorted_desc(git_repo: Path) -> None:
    """Multiple canonical files committed at different times — sorted newest first."""
    files_in_order = ["PROJECT.md", "philosophy.md", "playbook.md"]
    for i, f in enumerate(files_in_order):
        (git_repo / f).write_text(f"# {f}\n")
        _git(git_repo, "add", f)
        _git(
            git_repo, "commit", "-q", "-m", f"add {f}",
            "--date", f"2026-05-0{i + 1}T12:00:00Z",
        )

    rows = render_index.discover_recently_changed(git_repo)
    assert len(rows) == 3
    filenames = [row[0] for row in rows]
    assert filenames == [
        "[playbook.md](playbook.md)",
        "[philosophy.md](philosophy.md)",
        "[PROJECT.md](PROJECT.md)",
    ]
    assert "add playbook.md" in rows[0][2]


def test_recently_changed_truncates_long_messages(git_repo: Path) -> None:
    (git_repo / "PROJECT.md").write_text("# x\n")
    _git(git_repo, "add", "PROJECT.md")
    long_msg = "This is a deliberately long commit subject that goes well over thirty characters"
    _git(git_repo, "commit", "-q", "-m", long_msg)

    rows = render_index.discover_recently_changed(git_repo)
    assert len(rows) == 1
    change_cell = rows[0][2]
    assert len(change_cell) <= render_index.CHANGE_MSG_MAX
    assert change_cell.endswith("…")


def test_recently_changed_limits_to_n(git_repo: Path) -> None:
    for i, f in enumerate(render_index.CANONICAL_FILES):
        (git_repo / f).write_text(f"# {f}\n")
        _git(git_repo, "add", f)
        _git(
            git_repo, "commit", "-q", "-m", f"add {f}",
            "--date", f"2026-04-{(i % 28) + 1:02d}T12:00:00Z",
        )

    rows = render_index.discover_recently_changed(git_repo, n=5)
    assert len(rows) == 5
    rows = render_index.discover_recently_changed(git_repo, n=3)
    assert len(rows) == 3


def test_recently_changed_skips_files_with_no_history(git_repo: Path) -> None:
    (git_repo / "PROJECT.md").write_text("# x\n")
    _git(git_repo, "add", "PROJECT.md")
    _git(git_repo, "commit", "-q", "-m", "add PROJECT.md")
    rows = render_index.discover_recently_changed(git_repo)
    assert len(rows) == 1


# ─────────────────────── § Read-me-when-lost ────────────────────────────


def test_read_me_when_lost_is_static_and_populated(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 2, 16, 6, 29, tzinfo=timezone.utc)
    state = render_index.assemble_index_state(
        now=now, db_path=tmp_db, repo_root=tmp_repo
    )
    assert len(state["read_me_when_lost"]) == 4
    assert any("animating disciplines" in item for item in state["read_me_when_lost"])
    assert any("reframe entry" in item for item in state["read_me_when_lost"])
    assert any("methodology-imports" in item for item in state["read_me_when_lost"])
    assert any("playbook" in item.lower() for item in state["read_me_when_lost"])
