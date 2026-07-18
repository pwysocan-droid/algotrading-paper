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
from datetime import date, datetime, timezone
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


def pipeline_health(repo_root: Path = REPO_ROOT,
                    now: datetime | None = None) -> list[str]:
    """Foundry stall/alert detection — the seam's failure mode is SILENT
    (a synthesis crash on 2026-07-17 only logged an ALERT to a VPS file
    nobody reads). This surfaces it in the one channel read daily: the
    emailed digest. Returns warning lines, empty when healthy."""
    ts = now or datetime.now(timezone.utc)
    warnings: list[str] = []

    rounds = sorted((repo_root / "reviews" / "foundry").glob("round-*.json"))
    if rounds:
        age_days = (ts.timestamp() - rounds[-1].stat().st_mtime) / 86400.0
        if age_days > 3.0:
            warnings.append(
                f"⚠ FOUNDRY STALLED: newest round ({rounds[-1].stem}) is "
                f"{age_days:.1f} days old — no new round in >3 days. Check "
                "vps/logs/foundry-*.log and the cloud implementer's runs."
            )

    log_dir = repo_root / "vps" / "logs"
    if log_dir.exists():
        for prefix in ("foundry", "implementer"):
            # Concatenate yesterday+today in order and judge only the LAST
            # run block: an ALERT followed by a later successful run is a
            # recovered incident, and an alarm that keeps ringing after
            # recovery trains the operator to ignore it (first digest,
            # 2026-07-18, alarmed on a crash fixed 12 hours earlier).
            text = ""
            for offset in (1, 0):
                day = date.fromtimestamp(ts.timestamp() - offset * 86400).isoformat()
                log = log_dir / f"{prefix}-{day}.log"
                if log.exists():
                    text += log.read_text()
            if not text:
                continue
            blocks = text.split("=== ")
            last_run = next(
                (b for b in reversed(blocks) if not b.startswith("done")), "")
            if "ALERT" in last_run:
                warnings.append(
                    f"⚠ {prefix.upper()} ALERT: the most recent run failed — "
                    f"read the tail of vps/logs/{prefix}-*.log for the traceback."
                )
    return warnings


def build_digest(repo_root: Path = REPO_ROOT, db_path: Path | None = None,
                 now: datetime | None = None) -> str:
    ts = now or datetime.now(timezone.utc)
    lines = [
        f"# algotrading-paper · digest · {ts.date().isoformat()}",
        "",
    ]
    health = pipeline_health(repo_root, now=ts)
    if health:
        lines += ["## ⚠ Pipeline health", ""]
        lines += [f"- {w}" for w in health]
        lines += [""]

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
