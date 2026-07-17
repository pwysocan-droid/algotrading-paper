"""Foundry autopilot — the VPS half of the closed seam (decision-log 2026-07-17).

Runs from cron; each invocation advances whichever condition is ready:

  A. Newest round fully IMPLEMENTED (all idea names registered in
     config.STRATEGY_VARIANTS) but not yet GAUNTLETED (no gauntlet
     results covering them) → ensure research_bars.db exists (build via
     backfill if missing), run the staged parallel gauntlet on it with a
     selection/holdout split, push results.
  B. Newest round gauntleted AND every idea has a registry verdict
     (epitaphs written — the cloud agent's job) AND no newer round →
     run idea_foundry.py to generate the next round, push.

Idempotent: each condition checks git-visible state, so re-runs and
lost sessions are harmless. Implementation and epitaphs are the cloud
agent's half — pure code work needing no secrets.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent
FOUNDRY = REPO_ROOT / "reviews" / "foundry"
RESEARCH_DB = REPO_ROOT / "research_bars.db"
HOLDOUT_DAYS = 197  # 2026 window — never used for selection


def _newest_round() -> dict | None:
    rounds = sorted(FOUNDRY.glob("round-*.json"))
    if not rounds:
        return None
    return json.loads(rounds[-1].read_text())


def _idea_names(round_data: dict) -> list[str]:
    return [i["name"] for i in round_data.get("ideas", [])]


def _implemented(names: list[str]) -> bool:
    from config import STRATEGY_VARIANTS

    return all(n in STRATEGY_VARIANTS for n in names)


def _gauntleted(names: list[str]) -> bool:
    for path in sorted((REPO_ROOT / "reports").glob("gauntlet-*.json")):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            print(f"WARN: unreadable {path.name}: {exc}")  # never wedge on one bad file
            continue
        covered = {r["name"] for r in data.get("results", [])}
        if set(names) <= covered:
            return True
    return False


def _epitaphed(names: list[str]) -> bool:
    reg = json.loads((FOUNDRY / "dead-ideas.json").read_text())
    verdicts = {i["name"] for i in reg.get("ideas", [])}
    return all(n in verdicts for n in names)


def _sh(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def _git_push(paths: list[str], message: str) -> None:
    """Retrying push: results MUST reach the remote or the pipeline's other
    half (the cloud agent) never sees them and the autopilot waits forever
    on itself — the Pages-bug shape (audit 2026-07-17)."""
    for attempt in range(3):
        try:
            _sh(["git", "add", *paths])
            diff = subprocess.run(["git", "diff", "--staged", "--quiet"], cwd=REPO_ROOT)
            if diff.returncode == 0:
                print("nothing to commit")
                return
            _sh(["git", "commit", "-m", message,
                 "-m", "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"])
            subprocess.run(["git", "pull", "--rebase", "--autostash"], cwd=REPO_ROOT)
            _sh(["git", "push"])
            return
        except subprocess.CalledProcessError as exc:
            print(f"push attempt {attempt + 1} failed: {exc}; recovering")
            subprocess.run(["git", "rebase", "--abort"], cwd=REPO_ROOT)
    raise RuntimeError(f"could not push {paths} after 3 attempts — pipeline state is local-only")


def ensure_research_db() -> None:
    if RESEARCH_DB.exists():
        return
    print("research_bars.db missing — building (one-time, ~10 min)")
    import db as db_mod
    from scripts.backfill import parse_date, run_backfill

    db_mod.migrate(RESEARCH_DB)
    chunks = [("2024-01-01", "2024-07-01"), ("2024-07-01", "2025-01-01"),
              ("2025-01-01", "2025-07-01"), ("2025-07-01", "2026-01-04"),
              ("2026-01-04", datetime.now(timezone.utc).date().isoformat())]
    for a, b in chunks:
        run_backfill(parse_date(a), parse_date(b), db_path=RESEARCH_DB)


def main() -> int:
    rnd = _newest_round()
    if rnd is None:
        print("no rounds exist")
        return 0
    names = _idea_names(rnd)
    n = rnd.get("round")

    if _implemented(names) and not _gauntleted(names):
        print(f"condition A: round {n} implemented, not gauntleted — running")
        ensure_research_db()
        _sh([sys.executable, "scripts/run_gauntlet.py", "--staged",
             "--days", "930", "--db", str(RESEARCH_DB),
             "--names", ",".join(names)])
        _git_push(["reports"], f"Autopilot: staged gauntlet for round {n:03d}")
        return 0

    if _implemented(names) and _gauntleted(names) and _epitaphed(names):
        print(f"condition B: round {n} complete — generating round {n + 1}")
        _sh([sys.executable, "scripts/idea_foundry.py"])
        _sh([sys.executable, "scripts/generate_rounds.py"])
        _git_push(["reviews/foundry", "surface/rounds.json", "reports"],
                  f"Autopilot: foundry round {n + 1:03d}")
        return 0

    print(f"round {n}: implemented={_implemented(names)} "
          f"gauntleted={_gauntleted(names)} epitaphed={_epitaphed(names)} — waiting on cloud agent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
