"""Generate surface/surface.json — the live PWA's data feed.

Reads the project's SQLite DB plus pending.md and kahneman_triggers.yaml,
writes a single JSON file consumed by /surface/app.js. Runs at the end
of every cron execution alongside render_index.py. Idempotent — same
state in, byte-identical output.

JSON shape:

  {
    "generated_at": "ISO8601",
    "masthead": {"title": "algotrading-paper", "sub": "live"},
    "kahneman": null | {"trigger": str, "body_html": str, "attribution": str},
    "vitals": {
      "last_run_iso": "ISO8601" | null,
      "last_run_human": "Nm Ns ago" | "—",
      "next_run_human": "Nm Ns" | "now" | "—",
      "uptime_recent": "N of M ok · P.P%" | "no runs yet"
    },
    "state": [{name, qual, figure, unit, spark, spark_class}, * 4],
    "pending": [{when, when_class, thing, detail, kind, promoted}, *],
    "accumulating": [{name, count, delta, delta_class, spark, spark_class}, *],
    "timetable": [{when, what, tag, tag_class, row_class}, *]
  }

Sparklines are 8 unicode block characters covering the last 24h in 3h
buckets. Empty series → '▁▁▁▁▁▁▁▁' with spark_class='empty'.
Monotonically increasing → spark_class='growing'.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Make the repo root importable when this script is run via
# `python scripts/generate_surface.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

import db
import render_index
from config import WATCHED_SYMBOLS
from render_index import (
    CURRICULUM_DAYS,
    EXPECTED_RUNS_PER_DAY,
    REPO_ROOT,
    compute_phase_1_review_target,
    get_curriculum_start,
    phase_2_gates_passed,
    read_pending_records,
    read_yaml_md_records,
    runs_in_window,
    system_uptime_pct,
    trades_this_week,
)

# Observed cadence of the GH Actions cron, not the documented one. The
# workflow YAML says */5 * * * * (300s) but GH throttles small repos to
# ~60-min delivery. The surface tracks the actual cadence so the paddle
# ring fills at the right rate and "+Xm overdue" math is honest. See
# decision-log entry 2026-05-18.
CRON_INTERVAL_SECONDS = 60 * 60
SPARKLINE_BUCKETS = 8
EXPECTED_BARS_PER_DAY_PER_SYMBOL = 288  # 24h × 60min / 5-min-bar — Alpaca's bar grid
SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"
EMPTY_SPARKLINE = SPARKLINE_CHARS[0] * SPARKLINE_BUCKETS

# Curriculum timetable — derived from get_curriculum_start. Offsets are
# fixed by PROJECT.md's 8-week curriculum and shouldn't drift independently
# of it. Tag mappings match the surface CSS classes (gate / build / ops).
TIMETABLE_OFFSETS: list[tuple[int, str, str]] = [
    (0, "curriculum day 1", "●"),
    (5, "adversarial review · #1", "ops"),
    (10, "week 2 · strategy-roster review", "gate"),
    (29, "week 4 · walk-forward tuner online", "build"),
    (36, "week 5 · F&G integration", "build"),
    (50, "week 7 · LLM news sentiment", "build"),
    (CURRICULUM_DAYS, "phase 1 review", "gate"),
]


# ───────────────────────── sparkline helpers ──────────────────────────


def render_sparkline(values: list[float]) -> tuple[str, str | None]:
    """Render 8 block chars from `values`. Returns (chars, class).

    class is 'empty' if all zero, 'growing' if monotonically non-decreasing
    with at least one increase, else None.
    """
    if not values:
        return EMPTY_SPARKLINE, "empty"
    if all(v <= 0 for v in values):
        return EMPTY_SPARKLINE, "empty"
    hi = max(values)
    lo = min(values)
    if hi == lo:
        idx = len(SPARKLINE_CHARS) // 2
        chars = SPARKLINE_CHARS[idx] * len(values)
    else:
        chars = "".join(
            SPARKLINE_CHARS[int(round((v - lo) / (hi - lo) * (len(SPARKLINE_CHARS) - 1)))]
            for v in values
        )
    growing = all(values[i] <= values[i + 1] for i in range(len(values) - 1)) and hi > lo
    return chars, ("growing" if growing else None)


def bucket_24h(now: datetime, buckets: int = SPARKLINE_BUCKETS) -> list[tuple[datetime, datetime]]:
    """Return [buckets] (start, end) pairs covering the last 24h, oldest first."""
    bucket_ms = (24 * 3600) // buckets
    out: list[tuple[datetime, datetime]] = []
    for i in range(buckets):
        end = now - timedelta(seconds=bucket_ms * (buckets - 1 - i))
        start = end - timedelta(seconds=bucket_ms)
        out.append((start, end))
    return out


def bucketed_count(
    conn: sqlite3.Connection,
    table: str,
    timestamp_col: str,
    now: datetime,
    where_extra: str = "",
    params_extra: tuple = (),
) -> list[float]:
    out: list[float] = []
    for start, end in bucket_24h(now):
        sql = (
            f"SELECT COUNT(*) AS c FROM {table} "
            f"WHERE {timestamp_col} >= ? AND {timestamp_col} < ?"
            + (f" AND {where_extra}" if where_extra else "")
        )
        row = conn.execute(sql, (start.isoformat(), end.isoformat(), *params_extra)).fetchone()
        out.append(float(row["c"]) if row else 0.0)
    return out


def bucketed_cumulative(
    conn: sqlite3.Connection,
    table: str,
    timestamp_col: str,
    now: datetime,
) -> list[float]:
    """Cumulative row count up to the end of each 24h bucket — useful for
    monotonically-growing series like total bars or total cron runs.
    """
    out: list[float] = []
    for _, end in bucket_24h(now):
        row = conn.execute(
            f"SELECT COUNT(*) AS c FROM {table} WHERE {timestamp_col} < ?",
            (end.isoformat(),),
        ).fetchone()
        out.append(float(row["c"]) if row else 0.0)
    return out


# ───────────────────────── human formatting ───────────────────────────


def humanize_elapsed(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs:02d}s"


def first_ok_run(conn: sqlite3.Connection) -> datetime | None:
    return get_curriculum_start(conn)


def last_run_row(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT started_at, status, kind FROM runs ORDER BY id DESC LIMIT 1"
    ).fetchone()


def last_ok_cron_run(conn: sqlite3.Connection) -> datetime | None:
    row = conn.execute(
        """
        SELECT started_at FROM runs
         WHERE status = 'ok' AND kind = 'cron'
         ORDER BY id DESC LIMIT 1
        """
    ).fetchone()
    if row is None or row["started_at"] is None:
        return None
    ts = datetime.fromisoformat(row["started_at"])
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


# ─────────────────────── section builders ─────────────────────────────


def build_masthead() -> dict:
    return {"title": "algotrading-paper", "sub": "live"}


def build_vitals(conn: sqlite3.Connection, now: datetime) -> dict:
    last_cron = last_ok_cron_run(conn)
    last_run_iso = last_cron.isoformat() if last_cron else None
    if last_cron is None:
        last_human = "—"
        last_human_date = "—"
        next_human = "—"
    else:
        elapsed = (now - last_cron).total_seconds()
        last_human = f"{humanize_elapsed(elapsed)} ago"
        last_human_date = last_cron.strftime("%Y-%m-%d · %H:%M UTC")
        remaining = CRON_INTERVAL_SECONDS - elapsed
        next_human = "now" if remaining <= 0 else humanize_elapsed(remaining)

    ok_recent_row = conn.execute(
        "SELECT COUNT(*) AS c FROM runs WHERE status = 'ok' AND kind = 'cron'"
    ).fetchone()
    total_recent_row = conn.execute(
        "SELECT COUNT(*) AS c FROM runs WHERE kind = 'cron'"
    ).fetchone()
    n_ok = int(ok_recent_row["c"]) if ok_recent_row else 0
    n_total = int(total_recent_row["c"]) if total_recent_row else 0
    if n_total == 0:
        uptime_recent = "no cron runs yet"
    else:
        pct = (n_ok / n_total) * 100.0
        uptime_recent = f"{n_ok} of {n_total} ok · {pct:.1f}%"

    return {
        "last_run_iso": last_run_iso,
        "last_run_human": last_human,
        "last_run_human_date": last_human_date,
        "next_run_human": next_human,
        "uptime_recent": uptime_recent,
        "cron_interval_seconds": CRON_INTERVAL_SECONDS,
    }


def build_state(conn: sqlite3.Connection, now: datetime) -> list[dict]:
    expected_28d = EXPECTED_RUNS_PER_DAY * 28
    n_ok_cron_28d_row = conn.execute(
        """
        SELECT COUNT(*) AS c FROM runs
         WHERE status = 'ok' AND kind = 'cron' AND started_at >= ?
        """,
        ((now - timedelta(days=28)).isoformat(),),
    ).fetchone()
    n_ok_cron_28d = int(n_ok_cron_28d_row["c"]) if n_ok_cron_28d_row else 0
    uptime_pct = min(100.0, (n_ok_cron_28d / expected_28d) * 100.0) if expected_28d else 0.0

    uptime_buckets = []
    for start, end in bucket_24h(now):
        total_row = conn.execute(
            "SELECT COUNT(*) AS c FROM runs WHERE kind = 'cron' AND started_at >= ? AND started_at < ?",
            (start.isoformat(), end.isoformat()),
        ).fetchone()
        ok_row = conn.execute(
            "SELECT COUNT(*) AS c FROM runs WHERE kind = 'cron' AND status = 'ok' AND started_at >= ? AND started_at < ?",
            (start.isoformat(), end.isoformat()),
        ).fetchone()
        total = int(total_row["c"]) if total_row else 0
        ok = int(ok_row["c"]) if ok_row else 0
        uptime_buckets.append(float(ok) if total > 0 else 0.0)
    uptime_spark, uptime_class = render_sparkline(uptime_buckets)

    trades_count = trades_this_week(conn, now)
    trades_buckets = bucketed_count(conn, "trades", "entry_time", now)
    trades_spark, trades_class = render_sparkline(trades_buckets)

    gates_passed, _ = phase_2_gates_passed(conn, now)
    anchor = first_ok_run(conn)
    if anchor is None:
        gates_qual = "curriculum day 1 · open after week 4"
    else:
        day = (now - anchor).days + 1
        gates_qual = f"curriculum day {day} · open after week 4"
    gates_spark, gates_class = EMPTY_SPARKLINE, "empty"

    target = compute_phase_1_review_target(conn)
    if target is None:
        days_value = "—"
        days_qual = "not yet started"
        days_spark = EMPTY_SPARKLINE
        days_class: str | None = "empty"
    else:
        days_left = max(0, (target - now).days)
        days_value = str(days_left)
        days_qual = f"ends {target.date().isoformat()}"
        days_spark = "█▇▆▅▄▃▂▁"  # descending — the diagonal countdown shape
        days_class = None

    return [
        {
            "name": "system uptime",
            "qual": f"{n_ok_cron_28d} of {expected_28d} expected · 28-day window",
            "figure": f"{uptime_pct:.1f}",
            "unit": "%",
            "spark": uptime_spark,
            "spark_class": uptime_class,
        },
        {
            "name": "trades this week",
            "qual": "no strategies registered",
            "figure": str(trades_count),
            "unit": "",
            "spark": trades_spark,
            "spark_class": trades_class,
        },
        {
            "name": "phase 2 gates",
            "qual": gates_qual,
            "figure": str(gates_passed),
            "unit": "/3",
            "spark": gates_spark,
            "spark_class": gates_class,
        },
        {
            "name": "days to phase 1 review",
            "qual": days_qual,
            "figure": days_value,
            "unit": "",
            "spark": days_spark,
            "spark_class": days_class,
        },
    ]


def build_pending(repo_root: Path) -> list[dict]:
    records = render_index.read_pending_records(repo_root)
    out: list[dict] = []
    for rec in records:
        when = (rec.get("when") or "").strip()
        when_class: str | None
        if when == "open":
            when_class = "open"
        elif when and when.endswith("d"):
            when_class = "urgent"
        else:
            when_class = None
        out.append(
            {
                "when": when,
                "when_class": when_class,
                "thing": (rec.get("thing") or "").strip(),
                "detail": (rec.get("detail") or "").strip() or None,
                "kind": (rec.get("kind") or "").strip(),
                "promoted": bool(rec.get("promoted")),
            }
        )
    return out


def count_future_self_letters(repo_root: Path) -> int:
    """Count actual letter headings in decision-log.md.

    A real letter starts with `### Future-self letter` or
    `**Letter to future self` at the start of a line (or after a `> ` block-
    quote marker). Convention prose that references the heading style inside
    backticks is excluded — anchoring to line-start filters those out.
    """
    path = repo_root / "decision-log.md"
    if not path.exists():
        return 0
    text = path.read_text()
    pattern = re.compile(
        r"^(?:>\s+)?(?:###\s+Future-self letter|\*\*Letter to future self)",
        re.IGNORECASE | re.MULTILINE,
    )
    return len(pattern.findall(text))


def count_reviews(repo_root: Path) -> int:
    reviews_dir = repo_root / "reviews"
    if not reviews_dir.exists():
        return 0
    patterns = [
        re.compile(r"^\d{4}-\d{2}-friday\.md$"),
        re.compile(r"^\d{4}-\d{2}-prediction\.md$"),
        re.compile(r"^\d{4}-\d{2}-patterns\.md$"),
    ]
    n = 0
    for p in reviews_dir.iterdir():
        if p.is_file() and any(pat.match(p.name) for pat in patterns):
            n += 1
    return n


def _delta_24h_count(conn: sqlite3.Connection, table: str, ts_col: str, now: datetime) -> int:
    cutoff = now - timedelta(hours=24)
    row = conn.execute(
        f"SELECT COUNT(*) AS c FROM {table} WHERE {ts_col} >= ?",
        (cutoff.isoformat(),),
    ).fetchone()
    return int(row["c"]) if row else 0


def _fmt_delta(n: int) -> tuple[str, str | None]:
    if n == 0:
        return "+0", "zero"
    return f"+{n}", None


def build_accumulating(conn: sqlite3.Connection, repo_root: Path, now: datetime) -> list[dict]:
    rows: list[dict] = []

    bars_total_row = conn.execute("SELECT COUNT(*) AS c FROM bars").fetchone()
    bars_total = int(bars_total_row["c"]) if bars_total_row else 0
    bars_delta = _delta_24h_count(conn, "bars", "fetched_at", now)
    bars_buckets = bucketed_cumulative(conn, "bars", "fetched_at", now)
    bars_spark, bars_class = render_sparkline(bars_buckets)
    delta_str, delta_class = _fmt_delta(bars_delta)
    rows.append({
        "name": "bars", "count": f"{bars_total:,}",
        "delta": delta_str, "delta_class": delta_class,
        "spark": bars_spark, "spark_class": bars_class,
    })

    # Bar coverage — integrity check that catches future data holes.
    # Expected = 24h × 288 bars/symbol × len(WATCHED_SYMBOLS). Actual =
    # bars whose timestamp falls in the last 24h (using bars.timestamp,
    # which is the market time, not fetched_at). Coverage = actual / expected,
    # clamped to 100% (over-fetch impossible since timestamp is the Alpaca
    # bar grid). Sparkline = per-3h-bucket coverage rate.
    n_symbols = len(WATCHED_SYMBOLS)
    expected_24h = EXPECTED_BARS_PER_DAY_PER_SYMBOL * n_symbols
    actual_24h_row = conn.execute(
        "SELECT COUNT(*) AS c FROM bars WHERE timestamp >= ?",
        ((now - timedelta(hours=24)).isoformat(),),
    ).fetchone()
    actual_24h = int(actual_24h_row["c"]) if actual_24h_row else 0
    coverage_pct = min(100.0, (actual_24h / expected_24h) * 100.0) if expected_24h else 0.0

    coverage_buckets: list[float] = []
    expected_per_bucket = (EXPECTED_BARS_PER_DAY_PER_SYMBOL * n_symbols) / SPARKLINE_BUCKETS
    for start, end in bucket_24h(now):
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM bars WHERE timestamp >= ? AND timestamp < ?",
            (start.isoformat(), end.isoformat()),
        ).fetchone()
        n = int(row["c"]) if row else 0
        coverage_buckets.append(min(1.0, n / expected_per_bucket) if expected_per_bucket else 0.0)
    cov_spark, cov_class = render_sparkline(coverage_buckets)
    missing = max(0, expected_24h - actual_24h)
    if missing == 0:
        cov_delta, cov_delta_class = "+0", "zero"
    else:
        cov_delta, cov_delta_class = f"-{missing}", "note"
    rows.append({
        "name": "bar coverage",
        "count": f"{coverage_pct:.0f}%",
        "delta": cov_delta,
        "delta_class": cov_delta_class,
        "spark": cov_spark,
        "spark_class": cov_class,
    })

    cron_total_row = conn.execute(
        "SELECT COUNT(*) AS c FROM runs WHERE kind = 'cron'"
    ).fetchone()
    cron_total = int(cron_total_row["c"]) if cron_total_row else 0
    cron_delta = conn.execute(
        "SELECT COUNT(*) AS c FROM runs WHERE kind = 'cron' AND started_at >= ?",
        ((now - timedelta(hours=24)).isoformat(),),
    ).fetchone()["c"]
    cron_buckets = bucketed_count(
        conn, "runs", "started_at", now, where_extra="kind = 'cron'"
    )
    cron_spark, cron_class = render_sparkline(cron_buckets)
    delta_str, delta_class = _fmt_delta(int(cron_delta))
    rows.append({
        "name": "cron runs", "count": f"{cron_total:,}",
        "delta": delta_str, "delta_class": delta_class,
        "spark": cron_spark, "spark_class": cron_class,
    })

    llm_total_row = conn.execute("SELECT COUNT(*) AS c FROM llm_calls").fetchone()
    llm_total = int(llm_total_row["c"]) if llm_total_row else 0
    llm_delta = _delta_24h_count(conn, "llm_calls", "timestamp", now)
    llm_buckets = bucketed_count(conn, "llm_calls", "timestamp", now)
    llm_spark, llm_class = render_sparkline(llm_buckets)
    delta_str, delta_class = _fmt_delta(llm_delta)
    rows.append({
        "name": "llm calls", "count": f"{llm_total:,}",
        "delta": delta_str, "delta_class": delta_class,
        "spark": llm_spark, "spark_class": llm_class,
    })

    dec_total_row = conn.execute("SELECT COUNT(*) AS c FROM decisions").fetchone()
    dec_total = int(dec_total_row["c"]) if dec_total_row else 0
    dec_delta = _delta_24h_count(conn, "decisions", "decided_at", now)
    dec_buckets = bucketed_count(conn, "decisions", "decided_at", now)
    dec_spark, dec_class = render_sparkline(dec_buckets)
    delta_str, delta_class = _fmt_delta(dec_delta)
    rows.append({
        "name": "decisions", "count": f"{dec_total:,}",
        "delta": delta_str, "delta_class": delta_class,
        "spark": dec_spark, "spark_class": dec_class,
    })

    letters = count_future_self_letters(repo_root)
    rows.append({
        "name": "letters", "count": str(letters),
        "delta": "+0" if letters == 0 else f"+{letters}",
        "delta_class": "zero" if letters == 0 else None,
        "spark": EMPTY_SPARKLINE if letters == 0 else "▁▁▁▁▁▁▁█",
        "spark_class": "empty" if letters == 0 else None,
    })

    reviews = count_reviews(repo_root)
    next_friday_offset = (4 - now.weekday()) % 7  # 4 == Friday
    delta_note = "fri" if reviews == 0 else f"+{reviews}"
    delta_cls = "note" if reviews == 0 else None
    rows.append({
        "name": "reviews",
        "count": "—" if reviews == 0 else str(reviews),
        "delta": delta_note,
        "delta_class": delta_cls,
        "spark": EMPTY_SPARKLINE,
        "spark_class": "empty",
    })

    # Session-marker support: a stable per-row key and the raw numeric value.
    # app.js writes these as data-key / data-value so applySessionMarkers can
    # diff against the operator's previous-visit snapshot. key = name with
    # spaces → underscores (bars, bar_coverage, cron_runs, …); value = the
    # count's digits ("41,871" → "41871", "15%" → "15", "—" → "0").
    for r in rows:
        r["key"] = r["name"].replace(" ", "_")
        digits = re.sub(r"[^0-9]", "", r["count"])
        r["value"] = digits if digits else "0"

    return rows


# ─────────────────────── punch list ───────────────────────────────────


def _punch_item(rec: dict) -> dict:
    when = (rec.get("when") or "").strip()
    if when == "open":
        when_class: str | None = "open"
    elif when.endswith("d"):
        when_class = "urgent"
    else:
        when_class = None
    return {
        "id": f"{(rec.get('kind') or '').strip()}:{(rec.get('thing') or '').strip()}",
        "when": when,
        "when_class": when_class,
        "thing": (rec.get("thing") or "").strip(),
        "detail": (rec.get("detail") or "").strip() or None,
        "kind": (rec.get("kind") or "").strip(),
        "promoted": bool(rec.get("promoted")),
    }


def _when_days(when: str) -> int | None:
    m = re.match(r"^(\d+)d$", when.strip())
    return int(m.group(1)) if m else None


def build_punch_summary(items: list[dict]) -> dict:
    """due_7d / due_14d are cumulative (≤7 ⊂ ≤14). open counts when='open'.
    done_this_week is always 0 here — it's localStorage-only, computed
    client-side from the operator's done-toggles."""
    due_7 = due_14 = open_count = 0
    for it in items:
        days = _when_days(it["when"])
        if days is not None:
            if days <= 7:
                due_7 += 1
            if days <= 14:
                due_14 += 1
        elif it["when"] == "open":
            open_count += 1
    return {"due_7d": due_7, "due_14d": due_14, "open": open_count, "done_this_week": 0}


def build_punch_list(repo_root: Path = REPO_ROOT) -> dict:
    """Punch list JSON: gates + ops from pending.md (by kind), log from
    decision_log_queue.md, build from build_queue.md."""
    pending = read_pending_records(repo_root)
    gates = [_punch_item(r) for r in pending if (r.get("kind") or "").strip() == "gate"]
    ops = [_punch_item(r) for r in pending if (r.get("kind") or "").strip() == "ops"]
    log = [_punch_item(r) for r in read_yaml_md_records(repo_root / "decision_log_queue.md")]
    build = [_punch_item(r) for r in read_yaml_md_records(repo_root / "build_queue.md")]
    all_items = gates + ops + log + build
    return {
        "summary": build_punch_summary(all_items),
        "gates": gates,
        "ops": ops,
        "log": log,
        "build": build,
    }


def write_punch_list_json(out_path: Path, data: dict) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return out_path


_TIMETABLE_DAY_FMT = "%a %-m/%-d"


def _fmt_timetable_date(d: datetime) -> str:
    return d.strftime(_TIMETABLE_DAY_FMT).lower()


def build_timetable(conn: sqlite3.Connection, now: datetime) -> list[dict]:
    anchor = first_ok_run(conn)
    if anchor is None:
        # No anchor yet — show the planned offsets as relative labels.
        return [
            {
                "when": f"+{offset}d" if offset > 0 else "day 1",
                "what": label,
                "tag": tag,
                "tag_class": _tag_class(tag),
                "row_class": None,
            }
            for offset, label, tag in TIMETABLE_OFFSETS
        ]

    rows: list[dict] = []
    today = now.date()
    for offset, label, tag in TIMETABLE_OFFSETS:
        d = (anchor + timedelta(days=offset)).date()
        if today < d:
            row_class = None
            what = label
        elif today == d or (offset == 0 and (today - anchor.date()).days < 7):
            row_class = "now"
            what = f"{label} · now" if "now" not in label else label
        else:
            row_class = None
            what = label
        rows.append({
            "when": _fmt_timetable_date(datetime.combine(d, datetime.min.time())),
            "what": what,
            "tag": tag,
            "tag_class": _tag_class(tag, row_class),
            "row_class": row_class,
        })
    return rows


def _tag_class(tag: str, row_class: str | None = None) -> str | None:
    if row_class == "now":
        return "teal"
    if tag in {"gate", "build", "ops"}:
        return tag
    return None


# ───────────────────────── Kahneman triggers ──────────────────────────


def load_triggers(repo_root: Path) -> list[dict]:
    path = repo_root / "kahneman_triggers.yaml"
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return []
    triggers = data.get("triggers") if isinstance(data, dict) else None
    return triggers or []


def evaluate_condition(condition: dict, state: dict[str, Any]) -> bool:
    """Each condition is {var: {op: value}}. All vars in the condition
    must match for the trigger to fire."""
    for var, cmp in condition.items():
        actual = state.get(var)
        if actual is None:
            return False
        if not isinstance(cmp, dict):
            return False
        for op, expected in cmp.items():
            if op == "eq":
                if actual != expected:
                    return False
            elif op == "lte":
                if actual > expected:
                    return False
            elif op == "gte":
                if actual < expected:
                    return False
            elif op == "between":
                if not (expected[0] <= actual <= expected[1]):
                    return False
            else:
                return False
    return True


def kahneman_state(conn: sqlite3.Connection, repo_root: Path, now: datetime) -> dict:
    anchor = first_ok_run(conn)
    day_in_curriculum = (now - anchor).days + 1 if anchor else None
    target = compute_phase_1_review_target(conn)
    days_to_review = max(0, (target - now).days) if target else None
    weeks = ((day_in_curriculum + 6) // 7) if day_in_curriculum else None

    dlog = repo_root / "decision-log.md"
    days_since_decision: int | None = None
    if dlog.exists():
        for line in dlog.read_text().splitlines():
            m = re.match(r"^##\s+(\d{4}-\d{2}-\d{2})", line)
            if m:
                try:
                    last_decision = datetime.fromisoformat(m.group(1)).replace(
                        tzinfo=timezone.utc
                    )
                    days_since_decision = (now - last_decision).days
                    break
                except ValueError:
                    continue

    return {
        "day_in_curriculum": day_in_curriculum,
        "days_to_phase_1_review": days_to_review,
        "weeks_in_curriculum": weeks,
        "days_since_last_decision": days_since_decision,
    }


def build_kahneman(conn: sqlite3.Connection, repo_root: Path, now: datetime) -> dict | None:
    state = kahneman_state(conn, repo_root, now)
    for trigger in load_triggers(repo_root):
        condition = trigger.get("condition") or {}
        if not condition:
            continue
        if evaluate_condition(condition, state):
            return {
                "trigger": trigger.get("trigger", "").strip(),
                "body_html": trigger.get("body_html", "").strip(),
                "attribution": trigger.get("attribution", "").strip(),
            }
    return None


# ──────────────────────── assemble + write ────────────────────────────


# $/MTok by model prefix — longest match wins. Verified against the
# platform model catalog 2026-07-16. Estimates only; unknown models get
# no cost figure rather than a wrong one.
LLM_PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-sonnet-4-6": (3.00, 15.00),
}


def build_llm(conn: sqlite3.Connection) -> dict:
    """The backbone's own telemetry — calls, tokens, and estimated spend
    from llm_calls, grouped by called_from. The reframe committed to an
    auditable LLM backbone; this is the audit surfaced."""
    rows = conn.execute(
        """
        SELECT called_from, model, COUNT(*) AS calls,
               COALESCE(SUM(prompt_tokens), 0) AS in_tok,
               COALESCE(SUM(completion_tokens), 0) AS out_tok
          FROM llm_calls GROUP BY called_from, model
        """
    ).fetchall()
    by_caller: list[dict] = []
    total_calls = 0
    total_cost = 0.0
    cost_known = True
    for r in rows:
        cost = None
        for prefix, (p_in, p_out) in LLM_PRICES_PER_MTOK.items():
            if str(r["model"]).startswith(prefix):
                cost = r["in_tok"] / 1e6 * p_in + r["out_tok"] / 1e6 * p_out
                break
        if cost is None:
            cost_known = False
        else:
            total_cost += cost
        total_calls += r["calls"]
        by_caller.append({
            "called_from": r["called_from"],
            "model": r["model"],
            "calls": r["calls"],
            "tokens": r["in_tok"] + r["out_tok"],
            "cost_usd": round(cost, 4) if cost is not None else None,
        })
    return {
        "total_calls": total_calls,
        "total_cost_usd": round(total_cost, 4) if by_caller and cost_known else (
            round(total_cost, 4) if total_cost > 0 else None
        ),
        "by_caller": sorted(by_caller, key=lambda x: -x["calls"]),
    }


def generate(
    repo_root: Path = REPO_ROOT,
    db_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(timezone.utc)
    with db.connect(db_path) as conn:
        return {
            "generated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "masthead": build_masthead(),
            "kahneman": build_kahneman(conn, repo_root, now),
            "vitals": build_vitals(conn, now),
            "state": build_state(conn, now),
            "pending": build_pending(repo_root),
            "accumulating": build_accumulating(conn, repo_root, now),
            "timetable": build_timetable(conn, now),
            "llm": build_llm(conn),
        }


def write_surface_json(out_path: Path, data: dict) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return out_path


# ──────────────────── cache-busting for app.js ───────────────────────


_APP_JS_VERSION_RE = re.compile(r'(src="\./app\.js)(?:\?v=[^"]*)?(")')


def _hash_app_js(app_js: Path, length: int = 12) -> str:
    """First N hex chars of SHA-256(app.js) — enough cache-bust entropy
    without bloating the HTML. 12 chars = 48 bits ≈ 1 in 281 trillion
    collision probability."""
    return hashlib.sha256(app_js.read_bytes()).hexdigest()[:length]


def update_index_html_version(surface_dir: Path = REPO_ROOT / "surface") -> bool:
    """Rewrite surface/index.html so the <script src="./app.js?v=...">
    query string reflects the current hash of app.js.

    Browsers cache assets aggressively by URL; changing the URL when
    content changes is how every modern site avoids stale-JS bugs
    without user intervention. GitHub Pages doesn't allow custom
    Cache-Control headers, so URL versioning is the only lever.

    Returns True if index.html was rewritten, False if no-op (hash
    already current). Idempotent — calling repeatedly with no
    underlying change leaves the file alone (no dirty diff for the
    cron commit-back).
    """
    index = surface_dir / "index.html"
    app_js = surface_dir / "app.js"
    if not index.exists() or not app_js.exists():
        return False

    new_hash = _hash_app_js(app_js)
    html = index.read_text()
    new_html = _APP_JS_VERSION_RE.sub(rf'\1?v={new_hash}\2', html)
    if new_html == html:
        return False
    index.write_text(new_html)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate surface/surface.json + punch_list.json")
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "surface" / "surface.json")
    parser.add_argument("--punch-out", type=Path,
                        default=REPO_ROOT / "surface" / "punch_list.json")
    args = parser.parse_args()

    db.migrate()
    data = generate()
    out = write_surface_json(args.out, data)

    punch = build_punch_list()
    punch_out = write_punch_list_json(args.punch_out, punch)

    rewrote_index = update_index_html_version()
    s = punch["summary"]
    msg = (
        f"wrote {out} — {data['vitals']['uptime_recent']}\n"
        f"wrote {punch_out} — due≤7d {s['due_7d']} · due≤14d {s['due_14d']} · open {s['open']}"
    )
    if rewrote_index:
        msg += "\nrewrote index.html (app.js hash changed)"
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
