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
from render_index import (
    CURRICULUM_DAYS,
    EXPECTED_RUNS_PER_DAY,
    REPO_ROOT,
    compute_phase_1_review_target,
    get_curriculum_start,
    phase_2_gates_passed,
    runs_in_window,
    system_uptime_pct,
    trades_this_week,
)

CRON_INTERVAL_SECONDS = 5 * 60
SPARKLINE_BUCKETS = 8
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
        next_human = "—"
    else:
        elapsed = (now - last_cron).total_seconds()
        last_human = f"{humanize_elapsed(elapsed)} ago"
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
        "next_run_human": next_human,
        "uptime_recent": uptime_recent,
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

    return rows


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
        }


def write_surface_json(out_path: Path, data: dict) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate surface/surface.json")
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "surface" / "surface.json")
    args = parser.parse_args()

    db.migrate()
    data = generate()
    out = write_surface_json(args.out, data)
    print(f"wrote {out} — {data['vitals']['uptime_recent']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
