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
    assert v["last_run_human_date"] == "—"
    assert v["next_run_human"] == "—"
    assert "no cron runs yet" in v["uptime_recent"]


def test_vitals_includes_cron_interval_seconds(tmp_db: Path) -> None:
    """The surface needs to know the actual cron cadence so the ring arc
    fills over the right window. Hardcoded to GH's observed ~60-min
    cadence, not the documented 5-min schedule. See decision-log 2026-05-18."""
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        v = gs.build_vitals(conn, now)
    assert v["cron_interval_seconds"] == gs.CRON_INTERVAL_SECONDS
    assert v["cron_interval_seconds"] == 3600


def test_vitals_human_date_formatted_for_last_run(tmp_db: Path) -> None:
    now = datetime(2026, 5, 17, 19, 24, tzinfo=timezone.utc)
    last_cron = datetime(2026, 5, 17, 19, 22, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', 'cron')",
            (last_cron.isoformat(),),
        )
    with db.connect(tmp_db) as conn:
        v = gs.build_vitals(conn, now)
    assert v["last_run_human_date"] == "2026-05-17 · 19:22 UTC"


def test_vitals_with_one_cron_run(tmp_db: Path) -> None:
    """next_run_human is computed against CRON_INTERVAL_SECONDS (3600s after
    the 2026-05-18 recalibration to GH's observed cadence)."""
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
    # 3600s - (2*60 + 14) = 3466s = 57m 46s
    assert v["next_run_human"] == "57m 46s"
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


def test_accumulating_seven_rows_in_known_order(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        rows = gs.build_accumulating(conn, tmp_repo, now)
    names = [r["name"] for r in rows]
    assert names == [
        "bars", "bar coverage", "cron runs", "llm calls",
        "decisions", "letters", "reviews",
    ]


def test_bar_coverage_zero_when_no_bars(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        rows = gs.build_accumulating(conn, tmp_repo, now)
    cov = next(r for r in rows if r["name"] == "bar coverage")
    assert cov["count"] == "0%"
    assert cov["delta_class"] == "note"
    expected = gs.EXPECTED_BARS_PER_DAY_PER_SYMBOL * len(gs.WATCHED_SYMBOLS) \
        if hasattr(gs, "WATCHED_SYMBOLS") else 288 * 5
    assert cov["delta"] == f"-{expected}"


def test_bar_coverage_100pct_when_bars_complete(tmp_db: Path, tmp_repo: Path) -> None:
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    n_symbols = len(gs.WATCHED_SYMBOLS)
    expected = gs.EXPECTED_BARS_PER_DAY_PER_SYMBOL * n_symbols
    with db.connect(tmp_db) as conn:
        for i in range(expected):
            symbol = gs.WATCHED_SYMBOLS[i % n_symbols]
            ts = (now - timedelta(minutes=5 * (i // n_symbols + 1))).isoformat()
            conn.execute(
                """INSERT OR IGNORE INTO bars
                   (symbol, timestamp, open, high, low, close, volume, fetched_at)
                   VALUES (?, ?, 1, 1, 1, 1, 1, ?)""",
                (symbol, ts, now.isoformat()),
            )
    with db.connect(tmp_db) as conn:
        rows = gs.build_accumulating(conn, tmp_repo, now)
    cov = next(r for r in rows if r["name"] == "bar coverage")
    assert cov["count"] == "100%"
    assert cov["delta"] == "+0"
    assert cov["delta_class"] == "zero"


def test_accumulating_rows_have_key_and_value(tmp_db: Path, tmp_repo: Path) -> None:
    """Each accumulating row carries a stable session-marker key + raw value."""
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        rows = gs.build_accumulating(conn, tmp_repo, now)
    keys = {r["key"] for r in rows}
    assert {"bars", "bar_coverage", "cron_runs", "llm_calls", "decisions",
            "letters", "reviews"} == keys
    # value is digits-only; reviews count "—" → "0"
    reviews = next(r for r in rows if r["key"] == "reviews")
    assert reviews["value"] == "0"
    bars = next(r for r in rows if r["key"] == "bars")
    assert bars["value"].isdigit()


def test_accumulating_value_strips_formatting(tmp_db: Path, tmp_repo: Path) -> None:
    """'15%' → '15', commas stripped from large counts."""
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        rows = gs.build_accumulating(conn, tmp_repo, now)
    cov = next(r for r in rows if r["key"] == "bar_coverage")
    # count is like "0%" with no bars; value is the digits only
    assert "%" not in cov["value"]
    assert cov["value"].isdigit()


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


# ──────────────────────── cache-busting ───────────────────────────────


def test_hash_app_js_stable_for_same_content(tmp_path: Path) -> None:
    app_js = tmp_path / "app.js"
    app_js.write_text("console.log('v1');\n")
    h1 = gs._hash_app_js(app_js)
    h2 = gs._hash_app_js(app_js)
    assert h1 == h2
    assert len(h1) == 12
    assert all(c in "0123456789abcdef" for c in h1)


def test_hash_app_js_changes_with_content(tmp_path: Path) -> None:
    app_js = tmp_path / "app.js"
    app_js.write_text("console.log('v1');\n")
    h1 = gs._hash_app_js(app_js)
    app_js.write_text("console.log('v2');\n")
    h2 = gs._hash_app_js(app_js)
    assert h1 != h2


def test_update_index_html_version_rewrites_when_hash_differs(tmp_path: Path) -> None:
    surface = tmp_path / "surface"
    surface.mkdir()
    (surface / "app.js").write_text("console.log('initial');\n")
    (surface / "index.html").write_text(
        '<html><body>\n<script src="./app.js?v=stale"></script>\n</body></html>\n'
    )

    rewrote = gs.update_index_html_version(surface)
    assert rewrote is True

    expected_hash = gs._hash_app_js(surface / "app.js")
    new_html = (surface / "index.html").read_text()
    assert f'src="./app.js?v={expected_hash}"' in new_html
    assert "?v=stale" not in new_html


def test_update_index_html_version_no_op_when_hash_matches(tmp_path: Path) -> None:
    surface = tmp_path / "surface"
    surface.mkdir()
    (surface / "app.js").write_text("console.log('initial');\n")
    h = gs._hash_app_js(surface / "app.js")
    (surface / "index.html").write_text(
        f'<html><body>\n<script src="./app.js?v={h}"></script>\n</body></html>\n'
    )
    mtime_before = (surface / "index.html").stat().st_mtime_ns

    rewrote = gs.update_index_html_version(surface)
    assert rewrote is False
    mtime_after = (surface / "index.html").stat().st_mtime_ns
    assert mtime_before == mtime_after, "no-op must not touch the file"


def test_update_index_html_version_inserts_when_missing(tmp_path: Path) -> None:
    """If index.html has <script src='./app.js'> with no version, insert one."""
    surface = tmp_path / "surface"
    surface.mkdir()
    (surface / "app.js").write_text("console.log('x');\n")
    (surface / "index.html").write_text(
        '<html><body>\n<script src="./app.js"></script>\n</body></html>\n'
    )

    rewrote = gs.update_index_html_version(surface)
    assert rewrote is True
    h = gs._hash_app_js(surface / "app.js")
    assert f'src="./app.js?v={h}"' in (surface / "index.html").read_text()


def test_update_index_html_version_missing_files_no_op(tmp_path: Path) -> None:
    surface = tmp_path / "surface"
    surface.mkdir()
    assert gs.update_index_html_version(surface) is False

    (surface / "index.html").write_text("<html></html>\n")
    assert gs.update_index_html_version(surface) is False


def test_update_index_html_version_does_not_match_other_scripts(tmp_path: Path) -> None:
    """The version-rewrite regex is anchored to './app.js' specifically — must
    not touch other script tags or random app.js mentions in prose."""
    surface = tmp_path / "surface"
    surface.mkdir()
    (surface / "app.js").write_text("x\n")
    html_before = (
        '<html><body>\n'
        '<script src="./vendor/jquery.js?v=oldjq"></script>\n'
        '<script src="./app.js?v=dev"></script>\n'
        '<!-- comment mentions app.js?v=fake but should stay -->\n'
        '</body></html>\n'
    )
    (surface / "index.html").write_text(html_before)
    gs.update_index_html_version(surface)
    html_after = (surface / "index.html").read_text()
    assert "vendor/jquery.js?v=oldjq" in html_after, "other scripts untouched"
    assert "app.js?v=fake" in html_after, "prose mentions of app.js?v=fake untouched"
    h = gs._hash_app_js(surface / "app.js")
    assert f'src="./app.js?v={h}"' in html_after


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
    assert len(reloaded["accumulating"]) == 7
    assert reloaded["masthead"] == {"title": "algotrading-paper", "sub": "live"}
    assert reloaded["generated_at"].endswith("Z")


# ─────────────────────────── punch list ───────────────────────────────


def _write_pending(repo: Path, body: str) -> None:
    (repo / "pending.md").write_text("# Pending\n\n---\n\n" + body)


def test_punch_item_when_class_derivation() -> None:
    assert gs._punch_item({"thing": "x", "when": "10d", "kind": "gate"})["when_class"] == "urgent"
    assert gs._punch_item({"thing": "x", "when": "open", "kind": "ops"})["when_class"] == "open"
    assert gs._punch_item({"thing": "x", "when": "", "kind": "log"})["when_class"] is None


def test_punch_item_stable_id() -> None:
    it = gs._punch_item({"thing": "Week 2 review", "kind": "gate"})
    assert it["id"] == "gate:Week 2 review"


def test_build_punch_summary_cumulative_bands() -> None:
    items = [
        {"when": "3d"}, {"when": "10d"}, {"when": "10d"},
        {"when": "open"}, {"when": "open"},
    ]
    s = gs.build_punch_summary(items)
    assert s["due_7d"] == 1       # only 3d
    assert s["due_14d"] == 3      # 3d + 10d + 10d (cumulative)
    assert s["open"] == 2
    assert s["done_this_week"] == 0


def test_build_punch_list_sections_from_sources(tmp_repo: Path) -> None:
    _write_pending(tmp_repo,
        "- thing: Roster review\n  when: 10d\n  kind: gate\n  promoted: true\n\n"
        "- thing: Scheduler decision\n  when: 10d\n  kind: gate\n\n"
        "- thing: Friday review\n  when: 5d\n  kind: ops\n\n"
        "- thing: Future-self letters\n  when: open\n  kind: ops\n")
    (tmp_repo / "decision_log_queue.md").write_text(
        "# q\n\n---\n\n- thing: Shadow-signal schema\n  when: open\n  kind: log\n")
    (tmp_repo / "build_queue.md").write_text(
        "# q\n\n---\n\n- thing: Cron-variance row\n  when: open\n  kind: build\n")

    pl = gs.build_punch_list(tmp_repo)
    assert [i["thing"] for i in pl["gates"]] == ["Roster review", "Scheduler decision"]
    assert [i["thing"] for i in pl["ops"]] == ["Friday review", "Future-self letters"]
    assert [i["thing"] for i in pl["log"]] == ["Shadow-signal schema"]
    assert [i["thing"] for i in pl["build"]] == ["Cron-variance row"]
    assert pl["gates"][0]["promoted"] is True
    assert pl["summary"]["due_7d"] == 1     # Friday 5d
    assert pl["summary"]["due_14d"] == 3    # 5d + 10d + 10d
    assert pl["summary"]["open"] == 3       # Future-self + Shadow-signal + Cron-variance


def test_build_punch_list_empty_sources(tmp_repo: Path) -> None:
    pl = gs.build_punch_list(tmp_repo)
    assert pl["gates"] == []
    assert pl["ops"] == []
    assert pl["log"] == []
    assert pl["build"] == []
    assert pl["summary"] == {"due_7d": 0, "due_14d": 0, "open": 0, "done_this_week": 0}


def test_write_punch_list_json_round_trip(tmp_repo: Path) -> None:
    _write_pending(tmp_repo, "- thing: G\n  when: 10d\n  kind: gate\n")
    pl = gs.build_punch_list(tmp_repo)
    out = tmp_repo / "punch_list.json"
    gs.write_punch_list_json(out, pl)
    reloaded = json.loads(out.read_text())
    for key in ("summary", "gates", "ops", "log", "build"):
        assert key in reloaded
    assert reloaded["gates"][0]["thing"] == "G"


# --- LLM telemetry (build_llm) ----------------------------------------------


def test_build_llm_empty_table(tmp_db: Path) -> None:
    with db.connect(tmp_db) as conn:
        llm = gs.build_llm(conn)
    assert llm["total_calls"] == 0
    assert llm["by_caller"] == []


def test_build_llm_groups_and_prices(tmp_db: Path) -> None:
    with db.connect(tmp_db) as conn:
        for i, (caller, model, p_in, p_out) in enumerate([
            ("adversarial_cron", "claude-haiku-4-5", 1000, 500),
            ("adversarial_cron", "claude-haiku-4-5", 1000, 500),
            ("friday_bear_case", "claude-opus-4-8", 4000, 2000),
            ("mystery", "some-unknown-model", 100, 100),
        ]):
            conn.execute(
                "INSERT INTO llm_calls (timestamp, prompt_hash, prompt_full, response_full,"
                " model, latency_ms, prompt_tokens, completion_tokens, total_tokens, called_from)"
                " VALUES (?, ?, 'p', 'r', ?, 100, ?, ?, ?, ?)",
                (f"2026-07-16T0{i}:00:00+00:00", f"hash{i}", model, p_in, p_out,
                 p_in + p_out, caller),
            )
        llm = gs.build_llm(conn)

    assert llm["total_calls"] == 4
    by_caller = {c["called_from"]: c for c in llm["by_caller"]}
    assert by_caller["adversarial_cron"]["calls"] == 2
    assert by_caller["adversarial_cron"]["tokens"] == 3000
    # haiku: 2000 in * $1/M + 1000 out * $5/M = 0.002 + 0.005 = 0.007
    assert by_caller["adversarial_cron"]["cost_usd"] == pytest.approx(0.007)
    # opus: 4000 * 5/M + 2000 * 25/M = 0.02 + 0.05 = 0.07
    assert by_caller["friday_bear_case"]["cost_usd"] == pytest.approx(0.07)
    # unknown model: no cost figure rather than a wrong one
    assert by_caller["mystery"]["cost_usd"] is None


def test_surface_json_includes_llm_block(tmp_db: Path, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    data = gs.generate(repo_root=repo, db_path=tmp_db)
    assert "llm" in data
    assert data["llm"]["total_calls"] == 0


# --- Scoreboard --------------------------------------------------------------


def test_build_scoreboard_empty(tmp_db: Path) -> None:
    with db.connect(tmp_db) as conn:
        sb = gs.build_scoreboard(conn)
    assert sb["variants"] == []
    assert sb["total"]["placed"] == 0


def test_build_scoreboard_ranks_by_closed_pnl(tmp_db: Path) -> None:
    with db.connect(tmp_db) as conn:
        rows = [
            # (variant, status, pnl)
            ("null_baseline", "closed", -1.50),
            ("null_baseline", "closed", 2.00),
            ("null_baseline", "open", None),
            ("cand_a", "closed", 10.00),
            ("cand_a", "closed", -2.00),
        ]
        for i, (variant, status, pnl) in enumerate(rows):
            conn.execute(
                "INSERT INTO signals (symbol, variant_name, strategy, side, bar_timestamp,"
                " price_at_signal, reasoning_json, emitted_at)"
                " VALUES ('BTC/USD', ?, 's', 'buy', ?, 100.0, '{}', 't')",
                (variant, f"2026-07-16T00:{i:02d}:00+00:00"),
            )
            conn.execute(
                "INSERT INTO trades (signal_id, variant_name, symbol, side, qty, entry_price,"
                " entry_time, pnl_usd, is_real_money, status)"
                " VALUES (?, ?, 'BTC/USD', 'buy', 1.0, 100.0, ?, ?, 0, ?)",
                (i + 1, variant, f"2026-07-16T00:{i:02d}:00+00:00", pnl, status),
            )
        sb = gs.build_scoreboard(conn)

    assert [v["name"] for v in sb["variants"]] == ["cand_a", "null_baseline"]
    cand = sb["variants"][0]
    assert cand["placed"] == 2 and cand["closed"] == 2 and cand["open"] == 0
    assert cand["pnl_usd"] == pytest.approx(8.0)
    assert cand["win_rate"] == pytest.approx(0.5)
    null = sb["variants"][1]
    assert null["open"] == 1
    assert null["pnl_usd"] == pytest.approx(0.5)
    assert sb["total"]["placed"] == 5
    assert sb["total"]["open"] == 1
    assert sb["total"]["pnl_usd"] == pytest.approx(8.5)


def test_scoreboard_in_surface_json(tmp_db: Path, tmp_path: Path) -> None:
    repo = tmp_path / "repo2"
    repo.mkdir()
    data = gs.generate(repo_root=repo, db_path=tmp_db)
    assert "scoreboard" in data


def test_topline_shape_and_guards(tmp_db):
    """The topline must always produce bindable strings — even on an
    empty database with no foundry files (guards, not crashes)."""
    import db as db_mod
    from scripts.generate_surface import build_topline
    from datetime import datetime, timezone
    from pathlib import Path

    now = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
    with db_mod.connect(tmp_db) as conn:
        t = build_topline(conn, Path("/nonexistent"), now)
    for key in ("now_line", "pipeline_line", "health_line", "tile_pnl",
                "tile_best", "tile_ab", "tile_research", "tile_days"):
        assert isinstance(t[key], str) and t[key], key
    assert t["health_warn"] in (True, False)
