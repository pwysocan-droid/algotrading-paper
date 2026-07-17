"""Aggregate foundry rounds + gauntlet results into surface/rounds.json,
and render the weekly digest (reports/digest-YYYY-MM-DD.md).

rounds.json feeds the dashboard's results-by-date page. The digest is the
email body — actual sending is wired once the operator authorizes the
Gmail connector; until then it's a committed artifact.

Run by the nightly skeptic cron (cheap: pure file aggregation, no LLM).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db

REPO_ROOT = Path(__file__).resolve().parent.parent


def build_rounds(repo_root: Path = REPO_ROOT) -> dict:
    rounds = []
    for path in sorted((repo_root / "reviews" / "foundry").glob("round-*.json")):
        data = json.loads(path.read_text())
        rounds.append({
            "round": data.get("round"),
            "date": (data.get("generated_at") or "")[:10],
            "thesis": data.get("round_thesis"),
            "ideas": [
                {"name": i["name"], "lens": i["lens"],
                 "kill_criterion": i.get("kill_criterion")}
                for i in data.get("ideas", [])
            ],
        })

    gauntlets = []
    for path in sorted((repo_root / "reports").glob("gauntlet-*.json")):
        data = json.loads(path.read_text())
        gauntlets.append(data)

    # registry verdicts give each idea its current status
    verdicts = {}
    reg_path = repo_root / "reviews" / "foundry" / "dead-ideas.json"
    if reg_path.exists():
        reg = json.loads(reg_path.read_text())
        verdicts = {i["name"]: i["verdict"] for i in reg.get("ideas", [])}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rounds": rounds,
        "gauntlets": gauntlets,
        "verdicts": verdicts,
    }


def build_digest(repo_root: Path = REPO_ROOT, db_path: Path | None = None,
                 now: datetime | None = None) -> str:
    ts = now or datetime.now(timezone.utc)
    lines = [
        f"# algotrading-paper · digest · {ts.date().isoformat()}",
        "",
    ]

    # live scoreboard
    with db.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT variant_name, COUNT(*) AS placed,
                   SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) AS open_n,
                   SUM(CASE WHEN status='closed' AND pnl_usd > 0 THEN 1 ELSE 0 END) AS wins,
                   SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed_n,
                   COALESCE(SUM(CASE WHEN status='closed' THEN pnl_usd END), 0) AS pnl
              FROM trades GROUP BY variant_name ORDER BY pnl DESC
            """
        ).fetchall()
        llm = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(total_tokens),0) AS tok FROM llm_calls"
        ).fetchone()

    lines += ["## Live scoreboard (closed P&L)", ""]
    if rows:
        lines += ["| variant | placed | open | win% | P&L |", "| --- | --- | --- | --- | --- |"]
        for r in rows:
            wr = f"{r['wins'] / r['closed_n']:.0%}" if r["closed_n"] else "—"
            lines.append(
                f"| {r['variant_name']} | {r['placed']} | {r['open_n']} | {wr} "
                f"| ${r['pnl']:,.2f} |"
            )
    else:
        lines.append("no trades yet")
    lines.append("")

    # latest gauntlet
    gauntlets = sorted((repo_root / "reports").glob("gauntlet-*.json"))
    if gauntlets:
        g = json.loads(gauntlets[-1].read_text())
        lines += [f"## Latest gauntlet ({g['date']}, {g['days']}d)", "",
                  "| candidate | placed | net P&L | edge/slot |",
                  "| --- | --- | --- | --- |"]
        for r in g["results"]:
            eps = f"${r['edge_per_slot']:.3f}" if r["edge_per_slot"] is not None else "—"
            lines.append(
                f"| {r['name']} | {r['placed']} | ${r['total_pnl']:,.2f} | {eps} |"
            )
        lines.append("")

    # latest reviews
    fridays = sorted((repo_root / "reviews").glob("*-friday.md"))
    if fridays:
        latest = fridays[-1]
        body = latest.read_text()
        # last blockquote (the weaken/strengthen sentence) if present
        quotes = [l for l in body.splitlines() if l.startswith(">")]
        lines += [f"## Latest Friday review ({latest.stem})", ""]
        lines += quotes[-4:] if quotes else ["(see repo)"]
        lines.append("")

    lines += [
        "## Backbone",
        "",
        f"{llm['n']} llm_calls · {llm['tok']:,} tokens total",
        "",
        "---",
        "",
        "full detail: pwysocan-droid.github.io/algotrading-paper/surface/rounds.html",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    data = build_rounds()
    out = REPO_ROOT / "surface" / "rounds.json"
    out.write_text(json.dumps(data, indent=2) + "\n")

    digest = build_digest()
    dpath = REPO_ROOT / "reports" / f"digest-{datetime.now(timezone.utc).date().isoformat()}.md"
    dpath.write_text(digest)
    print(f"wrote {out} and {dpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
