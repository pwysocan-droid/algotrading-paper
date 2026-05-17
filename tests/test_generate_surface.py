"""Tests for scripts/generate_surface.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
from scripts import generate_surface as gs


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "reviews").mkdir()
    return repo


# ───────────────────────── sparkline helpers ──────────────────────────


def test_render_sparkline_empty_returns_ground_pattern() -> None:
    chars, cls = gs.render_sparkline([])
    assert chars == gs.EMPTY_SPARKLINE
    assert cls == "empty"


def test_render_sparkline_all_zero_is_empty() -> None:
    chars, cls = gs.render_sparkline([0, 0, 0, 0, 0, 0, 0, 0])
    assert chars == gs.EMPTY_SPARKLINE
    assert cls == "empty"


def test_render_sparkline_flat_nonzero_uses_middle_char() -> None:
    chars, cls = gs.render_sparkline([5, 5, 5, 5, 5, 5, 5, 5])
    assert len(set(chars)) == 1
    assert cls is None


def test_render_sparkline_growing_marked_growing() -> None:
    chars, cls = gs.render_sparkline([1, 2, 3, 4, 5, 6, 7, 8])
    assert cls == "growing"
    assert chars[0] == "▁"
    assert chars[-1] == "█"


def test_render_sparkline_non_monotonic_no_growing_class() -> None:
    chars, cls = gs.render_sparkline([1, 5, 2, 7, 3, 6, 4, 8])
    assert cls is None


def test_bucket_24h_returns_8_buckets() -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    buckets = gs.bucket_24h(now)
    assert len(buckets) == 8
    assert buckets[-1][1] == now
    assert buckets[0][0] == now - timedelta(hours=24)


# ───────────────────────────── vitals ─────────────────────────────────


def test_vitals_no_runs_shows_em_dash(tmp_db: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        v = gs.build_vitals(conn, now)
    assert v["last_run_iso"] is None
    assert v["last_run_human"] == "—"
    assert v["next_run_human"] == "—"
    assert "no cron runs yet" in v["uptime_recent"]


def test_vitals_with_one_cron_run(tmp_db: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    last_cron = now - timedelta(minutes=2, seconds=14)
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'cron')",
            (last_cron.isoformat(),),
        )
    with db.connect(tmp_db) as conn:
        v = gs.build_vitals(conn, now)
    assert v["last_run_iso"] is not None
    assert "2m 14s ago" in v["last_run_human"]
    assert v["next_run_human"] == "2m 46s"
    assert "1 of 1 ok · 100.0%" in v["uptime_recent"]


def test_vitals_backfill_not_counted_as_cron(tmp_db: Path) -> None:
    """Backfill ok runs do not count toward cron uptime."""
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'backfill')",
            ((now - timedelta(days=1)).isoformat(),),
        )
    with db.connect(tmp_db) as conn:
        v = gs.build_vitals(conn, now)
    assert v["last_run_iso"] is None
    assert "no cron runs yet" in v["uptime_recent"]


# ────────────────────────────── state ────────────────────────────────


def test_state_no_runs_uptime_emdash_days_emdash(tmp_db: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        state = gs.build_state(conn, now)
    assert len(state) == 4
    assert state[3]["figure"] == "—"
    assert state[3]["qual"] == "not yet started"
    assert state[0]["figure"] == "0.0"
    assert state[1]["figure"] == "0"
    assert state[2]["figure"] == "0"
    assert state[2]["unit"] == "/3"


def test_state_days_to_review_uses_anchor_plus_56(tmp_db: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    anchor = now - timedelta(days=1)
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'cron')",
            (anchor.isoformat(),),
        )
    with db.connect(tmp_db) as conn:
        state = gs.build_state(conn, now)
    target = anchor + timedelta(days=56)
    assert state[3]["figure"] == "55"
    assert state[3]["qual"] == f"ends {target.date().isoformat()}"


# ──────────────────────────── pending ─────────────────────────────────


def test_pending_when_class_open_vs_urgent(tmp_repo: Path) -> None:
    (tmp_repo / "pending.md").write_text(
        "---\n\n"
        "- thing: Urgent gate\n  detail: gate detail\n  when: 10d\n  kind: gate\n  promoted: true\n\n"
        "- thing: Open item\n  when: open\n  kind: ops\n"
    )
    rows = gs.build_pending(tmp_repo)
    assert len(rows) == 2
    assert rows[0]["when"] == "10d"
    assert rows[0]["when_class"] == "urgent"
    assert rows[0]["promoted"] is True
    assert rows[1]["when_class"] == "open"
    assert rows[1]["promoted"] is False


# ────────────────────────── accumulating ──────────────────────────────


def test_accumulating_six_rows_in_known_order(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        rows = gs.build_accumulating(conn, tmp_repo, now)
    names = [r["name"] for r in rows]
    assert names == ["bars", "cron runs", "llm calls", "decisions", "letters", "reviews"]


def test_accumulating_zero_delta_marked_zero_class(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        rows = gs.build_accumulating(conn, tmp_repo, now)
    bars_row = next(r for r in rows if r["name"] == "bars")
    assert bars_row["delta"] == "+0"
    assert bars_row["delta_class"] == "zero"


def test_count_future_self_letters_parses_decision_log(tmp_repo: Path) -> None:
    (tmp_repo / "decision-log.md").write_text(
        "## 2026-04-26 — Entry one\n\n"
        "**Letter to future self at the moment of override temptation:**\n\n"
        "body\n\n"
        "## 2026-05-17 — Entry two\n\n"
        "### Future-self letter\n\n"
        "body\n"
    )
    assert gs.count_future_self_letters(tmp_repo) == 2


def test_count_future_self_letters_ignores_convention_prose(tmp_repo: Path) -> None:
    """Convention text referencing the heading style in backticks must not
    inflate the count."""
    (tmp_repo / "decision-log.md").write_text(
        "## Future-self-letter convention\n\n"
        "Hard-rule entries get a `### Future-self letter` section appended.\n"
        "The letter goes inside a `### Future-self letter` heading at the end\n"
        "of the entry it belongs to.\n\n"
        "## 2026-05-17 — Entry one\n\n"
        "**Letter to future self at the moment of override temptation:**\n\n"
        "body\n"
    )
    assert gs.count_future_self_letters(tmp_repo) == 1


def test_count_future_self_letters_counts_blockquoted_letters(tmp_repo: Path) -> None:
    """The convention's worked example sits inside a blockquote — it should
    still count if it's a real letter heading."""
    (tmp_repo / "decision-log.md").write_text(
        "## Convention\n\n"
        "> ### Future-self letter\n>\n"
        "> body of the worked example\n"
    )
    assert gs.count_future_self_letters(tmp_repo) == 1


def test_count_reviews_matches_filename_patterns(tmp_repo: Path) -> None:
    (tmp_repo / "reviews" / "2026-20-friday.md").write_text("x")
    (tmp_repo / "reviews" / "2026-21-prediction.md").write_text("x")
    (tmp_repo / "reviews" / "2026-05-patterns.md").write_text("x")
    (tmp_repo / "reviews" / "random.md").write_text("x")
    assert gs.count_reviews(tmp_repo) == 3


# ─────────────────────────── timetable ────────────────────────────────


def test_timetable_uses_anchor_when_available(tmp_db: Path) -> None:
    anchor = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'cron')",
            (anchor.isoformat(),),
        )
    with db.connect(tmp_db) as conn:
        rows = gs.build_timetable(conn, now)
    assert len(rows) == len(gs.TIMETABLE_OFFSETS)
    assert rows[0]["row_class"] == "now"
    assert rows[0]["tag_class"] == "teal"
    assert "5/17" in rows[0]["when"]
    assert rows[-1]["tag"] == "gate"


def test_timetable_no_anchor_uses_relative_labels(tmp_db: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        rows = gs.build_timetable(conn, now)
    assert rows[0]["when"] == "day 1"
    assert rows[2]["when"] == "+10d"


# ──────────────────────────── kahneman ────────────────────────────────


def test_evaluate_condition_eq_matches() -> None:
    assert gs.evaluate_condition({"day_in_curriculum": {"eq": 1}},
                                 {"day_in_curriculum": 1}) is True
    assert gs.evaluate_condition({"day_in_curriculum": {"eq": 1}},
                                 {"day_in_curriculum": 2}) is False


def test_evaluate_condition_lte_matches() -> None:
    assert gs.evaluate_condition({"days_to_phase_1_review": {"lte": 7}},
                                 {"days_to_phase_1_review": 5}) is True
    assert gs.evaluate_condition({"days_to_phase_1_review": {"lte": 7}},
                                 {"days_to_phase_1_review": 7}) is True
    assert gs.evaluate_condition({"days_to_phase_1_review": {"lte": 7}},
                                 {"days_to_phase_1_review": 8}) is False


def test_evaluate_condition_between() -> None:
    assert gs.evaluate_condition({"day_in_curriculum": {"between": [9, 11]}},
                                 {"day_in_curriculum": 10}) is True
    assert gs.evaluate_condition({"day_in_curriculum": {"between": [9, 11]}},
                                 {"day_in_curriculum": 12}) is False


def test_evaluate_condition_missing_var_fails() -> None:
    assert gs.evaluate_condition({"unknown_var": {"eq": 1}}, {}) is False


def test_kahneman_day_1_trigger_fires(tmp_db: Path, tmp_repo: Path) -> None:
    # Real trigger config from kahneman_triggers.yaml — copy in for hermetic test.
    (tmp_repo / "kahneman_triggers.yaml").write_text(
        "triggers:\n"
        "  - condition:\n"
        "      day_in_curriculum:\n"
        "        eq: 1\n"
        "    trigger: 'day 1 · planning fallacy'\n"
        "    body_html: 'body'\n"
        "    attribution: '— after K&T'\n"
    )
    anchor = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'cron')",
            (anchor.isoformat(),),
        )
    with db.connect(tmp_db) as conn:
        k = gs.build_kahneman(conn, tmp_repo, now)
    assert k is not None
    assert "day 1" in k["trigger"]


def test_kahneman_returns_none_when_nothing_matches(tmp_db: Path, tmp_repo: Path) -> None:
    (tmp_repo / "kahneman_triggers.yaml").write_text(
        "triggers:\n"
        "  - condition:\n"
        "      day_in_curriculum:\n"
        "        eq: 1\n"
        "    trigger: 'day 1'\n"
        "    body_html: ''\n"
        "    attribution: ''\n"
    )
    anchor = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)  # day 17 — no match
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'cron')",
            (anchor.isoformat(),),
        )
    with db.connect(tmp_db) as conn:
        k = gs.build_kahneman(conn, tmp_repo, now)
    assert k is None


def test_kahneman_no_triggers_file_returns_none(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        k = gs.build_kahneman(conn, tmp_repo, now)
    assert k is None


# ────────────────────── end-to-end + idempotency ──────────────────────


def test_generate_idempotent(tmp_db: Path, tmp_repo: Path) -> None:
    """Same now → byte-identical JSON output (required for cron commit-back
    so no-op runs don't produce dirty diffs)."""
    (tmp_repo / "pending.md").write_text("")
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    a = gs.generate(repo_root=tmp_repo, db_path=tmp_db, now=now)
    b = gs.generate(repo_root=tmp_repo, db_path=tmp_db, now=now)
    assert json.dumps(a) == json.dumps(b)


def test_generate_writes_well_formed_json(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    data = gs.generate(repo_root=tmp_repo, db_path=tmp_db, now=now)
    out = tmp_repo / "surface.json"
    gs.write_surface_json(out, data)
    reloaded = json.loads(out.read_text())

    for key in ("generated_at", "masthead", "kahneman", "vitals",
                "state", "pending", "accumulating", "timetable"):
        assert key in reloaded, f"missing key {key}"
    assert len(reloaded["state"]) == 4
    assert len(reloaded["accumulating"]) == 6
    assert reloaded["masthead"] == {"title": "algotrading-paper", "sub": "live"}
    assert reloaded["generated_at"].endswith("Z")
