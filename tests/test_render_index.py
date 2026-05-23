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


def test_days_to_phase_1_review_returns_none_when_no_target(tmp_db: Path) -> None:
    now = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
    assert render_index.days_to_phase_1_review(now, None) is None


def test_get_curriculum_start_returns_none_with_no_runs(tmp_db: Path) -> None:
    with db.connect(tmp_db) as conn:
        assert render_index.get_curriculum_start(conn) is None


def test_get_curriculum_start_returns_earliest_ok(tmp_db: Path) -> None:
    """Multiple runs: returns the earliest ok one, ignores failed ones earlier."""
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'failed')",
            ("2026-05-01T00:00:00+00:00",),
        )
        conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'ok')",
            ("2026-05-02T12:00:00+00:00",),
        )
        conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'ok')",
            ("2026-05-03T00:00:00+00:00",),
        )
    with db.connect(tmp_db) as conn:
        ts = render_index.get_curriculum_start(conn)
    assert ts == datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)


def test_get_curriculum_start_skips_only_failed(tmp_db: Path) -> None:
    """Runs exist but none are ok → still None (curriculum hasn't started)."""
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'failed')",
            ("2026-05-01T00:00:00+00:00",),
        )
    with db.connect(tmp_db) as conn:
        assert render_index.get_curriculum_start(conn) is None


def test_get_curriculum_start_ignores_backfill_kind(tmp_db: Path) -> None:
    """A backfill run (even successful) does NOT start the curriculum.

    The curriculum measures cron operations; backfills are seeding events.
    """
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'backfill')",
            ("2026-05-03T00:00:00+00:00",),
        )
    with db.connect(tmp_db) as conn:
        assert render_index.get_curriculum_start(conn) is None, (
            "a successful backfill must not be treated as a curriculum-start cron run"
        )


def test_get_curriculum_start_ignores_manual_kind(tmp_db: Path) -> None:
    """Manual ad-hoc fetches don't start the curriculum either."""
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'manual')",
            ("2026-05-03T00:00:00+00:00",),
        )
    with db.connect(tmp_db) as conn:
        assert render_index.get_curriculum_start(conn) is None


def test_get_curriculum_start_returns_earliest_cron_with_mixed_kinds(tmp_db: Path) -> None:
    """When backfill, manual, and cron rows all exist, returns the earliest cron one
    even if it's later in wall-clock time than the backfill/manual rows."""
    with db.connect(tmp_db) as conn:
        # Earliest row is a backfill — should be ignored.
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'backfill')",
            ("2026-05-01T00:00:00+00:00",),
        )
        # Manual run between backfill and cron — also ignored.
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'manual')",
            ("2026-05-02T00:00:00+00:00",),
        )
        # Two cron runs; the earlier one wins.
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'cron')",
            ("2026-05-04T12:00:00+00:00",),
        )
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'cron')",
            ("2026-05-03T12:00:00+00:00",),
        )
    with db.connect(tmp_db) as conn:
        ts = render_index.get_curriculum_start(conn)
    assert ts == datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc), (
        "must return the earliest cron-kind ok run, not the earliest of any kind"
    )


def test_get_curriculum_start_skips_failed_cron(tmp_db: Path) -> None:
    """A failed cron run doesn't start the curriculum either — only ok+cron does."""
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'failed', 'cron')",
            ("2026-05-03T00:00:00+00:00",),
        )
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'cron')",
            ("2026-05-04T00:00:00+00:00",),
        )
    with db.connect(tmp_db) as conn:
        ts = render_index.get_curriculum_start(conn)
    assert ts == datetime(2026, 5, 4, 0, 0, tzinfo=timezone.utc)


def test_compute_phase_1_review_target_uses_first_ok_plus_56_days(tmp_db: Path) -> None:
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'ok')",
            ("2026-05-03T00:00:00+00:00",),
        )
    with db.connect(tmp_db) as conn:
        target = render_index.compute_phase_1_review_target(conn)
    assert target == datetime(2026, 5, 3, 0, 0, tzinfo=timezone.utc) + timedelta(
        days=render_index.CURRICULUM_DAYS
    )


def test_compute_phase_1_review_target_returns_none_with_no_runs(tmp_db: Path) -> None:
    with db.connect(tmp_db) as conn:
        assert render_index.compute_phase_1_review_target(conn) is None


def test_index_shows_emdash_and_not_yet_started_when_no_runs(
    tmp_db: Path, tmp_repo: Path
) -> None:
    """The deliverable: with no successful runs, days renders as em-dash and
    the sublabel reads 'not yet started' (not 'calendar')."""
    now = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    out_path = tmp_repo / "INDEX.md"
    render_index.write_index(out_path, now=now, db_path=tmp_db, repo_root=tmp_repo)
    text = out_path.read_text()
    band = text.split("# algotrading-paper")[1].split("§ 01")[0]
    assert "Days to phase 1 review" in band
    assert "**—**" in band, "days-to-review must be em-dash when no anchor exists"
    assert "not yet started" in band, "sublabel must read 'not yet started'"
    assert "**0 / 3**" in band


def test_index_shows_days_count_after_first_ok_run(
    tmp_db: Path, tmp_repo: Path
) -> None:
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'ok')",
            ("2026-05-03T00:00:00+00:00",),
        )
    now = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    out_path = tmp_repo / "INDEX.md"
    render_index.write_index(out_path, now=now, db_path=tmp_db, repo_root=tmp_repo)
    text = out_path.read_text()
    band = text.split("# algotrading-paper")[1].split("§ 01")[0]
    expected_days = render_index.CURRICULUM_DAYS - 14  # 56 - 14 since 5/3 to 5/17
    assert f"**{expected_days}**" in band, (
        f"days-to-review should be {expected_days} days "
        f"(anchor 2026-05-03 + {render_index.CURRICULUM_DAYS}d − today 2026-05-17)"
    )
    # New sublabel: actual review date, not the word "calendar"
    expected_end_date = "2026-06-28"  # 2026-05-03 + 56 days
    assert f"ends {expected_end_date}" in band, (
        f"sublabel must read 'ends {expected_end_date}'; got band:\n{band}"
    )
    assert "calendar" not in band, "sublabel should not say 'calendar' anymore"


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


def test_read_pending_items_doc_only_returns_empty(tmp_repo: Path) -> None:
    """A pending.md with only prose and no YAML body returns []."""
    (tmp_repo / "pending.md").write_text(
        "# Pending\n\nSome prose explaining the file.\n"
    )
    assert render_index.read_pending_items(tmp_repo) == []


def test_read_pending_items_parses_yaml_records(tmp_repo: Path) -> None:
    (tmp_repo / "pending.md").write_text(
        "# Pending\n\nIntro prose.\n\n"
        "---\n\n"
        "- thing: First item\n"
        "  detail: with a clarifying line\n"
        "  when: 10d\n"
        "  kind: gate\n"
        "  promoted: true\n"
        "\n"
        "- thing: Second item without a detail\n"
        "  when: open\n"
        "  kind: ops\n"
        "\n"
        "- thing: Third item with em-dash — punctuation\n"
        "  detail: should survive\n"
        "  when: 5d\n"
        "  kind: log\n"
    )
    items = render_index.read_pending_items(tmp_repo)
    assert len(items) == 3
    assert items[0] == "First item — with a clarifying line"
    assert items[1] == "Second item without a detail"
    assert items[2] == "Third item with em-dash — punctuation — should survive"


def test_read_pending_items_handles_malformed_yaml(tmp_repo: Path) -> None:
    """A broken YAML body returns [] rather than raising — the surface
    keeps working even if the operator types an unbalanced quote."""
    (tmp_repo / "pending.md").write_text(
        "# Pending\n\n---\n\n- thing: broken\n  detail: \"unclosed\n"
    )
    assert render_index.read_pending_items(tmp_repo) == []


def test_read_pending_items_preserves_hash_in_quoted_strings(tmp_repo: Path) -> None:
    """YAML treats unquoted # as comment start — values containing # must be
    quoted in pending.md. Verifies quoted values round-trip cleanly."""
    (tmp_repo / "pending.md").write_text(
        "---\n\n"
        '- thing: "Friday adversarial review · #1"\n'
        "  when: 5d\n"
        "  kind: ops\n"
    )
    items = render_index.read_pending_items(tmp_repo)
    assert items == ["Friday adversarial review · #1"]


def test_real_queue_files_parse_to_valid_records() -> None:
    """Guard: the committed pending.md / decision_log_queue.md / build_queue.md
    must each parse to ≥1 valid record with thing + kind. A malformed YAML edit
    silently returns [] (blanking a surface section without erroring), so this
    catches a fat-fingered operator edit before it ships."""
    root = Path(render_index.__file__).resolve().parent
    for fname in ("pending.md", "decision_log_queue.md", "build_queue.md"):
        path = root / fname
        assert path.exists(), f"{fname} missing"
        recs = render_index.read_yaml_md_records(path)
        assert len(recs) > 0, f"{fname} parsed to zero records — malformed YAML?"
        for r in recs:
            assert r.get("thing"), f"{fname}: record missing 'thing': {r!r}"
            assert r.get("kind"), f"{fname}: record missing 'kind': {r.get('thing')!r}"


def test_read_pending_records_returns_full_structure(tmp_repo: Path) -> None:
    """generate_surface.py consumes the structured form via this function."""
    (tmp_repo / "pending.md").write_text(
        "---\n\n"
        "- thing: First\n"
        "  detail: detail-1\n"
        "  when: 10d\n"
        "  kind: gate\n"
        "  promoted: true\n"
        "\n"
        "- thing: Second\n"
        "  when: open\n"
        "  kind: ops\n"
    )
    records = render_index.read_pending_records(tmp_repo)
    assert len(records) == 2
    assert records[0]["thing"] == "First"
    assert records[0]["promoted"] is True
    assert records[0]["kind"] == "gate"
    assert records[1]["when"] == "open"
    assert "detail" not in records[1] or records[1].get("detail") is None


def test_pending_decisions_rendered_in_index(tmp_db: Path, tmp_repo: Path) -> None:
    (tmp_repo / "pending.md").write_text(
        "---\n\n"
        "- thing: Test pending item one\n"
        "  detail: with detail\n"
        "  when: 10d\n"
        "  kind: gate\n"
        "\n"
        "- thing: Test pending item two\n"
        "  when: open\n"
        "  kind: ops\n"
    )
    now = datetime(2026, 5, 2, 16, 6, 29, tzinfo=timezone.utc)
    out_path = tmp_repo / "INDEX.md"
    render_index.write_index(out_path, now=now, db_path=tmp_db, repo_root=tmp_repo)
    text = out_path.read_text()
    assert "§ 02 — Pending decisions · 2 items" in text
    assert "▸ Test pending item one — with detail" in text
    assert "▸ Test pending item two" in text


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
