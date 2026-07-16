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
from datetime import datetime, timezone
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
        from claude_client import ClaudeClient

        client = ClaudeClient(db_path=db_path)
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


def main() -> int:
    db.migrate()
    path = run_nightly()
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
