"""Generate INDEX.md at the repo root.

Scans the repo for the latest of each surface kind, computes the project-
level four-stat band (uptime, trades-this-week, Phase 2 gates passed,
days to phase 1 review), and writes INDEX.md via render.render_index.

Manually runnable for Week 1; the auto-regeneration trigger lands in
Week 2 alongside the cron.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import db
from render import EMDASH, Stat, render_index

REPO_ROOT = Path(__file__).resolve().parent

PHASE_1_REVIEW_DEFAULT = datetime(2026, 6, 28, tzinfo=timezone.utc)
EXPECTED_RUNS_PER_DAY = 288  # one every 5 minutes
UPTIME_GATE_PCT = 95.0
PROMOTION_GATE_TRADES = 100


@dataclass
class SurfaceLatest:
    surface: str
    filename: str | None
    generated: datetime | None
    status: str


def _newest_matching(directory: Path, pattern: re.Pattern[str]) -> Path | None:
    if not directory.exists():
        return None
    candidates = [p for p in directory.iterdir() if p.is_file() and pattern.match(p.name)]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.name, reverse=True)
    return candidates[0]


def _newest_at_root(root: Path, pattern: re.Pattern[str]) -> Path | None:
    candidates = [p for p in root.iterdir() if p.is_file() and pattern.match(p.name)]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.name, reverse=True)
    return candidates[0]


REPLAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-replay\.md$")
WEEKLY_AB_RE = re.compile(r"^\d{4}-\d{2}\.md$")
RECOMMENDATION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
WEEK_STATUS_RE = re.compile(r"^week-\d+-status\.md$")
FRIDAY_REVIEW_RE = re.compile(r"^\d{4}-\d{2}-friday\.md$")
PREDICTION_RE = re.compile(r"^\d{4}-\d{2}-prediction\.md$")
PATTERNS_RE = re.compile(r"^\d{4}-\d{2}-patterns\.md$")


def discover_surfaces(root: Path = REPO_ROOT) -> list[SurfaceLatest]:
    out: list[SurfaceLatest] = []

    replay = _newest_matching(root / "reports", REPLAY_RE)
    out.append(
        SurfaceLatest(
            surface="replay",
            filename=replay.relative_to(root).as_posix() if replay else None,
            generated=_mtime(replay),
            status="ok" if replay else "not yet · Week 1",
        )
    )

    week_status = _newest_at_root(root, WEEK_STATUS_RE)
    out.append(
        SurfaceLatest(
            surface="week status",
            filename=week_status.name if week_status else None,
            generated=_mtime(week_status),
            status="ok" if week_status else "not yet · Week 1",
        )
    )

    weekly_ab = _newest_matching(root / "reports" / "ab", WEEKLY_AB_RE)
    out.append(
        SurfaceLatest(
            surface="weekly A/B",
            filename=weekly_ab.relative_to(root).as_posix() if weekly_ab else None,
            generated=_mtime(weekly_ab),
            status="ok" if weekly_ab else "not yet · Week 4",
        )
    )

    recs = _newest_matching(root / "recommendations", RECOMMENDATION_RE)
    out.append(
        SurfaceLatest(
            surface="recommendations",
            filename=recs.relative_to(root).as_posix() if recs else None,
            generated=_mtime(recs),
            status="ok" if recs else "not yet · Week 4",
        )
    )

    friday = _newest_matching(root / "reviews", FRIDAY_REVIEW_RE)
    out.append(
        SurfaceLatest(
            surface="Friday adversarial review",
            filename=friday.relative_to(root).as_posix() if friday else None,
            generated=_mtime(friday),
            status="ok" if friday else "first run · Week 1",
        )
    )

    prediction = _newest_matching(root / "reviews", PREDICTION_RE)
    out.append(
        SurfaceLatest(
            surface="weekly prediction",
            filename=prediction.relative_to(root).as_posix() if prediction else None,
            generated=_mtime(prediction),
            status="ok" if prediction else "not yet · Week 2",
        )
    )

    patterns = _newest_matching(root / "reviews", PATTERNS_RE)
    out.append(
        SurfaceLatest(
            surface="monthly patterns",
            filename=patterns.relative_to(root).as_posix() if patterns else None,
            generated=_mtime(patterns),
            status="ok" if patterns else "not yet · Month 2",
        )
    )

    return out


def _mtime(path: Path | None) -> datetime | None:
    if path is None:
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def system_uptime_pct(conn: sqlite3.Connection, now: datetime, weeks: int = 4) -> float | None:
    """Approximate uptime as fraction of expected runs that completed with status='ok'.

    Returns None when no runs have happened yet (true em-dash case for Week 1).
    """
    cutoff = now - timedelta(weeks=weeks)
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM runs WHERE started_at >= ?",
        (cutoff.isoformat(),),
    ).fetchone()
    total = int(row["c"]) if row else 0
    if total == 0:
        return None
    ok_row = conn.execute(
        "SELECT COUNT(*) AS c FROM runs WHERE started_at >= ? AND status = 'ok'",
        (cutoff.isoformat(),),
    ).fetchone()
    ok = int(ok_row["c"]) if ok_row else 0
    return (ok / total) * 100.0


def trades_this_week(conn: sqlite3.Connection, now: datetime) -> int:
    iso_year, iso_week, _ = now.isocalendar()
    monday = datetime.fromisocalendar(iso_year, iso_week, 1).replace(tzinfo=timezone.utc)
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM trades WHERE entry_time >= ?",
        (monday.isoformat(),),
    ).fetchone()
    return int(row["c"]) if row else 0


def phase_2_gates_passed(conn: sqlite3.Connection, now: datetime) -> tuple[int, list[bool]]:
    """Check the three gates from PROJECT.md "Phase 2 — Seed real capital":

    gate 1: system uptime ≥ 95% over prior 4 weeks
    gate 2: ≥1 A/B-validated promotion (p<0.05 over 100+ trades) — promoted=1
    gate 3: 30-day paper P&L positive (or written override; we read raw P&L only)
    """
    uptime = system_uptime_pct(conn, now)
    gate1 = uptime is not None and uptime >= UPTIME_GATE_PCT

    promotion_row = conn.execute(
        """
        SELECT COUNT(*) AS c
          FROM recommendations
         WHERE promoted = 1 AND n_trades >= ?
        """,
        (PROMOTION_GATE_TRADES,),
    ).fetchone()
    gate2 = int(promotion_row["c"]) > 0

    cutoff = now - timedelta(days=30)
    pnl_row = conn.execute(
        """
        SELECT COALESCE(SUM(pnl_usd), 0) AS pnl
          FROM trades
         WHERE entry_time >= ? AND status = 'closed' AND pnl_usd IS NOT NULL
        """,
        (cutoff.isoformat(),),
    ).fetchone()
    pnl = float(pnl_row["pnl"]) if pnl_row else 0.0
    gate3 = pnl > 0.0

    gates = [gate1, gate2, gate3]
    return sum(gates), gates


def days_to_phase_1_review(now: datetime, target: datetime = PHASE_1_REVIEW_DEFAULT) -> int:
    delta = target - now
    return max(0, delta.days)


def _format_uptime(pct: float | None) -> str:
    if pct is None:
        return EMDASH
    return f"{pct:.1f}%"


def assemble_index_state(
    *,
    now: datetime,
    db_path: Path | None = None,
    repo_root: Path = REPO_ROOT,
    phase_label: str = "Phase 1",
    week: int | str = 1,
    phase_1_review_target: datetime = PHASE_1_REVIEW_DEFAULT,
) -> dict:
    surfaces = discover_surfaces(repo_root)

    with db.connect(db_path) as conn:
        uptime = system_uptime_pct(conn, now)
        n_trades_week = trades_this_week(conn, now)
        gates_passed, _ = phase_2_gates_passed(conn, now)

    days_left = days_to_phase_1_review(now, phase_1_review_target)

    stats = [
        Stat("System uptime", _format_uptime(uptime), "last 4w"),
        Stat("Trades this week", str(n_trades_week), "paper"),
        Stat("Phase 2 gates", f"{gates_passed} / 3", "passed"),
        Stat("Days to phase 1 review", str(days_left), "calendar"),
    ]

    surface_dicts = [
        {
            "surface": s.surface,
            "filename": s.filename,
            "generated": s.generated,
            "status": s.status,
        }
        for s in surfaces
    ]

    latest_links: list[tuple[str, str]] = []
    replay_link = next((s for s in surfaces if s.surface == "replay" and s.filename), None)
    week_link = next((s for s in surfaces if s.surface == "week status" and s.filename), None)
    if replay_link is not None:
        latest_links.append(("↗ latest replay", replay_link.filename or ""))
    if week_link is not None:
        latest_links.append(("↗ latest week status", week_link.filename or ""))

    reading_order = [
        ("replay", "the latest backtest snapshot — start here on Monday morning."),
        ("status", "week-N-status.md is what was built and what's deferred for the current week."),
        ("recommendations", "candidate variants from the walk-forward tuner — Week 4 onward; review before promoting."),
        ("patterns", "monthly Claude pass over the decision log — Month 2 onward; surfaces drift and contradictions."),
        ("philosophy", "if you're lost in week 4, this is where you go — what success means and what failure looks like."),
    ]

    foundational = [
        ("PROJECT.md", "PROJECT.md"),
        ("philosophy.md", "philosophy.md"),
        ("decision-log.md", "decision-log.md"),
        ("playbook.md", "playbook.md"),
        ("roadmap.md", "roadmap.md"),
        ("week-0-synthesis.md", "week-0-synthesis.md"),
        ("report-format-spec.md", "report-format-spec.md"),
        ("setup.md", "setup.md"),
    ]

    return {
        "phase": phase_label,
        "week": week,
        "timestamp": now,
        "latest_links": latest_links,
        "stats": stats,
        "flags": [],
        "surfaces": surface_dicts,
        "reading_order": reading_order,
        "foundational_docs": foundational,
    }


def write_index(
    out_path: Path | None = None,
    *,
    now: datetime | None = None,
    db_path: Path | None = None,
    repo_root: Path = REPO_ROOT,
    phase_label: str = "Phase 1",
    week: int | str = 1,
    phase_1_review_target: datetime = PHASE_1_REVIEW_DEFAULT,
) -> Path:
    out = out_path or (repo_root / "INDEX.md")
    state = assemble_index_state(
        now=now or datetime.now(timezone.utc),
        db_path=db_path,
        repo_root=repo_root,
        phase_label=phase_label,
        week=week,
        phase_1_review_target=phase_1_review_target,
    )
    out.write_text(render_index(state))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate INDEX.md")
    parser.add_argument("--phase", default="Phase 1")
    parser.add_argument("--week", default="1")
    parser.add_argument("--review-date", default=PHASE_1_REVIEW_DEFAULT.date().isoformat(),
                        help="phase 1 review target date (YYYY-MM-DD)")
    args = parser.parse_args()

    db.migrate()
    target = datetime.fromisoformat(args.review_date).replace(tzinfo=timezone.utc)
    out = write_index(
        phase_label=args.phase, week=args.week, phase_1_review_target=target
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
