#!/usr/bin/env bash
# Fallback implementer — the VPS's own hands (2026-07-17).
#
# The cloud foundry-implementer routine failed silently four times on
# its first real task, and the local-Mac stand-in only works while the
# Mac is on. This makes the seam genuinely machine-resident: Claude
# Code runs ON the VPS and does the same job — implement the newest
# round's ideas, or write epitaphs — whenever the cloud half has left
# work undone. Scheduled an hour AFTER the cloud's 08:08/20:08 UTC
# slots, so the cloud keeps first shot and this only fires on its
# silence. Idempotent: state is derived from the repo every run.

set -uo pipefail
REPO="/home/trader/algotrading-paper"
LOG="${REPO}/vps/logs/implementer-$(date -u +%Y-%m-%d).log"
export PATH="$HOME/.local/bin:$PATH"

exec 9>"${REPO}/vps/logs/implementer.lock"
flock -n 9 || { echo "implementer already running" >> "${LOG}"; exit 0; }

cd "${REPO}" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate || exit 1
export "$(grep '^ANTHROPIC_API_KEY=' .env | head -1 | xargs)"
git pull --rebase --autostash >>"${LOG}" 2>&1 || true

echo "=== implementer $(date -u +%FT%TZ) ===" >> "${LOG}"

# Anything for the implementer to do? (Mirrors foundry_autopilot's checks:
# work exists when the newest round is unimplemented, or gauntleted but
# not epitaphed. Gauntlet-pending is the autopilot's own job — skip.)
STATE=$(python - << 'EOF'
import sys
sys.path.insert(0, ".")
from scripts.foundry_autopilot import (
    _epitaphed, _gauntleted, _idea_names, _implemented, _newest_round)
rnd = _newest_round()
if rnd is None:
    print("none")
    raise SystemExit
names = _idea_names(rnd)
if not _implemented(names):
    print("implement")
elif _gauntleted(names) and not _epitaphed(names):
    print("epitaphs")
else:
    print("none")
EOF
)
echo "state: ${STATE}" >> "${LOG}"
if [ "${STATE}" = "none" ]; then
  echo "nothing pending — cloud half kept up (or gauntlet in progress)" >> "${LOG}"
  echo "=== done $(date -u +%FT%TZ) ===" >> "${LOG}"
  exit 0
fi

PROMPT="You are the foundry implementation agent, running directly on the trading VPS (the cloud half was silent, you are the fallback). The repo is the current directory with a ready .venv — use .venv/bin/python for everything; dependencies are installed. Read decision-log.md entry '2026-07-17 — Close the seam' first. Do exactly ONE task, then stop.

1) EPITAPHS: Find the newest reviews/foundry/round-NNN.json. If some reports/gauntlet-*.json covers all its idea names AND any name lacks an entry in reviews/foundry/dead-ideas.json, add one entry per missing idea: name; lineage 'foundry rNNN · <lens>'; tested (date + window); result (n, pnl, edge/slot, win rate); verdict 'dead' (or 'holdout_survivor' ONLY if it beat its own kill_criterion — never 'live_arm'); an epitaph with the mechanism-level lesson; and a gradient object {predicted_fires_per_sym_day, actual, net_expectancy_pct}. Promote patterns seen twice into failure_lessons; maintain total_ideas_tested. Then refresh STATUS.md: bump its snapshot date and update the 'Current research state' numbers (rounds complete, ideas tested, lessons count, and the one-lead paragraph if the newest verdicts changed the picture) — keep its voice honest and terse, never hype a small sample. Validate JSON parses, commit, push.

2) IMPLEMENT: Else if any idea from the newest round is missing from STRATEGY_VARIANTS in config.py: implement ALL missing ideas as pure functions in signals.py per their entry_rule (follow the existing foundry-round idiom; register in STRATEGY_REGISTRY and config.STRATEGY_VARIANTS with enabled=False and the spec's params; premise-check cheap distribution claims against the bars table first and record results in the commit message). Add tests per the TestFoundryRound00X patterns and update the registry-key-set assertion. Run '.venv/bin/python -m pytest tests/ -q' until fully green. Commit crediting the round, push.

HARD RULES: never set enabled=True on anything; NEVER modify or delete trader.db, .env, research_bars.db, or anything under vps/; never force-push; only push with a green test suite; if you cannot finish, print the exact error and stop."

echo "invoking claude code (state=${STATE})" >> "${LOG}"
if timeout 5400 claude -p "${PROMPT}" \
    --model claude-sonnet-5 \
    --dangerously-skip-permissions >>"${LOG}" 2>&1; then
  echo "claude run complete" >> "${LOG}"
else
  echo "ALERT: fallback implementer FAILED $(date -u +%FT%TZ)" >> "${LOG}"
fi
echo "=== done $(date -u +%FT%TZ) ===" >> "${LOG}"
