"""Nightly adversarial skeptic — the always-on drift check.

The weekly Friday review (reviews/templates/friday-bear-case.md) is the
full 4G bear case. This is its lightweight nightly sibling: read the
last 7 runs rows and the open pending.md items, ask the skeptic what the
operator is avoiding or letting slide, and leave a dated note. It exists
because the W21 review's sharpest finding was structural: disciplines
that depend on the operator showing up don't run when the operator
doesn't show up (the 2026-05-22 Friday review was skipped; then a 47-day
gap). This one runs from cron on the VPS whether anyone shows up or not.

Output contract:
  - Full skeptic text  -> reviews/nightly/YYYY-MM-DD.md (verbatim, unedited)
  - pending.md         -> ONE item ("Nightly skeptic · YYYY-MM-DD"), the
    prior night's item replaced, not accumulated. pending.md is strict
    YAML-after---separator read by render_index.py and
    generate_surface.py — raw prose appended there would silently break
    the parse and blank the live surface's pending section, so the full
    text goes to reviews/nightly/ and pending.md gets a valid pointer
    record only.

Every call goes through claude_client.ClaudeClient, so it lands in
llm_calls (called_from='adversarial_cron') and inherits the distillation
base system prompt; the skeptic instructions layer on top.

Runs on the VPS (single-writer discipline: the llm_calls row is a
trader.db write). See vps/cron-skeptic.sh and vps/crontab.txt.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import db
from render_index import read_yaml_md_records

REPO_ROOT = Path(__file__).resolve().parent

NIGHTLY_ITEM_PREFIX = "Nightly skeptic · "

SKEPTIC_SYSTEM = """\
You are the nightly adversarial skeptic for an algorithmic paper-trading
project. Argue the bear case only — no hedging, no "on the other hand",
no softening to be polite. The operator has other conversations for the
bull case.

You see two things: the last 7 pipeline runs, and the operator's open
pending items. Your job is drift detection, not analysis: what is being
avoided, what has been open too long, what does the runs data contradict
about the project's self-narrative? If an item has clearly been pending
longer than its own deadline implies, say so bluntly. If the pipeline
runs show data but no decisions, name the gap.

Three short paragraphs maximum. End with the single most urgent thing
the operator should do tomorrow, on one line prefixed 'TOMORROW: '.\
"""


def read_recent_runs(conn: sqlite3.Connection, limit: int = 7) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, started_at, finished_at, status, bars_added, kind
          FROM runs
         ORDER BY id DESC
         LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def build_prompt(runs: list[dict], pending: list[dict], now: datetime) -> str:
    runs_lines = [
        f"  run {r['id']}: {r['started_at']} status={r['status']} "
        f"bars_added={r['bars_added']} kind={r['kind']}"
        for r in runs
    ] or ["  (no runs recorded)"]

    pending_lines = [
        f"  - [{(r.get('kind') or '?')}] {r['thing']}"
        + (f" — {r['detail']}" if r.get("detail") else "")
        + (f" (when: {r['when']})" if r.get("when") else "")
        for r in pending
    ] or ["  (pending list is empty)"]

    return (
        f"Nightly skeptic run, {now.date().isoformat()}.\n\n"
        f"Last {len(runs)} pipeline runs (newest first):\n"
        + "\n".join(runs_lines)
        + "\n\nOpen pending items (operator-managed):\n"
        + "\n".join(pending_lines)
        + "\n\nBear case, please."
    )


def _replace_nightly_item(pending_path: Path, date_str: str, detail: str) -> None:
    """Append today's nightly-skeptic pointer, replacing any prior one.

    Exactly one nightly item lives in pending.md at a time — accumulating
    one per night would silt up the punch list. The item is written as a
    plain YAML record so read_yaml_md_records keeps parsing the file.
    """
    text = pending_path.read_text()
    lines = text.splitlines(keepends=True)

    # Drop a previous nightly block: the "- thing:" line holding the
    # prefix plus its following indented lines.
    out: list[str] = []
    skipping = False
    for line in lines:
        if NIGHTLY_ITEM_PREFIX in line and line.lstrip().startswith("- thing:"):
            skipping = True
            continue
        if skipping:
            if line.strip() and not line.startswith((" ", "\t")):
                skipping = False
            else:
                continue
        out.append(line)

    # YAML-quote the detail; keep it one line.
    safe_detail = detail.replace('"', "'").strip()
    block = (
        f'\n- thing: "{NIGHTLY_ITEM_PREFIX}{date_str}"\n'
        f'  detail: "{safe_detail}"\n'
        f"  when: open\n"
        f"  kind: ops\n"
    )
    pending_path.write_text("".join(out).rstrip("\n") + "\n" + block)


def run_nightly(
    client=None,
    db_path: Path | None = None,
    repo_root: Path = REPO_ROOT,
    now: datetime | None = None,
) -> Path:
    """Run the skeptic once. Returns the path of the written review file.

    `client` is injectable for tests (anything with a .complete(prompt,
    called_from, system=...) returning an object with .text). A real run
    constructs ClaudeClient, which needs ANTHROPIC_API_KEY.
    """
    ts = now or datetime.now(timezone.utc)
    date_str = ts.date().isoformat()

    with db.connect(db_path) as conn:
        runs = read_recent_runs(conn)
    pending_path = repo_root / "pending.md"
    pending = read_yaml_md_records(pending_path)
    # Don't feed yesterday's skeptic item back to the skeptic.
    pending = [r for r in pending if not str(r.get("thing", "")).startswith(NIGHTLY_ITEM_PREFIX)]

    prompt = build_prompt(runs, pending, ts)

    if client is None:
        from claude_client import ClaudeClient, model_for_role

        client = ClaudeClient(model=model_for_role("nightly"), db_path=db_path)
    result = client.complete(prompt, called_from="adversarial_cron", system=SKEPTIC_SYSTEM)

    out_dir = repo_root / "reviews" / "nightly"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date_str}.md"
    out_path.write_text(
        f"# Nightly skeptic — {date_str}\n\n"
        f"model {result.model} · called_from adversarial_cron · logged to llm_calls\n\n"
        f"---\n\n{result.text}\n"
    )

    # First line of the response as the pending.md detail (truncated).
    first_line = next((ln.strip() for ln in result.text.splitlines() if ln.strip()), "")
    if len(first_line) > 100:
        first_line = first_line[:97] + "..."
    _replace_nightly_item(pending_path, date_str, first_line or "see reviews/nightly/")

    return out_path


def _extract_template_prompt(template_path: Path) -> str:
    """The 4G prompt lives in the template file's fenced code block —
    the file is the spec, so read it rather than duplicating it here."""
    text = template_path.read_text()
    start = text.index("```\n") + 4
    end = text.index("\n```", start)
    return text[start:end]


def _gather_friday_inputs(
    conn: sqlite3.Connection, week_start: datetime, repo_root: Path
) -> dict[str, str]:
    since = week_start.isoformat()

    trades = conn.execute(
        """
        SELECT variant_name, symbol, side, entry_price, exit_price,
               exit_reason, pnl_usd, pnl_pct, entry_time, exit_time
          FROM trades WHERE entry_time >= ? ORDER BY entry_time DESC
        """,
        (since,),
    ).fetchall()
    trade_lines = [
        "  " + " | ".join(str(r[k]) for k in r.keys()) for r in trades
    ] or ["  (no trades this week — zero rows)"]

    runs = conn.execute(
        "SELECT status, COUNT(*) AS n FROM runs WHERE started_at >= ? GROUP BY status",
        (since,),
    ).fetchall()
    runs_lines = [f"  {r['status']}: {r['n']}" for r in runs] or ["  (no runs)"]

    decisions = conn.execute(
        "SELECT action, COUNT(*) AS n FROM decisions WHERE decided_at >= ? GROUP BY action",
        (since,),
    ).fetchall()
    decision_lines = [f"  {r['action']}: {r['n']}" for r in decisions] or [
        "  (no decisions — execution layer has never run live)"
    ]
    reasons = conn.execute(
        """
        SELECT DISTINCT reason FROM decisions
         WHERE decided_at >= ? AND action = 'rejected' LIMIT 5
        """,
        (since,),
    ).fetchall()
    if reasons:
        decision_lines.append("  top rejection reasons:")
        decision_lines.extend(f"    - {r['reason']}" for r in reasons)

    # Promotions: none can exist until compare.py + the promotion flow are
    # built (recommendations table is empty), so report honestly.
    n_promoted = conn.execute(
        "SELECT COUNT(*) AS n FROM recommendations WHERE promoted = 1"
    ).fetchone()["n"]
    promotions = (
        f"{n_promoted} promoted recommendations exist"
        if n_promoted
        else "none — no promotion machinery has run yet"
    )

    # Prior bear case: the newest reviews/*-friday.md
    prior_files = sorted((repo_root / "reviews").glob("*-friday.md"))
    if prior_files:
        prior = prior_files[-1].read_text()
    else:
        prior = "none — first Friday review"

    return {
        "TRADE_HISTORY_TABLE": "\n".join(trade_lines),
        "RUNS_LOG_SUMMARY": "\n".join(runs_lines),
        "DECISIONS_TABLE": "\n".join(decision_lines),
        "PROMOTIONS_THIS_WEEK": promotions,
        "PRIOR_BEAR_CASE": prior,
    }


def run_friday(
    client=None,
    db_path: Path | None = None,
    repo_root: Path = REPO_ROOT,
    now: datetime | None = None,
) -> Path:
    """Generate the full 4G Friday bear-case review from the committed
    template (reviews/templates/friday-bear-case.md), filled with the
    week's real data, saved verbatim per the template's operator notes.
    """
    ts = now or datetime.now(timezone.utc)
    iso = ts.isocalendar()
    week_label = f"{iso.year}-W{iso.week:02d}"
    week_start = ts - timedelta(days=7)

    prompt_template = _extract_template_prompt(
        repo_root / "reviews" / "templates" / "friday-bear-case.md"
    )

    with db.connect(db_path) as conn:
        inputs = _gather_friday_inputs(conn, week_start, repo_root)

    prompt = prompt_template
    prompt = prompt.replace("{{WEEK_NUMBER - 1}}", str(iso.week - 1))
    prompt = prompt.replace("{{WEEK_NUMBER}}", str(iso.week))
    prompt = prompt.replace(
        "{{WEEK_RANGE}}", f"{week_start.date().isoformat()} → {ts.date().isoformat()}"
    )
    for key, value in inputs.items():
        prompt = prompt.replace("{{" + key + "}}", value)

    if client is None:
        from claude_client import ClaudeClient, model_for_role

        client = ClaudeClient(model=model_for_role("review"), db_path=db_path)
    result = client.complete(
        prompt, called_from="friday_bear_case", max_tokens=8192
    )

    out_path = repo_root / "reviews" / f"{week_label}-friday.md"
    # Verbatim per the template's operator notes — editing defeats the
    # methodology. Only a provenance footer is appended.
    out_path.write_text(
        f"{result.text}\n\n---\n\n"
        f"machine-generated · model {result.model} · called_from friday_bear_case "
        f"· logged to llm_calls\n"
    )
    return out_path


# ── The investigator (route A) ──────────────────────────────────────────
# Upgrades the Friday review from form letter to analyst: instead of
# receiving a fixed data dump, the model queries trader.db and reads repo
# files itself, then writes. Manual tool loop via claude_client.
# complete_agentic — every API call audited in llm_calls.

INVESTIGATOR_TOOLS = [
    {
        "name": "run_sql",
        "description": (
            "Run a read-only SELECT (or WITH...SELECT) against trader.db. "
            "Tables: bars, signals, trades, decisions, runs, recommendations, "
            "llm_calls, context_data. Returns up to 200 rows as text. "
            "Use this to gather trade history, run stats, decision breakdowns."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "A single SELECT statement"}},
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": (
            "Read a repo file (path relative to the repo root), e.g. "
            "pending.md, decision-log.md, reviews/2026-W29-friday.md, "
            "reports/gauntlet-2026-07-16.md. Returns up to 20000 chars."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
]


def make_sql_tool(db_path: Path | None = None):
    """Read-only by construction: URI mode=ro plus a SELECT/WITH gate."""
    def run_sql(inp: dict) -> str:
        query = str(inp.get("query", "")).strip().rstrip(";")
        head = query.lstrip("( ").split(None, 1)[0].upper() if query else ""
        if head not in ("SELECT", "WITH"):
            raise ValueError("read-only: only SELECT/WITH queries are allowed")
        path = db_path or (REPO_ROOT / "trader.db")
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(query).fetchmany(200)
        finally:
            conn.close()
        if not rows:
            return "(no rows)"
        cols = rows[0].keys()
        lines = [" | ".join(cols)]
        lines += [" | ".join(str(r[c]) for c in cols) for r in rows]
        out = "\n".join(lines)
        return out[:8000] + ("\n...(truncated)" if len(out) > 8000 else "")
    return run_sql


def make_file_tool(repo_root: Path = REPO_ROOT):
    def read_file(inp: dict) -> str:
        rel = str(inp.get("path", ""))
        target = (repo_root / rel).resolve()
        root = repo_root.resolve()
        if not target.is_relative_to(root):
            raise ValueError("path escapes the repo root")
        if not target.is_file():
            raise FileNotFoundError(rel)
        text = target.read_text(errors="replace")
        return text[:20000] + ("\n...(truncated)" if len(text) > 20000 else "")
    return read_file


def run_friday_investigated(
    client=None,
    db_path: Path | None = None,
    repo_root: Path = REPO_ROOT,
    now: datetime | None = None,
) -> Path:
    """The analyst version of the Friday review: same 4G template as the
    spec, but the {{...}} inputs are gathered by the model itself via
    read-only tools. Falls back to run_friday() at the call site."""
    ts = now or datetime.now(timezone.utc)
    iso = ts.isocalendar()
    week_label = f"{iso.year}-W{iso.week:02d}"
    week_start = ts - timedelta(days=7)

    template_prompt = _extract_template_prompt(
        repo_root / "reviews" / "templates" / "friday-bear-case.md"
    )
    prompt = (
        f"Today is {ts.date().isoformat()} (ISO week {iso.week}). The week "
        f"under review is {week_start.date().isoformat()} → {ts.date().isoformat()}.\n\n"
        "You are the INVESTIGATOR for this week's 4G Friday review. The "
        "template below contains {{PLACEHOLDER}} inputs that are NOT "
        "pre-filled: gather them yourself with the run_sql and read_file "
        "tools before writing anything. At minimum: the week's trades "
        "(entry/exit/pnl by variant), runs status counts, decisions "
        "placed-vs-rejected with top rejection reasons, the prior Friday "
        "review file (newest reviews/*-friday.md before this week), and "
        "pending.md. Investigate anything suspicious the numbers surface — "
        "you may run additional queries and read decision-log.md or recent "
        "reports. Then produce the review exactly per the template's four "
        "mandatory sections plus the final weaken/strengthen sentence.\n\n"
        "--- TEMPLATE ---\n\n" + template_prompt
    )

    if client is None:
        from claude_client import ClaudeClient, model_for_role

        client = ClaudeClient(model=model_for_role("review"), db_path=db_path)
    from claude_client import complete_agentic

    result = complete_agentic(
        client,
        prompt,
        called_from="friday_bear_case_investigated",
        tools=INVESTIGATOR_TOOLS,
        tool_handlers={
            "run_sql": make_sql_tool(db_path),
            "read_file": make_file_tool(repo_root),
        },
        system=SKEPTIC_SYSTEM,
        max_tokens=8192,
        max_turns=10,
    )

    out_path = repo_root / "reviews" / f"{week_label}-friday.md"
    out_path.write_text(
        f"{result.text}\n\n---\n\n"
        f"machine-generated (investigator, {result.turns} turns) · model {result.model} "
        f"· called_from friday_bear_case_investigated · logged to llm_calls\n"
    )
    return out_path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Adversarial reviews (nightly + Friday)")
    parser.add_argument(
        "--friday", action="store_true",
        help="run the full 4G Friday bear-case review instead of the nightly skeptic",
    )
    args = parser.parse_args()

    db.migrate()
    if args.friday:
        # Investigator first; static template as fallback — a missed
        # Friday review is a Phase 1b archive trigger, so belt and braces.
        try:
            path = run_friday_investigated()
        except Exception as exc:
            print(f"investigator failed ({type(exc).__name__}: {exc}); falling back to static review")
            path = run_friday()
    else:
        path = run_nightly()
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
