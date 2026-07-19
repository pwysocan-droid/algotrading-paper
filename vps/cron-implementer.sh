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
from pathlib import Path
sys.path.insert(0, ".")
from scripts.foundry_autopilot import (
    _epitaphed, _gauntleted, _idea_names, _implemented, _newest_round)
rnd = _newest_round()
if rnd is None:
    print("none")
    raise SystemExit
n = rnd.get("round")
names = _idea_names(rnd)
foundry = Path("reviews/foundry")
premortem = (foundry / f"premortem-{n:03d}.md").exists()
secondread = (foundry / f"secondread-{n:03d}.md").exists()
# Fresh-context stages (decision-log 2026-07-18 "outside eyes"):
# a blind pre-mortem gates implementation; a blind second reading
# follows the epitaphs. Order matters: epitaphs first (unblocks the
# autopilot), then the newest round's premortem/implementation.
if _gauntleted(names) and not _epitaphed(names):
    print("epitaphs")
elif not _implemented(names) and not premortem:
    print(f"premortem {n}")
elif not _implemented(names):
    print("implement")
elif _epitaphed(names) and not secondread:
    print(f"secondread {n}")
else:
    print("none")
EOF
)
echo "state: ${STATE}" >> "${LOG}"
if [ "${STATE}" = "none" ]; then
  echo "nothing pending — pipeline current (or gauntlet in progress)" >> "${LOG}"
  echo "=== done $(date -u +%FT%TZ) ===" >> "${LOG}"
  exit 0
fi

# ── Fresh-context stages: each claude -p call is a BRAND-NEW context —
# the elicitation exercise (2026-07-18) proved unanchored eyes catch
# what the pipeline's own context cannot. These stages institutionalize
# that as machinery, not memory.

if [[ "${STATE}" == premortem* ]]; then
  N="${STATE#premortem }"
  NNN=$(printf '%03d' "${N}")
  PM_PROMPT="You are a BLIND pre-mortem critic for a trading-strategy research pipeline. You have no history with this project beyond the two files you are told to read. Read reviews/foundry/round-${NNN}.json (this round's 5 idea specs) and reviews/foundry/dead-ideas.json (every prior death + failure lessons). For EACH idea, try to kill it on paper BEFORE any implementation cost: check the base-rate arithmetic for correlated-conjunction errors (lesson: CONJUNCTIONS MULTIPLY TO ZERO) AND apply the measured calibration prior (2026-07-19 regression over 18 gradient records: predicted rates carry ~zero information — specs predicting >=0.3 fires/sym/day over-predicted ~17x on average, <0.3/day under-predicted ~2x, scatter +-8x; discount every expected_fire_rate accordingly), expected placed sample n>=100 over 930 days x 5 symbols (decidability), descent from a dead lineage, conflicts with the measured ceiling (sub-12h OHLCV is empty; 24h+maker or multi-week is the admissible band) and with any other failure lesson. Verdict per idea: IMPLEMENT (no fatal flaw found), REDESIGN (state the one change that fixes it), or SKIP (state the lesson it violates). Be adversarial; a false IMPLEMENT wastes a gauntlet, a false SKIP costs one idea. Write your report to reviews/foundry/premortem-${NNN}.md, then git add/commit ('Premortem: round ${NNN}') and push. Do not modify ANY other file."
  echo "invoking blind premortem (round ${N})" >> "${LOG}"
  if timeout 1800 claude -p "${PM_PROMPT}" --model claude-sonnet-5 \
      --dangerously-skip-permissions >>"${LOG}" 2>&1; then
    echo "premortem complete" >> "${LOG}"
  else
    echo "ALERT: premortem FAILED $(date -u +%FT%TZ)" >> "${LOG}"
  fi
  echo "=== done $(date -u +%FT%TZ) ===" >> "${LOG}"
  exit 0
fi

if [[ "${STATE}" == secondread* ]]; then
  N="${STATE#secondread }"
  NNN=$(printf '%03d' "${N}")
  # True blindness: the material is INLINED and the call gets no tools,
  # so it cannot peek at the pipeline's own epitaphs.
  MATERIAL=$(python - << PYEOF
import json, glob
n = int("${N}")
rnd = json.load(open(f"reviews/foundry/round-{n:03d}.json"))
ideas = {i["name"]: {"mechanism": i["mechanism"], "entry_rule": i["entry_rule"]}
         for i in rnd["ideas"]}
rows = []
for p in sorted(glob.glob("reports/gauntlet-*.json")):
    d = json.load(open(p))
    for r in d.get("results", []):
        if r["name"] in ideas:
            rows.append({k: r.get(k) for k in
                         ("name", "fill_model", "candidates", "placed",
                          "total_pnl", "edge_per_slot", "win_rate", "sharpe")})
print(json.dumps({"ideas": ideas, "gauntlet_rows": rows}, indent=1))
PYEOF
)
  SR_PROMPT="You are an independent second reader for a trading-strategy research pipeline. Below are 5 strategy ideas (mechanism + entry rule) and their backtest results (930-day constrained replay, fees 0.25%/leg, slippage 0.05%/leg, \$200 positions; edge_per_slot = net P&L per placed trade; a verdict needs n>=30). Someone else has already written cause-of-death diagnoses that you have NOT seen and must not try to guess. Write YOUR OWN mechanism-level diagnosis for each idea: WHY did it produce these numbers? Distinguish 'mechanism refuted', 'starved/undecidable', and 'uninformative'. Then rank your five diagnoses by your confidence in them. Output markdown only.

${MATERIAL}"
  echo "invoking blind second reader (round ${N})" >> "${LOG}"
  OUT="reviews/foundry/secondread-${NNN}.md"
  if timeout 900 claude -p "${SR_PROMPT}" --model claude-sonnet-5 \
      --allowedTools "" > "${OUT}.tmp" 2>>"${LOG}"; then
    {
      echo "# Second reading — round ${NNN} (blind, no registry access)"
      echo ""
      echo "Independent diagnoses written WITHOUT sight of the epitaphs;"
      echo "disagreement with dead-ideas.json marks a fragile lesson."
      echo ""
      cat "${OUT}.tmp"
    } > "${OUT}"
    rm -f "${OUT}.tmp"
    git add "${OUT}" >>"${LOG}" 2>&1
    git commit -m "Second reading: round ${NNN} (blind diagnosis)" \
      -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>" >>"${LOG}" 2>&1
    git pull --rebase --autostash >>"${LOG}" 2>&1 && git push >>"${LOG}" 2>&1
    echo "secondread complete" >> "${LOG}"
  else
    rm -f "${OUT}.tmp"
    echo "ALERT: secondread FAILED $(date -u +%FT%TZ)" >> "${LOG}"
  fi
  echo "=== done $(date -u +%FT%TZ) ===" >> "${LOG}"
  exit 0
fi

PROMPT="You are the foundry implementation agent, running directly on the trading VPS (the cloud half was silent, you are the fallback). The repo is the current directory with a ready .venv — use .venv/bin/python for everything; dependencies are installed. Read decision-log.md entry '2026-07-17 — Close the seam' first. Do exactly ONE task, then stop.

1) EPITAPHS: Find the newest reviews/foundry/round-NNN.json. If some reports/gauntlet-*.json covers all its idea names AND any name lacks an entry in reviews/foundry/dead-ideas.json, add one entry per missing idea: name; lineage 'foundry rNNN · <lens>'; tested (date + window); result (n, pnl, edge/slot, win rate); verdict 'dead' (or 'holdout_survivor' ONLY if it beat its own kill_criterion — never 'live_arm'); an epitaph with the mechanism-level lesson — and if the epitaph makes any COMPARATIVE claim ('carries information', 'no drift', 'selects losers', 'no better than X'), it MUST include a control_arm field citing the measured other side of the comparison, or explicitly 'control_arm': null (visible shame — the 2026-07-19 fragility audit found the five most poisonous lessons were all one-armed comparisons); and a gradient object {predicted_fires_per_sym_day, actual, net_expectancy_pct}. If reviews/foundry/premortem-NNN.md exists for this round, cite its per-idea verdict in each epitaph and add premortem_correct: true/false to the gradient object — the premortem is a forecaster being scored. Promote patterns seen twice into failure_lessons; maintain total_ideas_tested. Then refresh STATUS.md: bump its snapshot date and update the 'Current research state' numbers (rounds complete, ideas tested, lessons count, and the one-lead paragraph if the newest verdicts changed the picture) — keep its voice honest and terse, never hype a small sample. Validate JSON parses, commit, push.

2) IMPLEMENT: Else if any idea from the newest round is missing from STRATEGY_VARIANTS in config.py: FIRST read reviews/foundry/premortem-NNN.md (a blind critic's per-idea verdicts) — implement ALL ideas regardless, but apply any REDESIGN the spec accommodates and record the premortem verdicts in the commit message. Implement each as a pure function in signals.py per their entry_rule (follow the existing foundry-round idiom; register in STRATEGY_REGISTRY and config.STRATEGY_VARIANTS with enabled=False and the spec's params; premise-check cheap distribution claims against the bars table first and record results in the commit message). Add tests per the TestFoundryRound00X patterns and update the registry-key-set assertion. Run '.venv/bin/python -m pytest tests/ -q' until fully green. Commit crediting the round, push.

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
