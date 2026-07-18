#!/usr/bin/env bash
# Monthly outside eyes — 1st of the month, 12:02 UTC (2026-07-18).
#
# The elicitation exercise proved that unanchored fresh contexts find
# what the pipeline's own context cannot. Two standing outside runs:
#   1. Rival-lab audit: a domain-disguised description of the CURRENT
#      operation (numbers regenerated from live state) is handed to a
#      blind, tool-less context that reverse-engineers a 10x-better
#      rival. reviews/outside/audit-YYYY-MM.md
#   2. Literature refresh: a web-enabled context re-surveys published
#      evidence since the last survey. reviews/outside/literature-YYYY-MM.md
# Both land in the repo; the Friday review and the operator read them.

set -uo pipefail
REPO="/home/trader/algotrading-paper"
LOG="${REPO}/vps/logs/outside-$(date -u +%Y-%m).log"
export PATH="$HOME/.local/bin:$PATH"
exec 9>"${REPO}/vps/logs/outside.lock"
flock -n 9 || exit 0

cd "${REPO}" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate || exit 1
export "$(grep '^ANTHROPIC_API_KEY=' .env | head -1 | xargs)"
git pull --rebase --autostash >>"${LOG}" 2>&1 || true
mkdir -p reviews/outside
MONTH=$(date -u +%Y-%m)
echo "=== outside ${MONTH} $(date -u +%FT%TZ) ===" >> "${LOG}"

# ── 1. Rival-lab audit (blind, tool-less, domain-disguised) ──────────
DISGUISE=$(python - << 'PYEOF'
import json
reg = json.load(open("reviews/foundry/dead-ideas.json"))
n_ideas = len(reg.get("ideas", []))
n_lessons = len(reg.get("failure_lessons", []))
import glob
n_rounds = len(glob.glob("reviews/foundry/round-*.json"))
print(f"""I run a small automated research pipeline that searches for forecasting
rules in archived time-series data. Evidence sources: a fixed archive of
~2.5 years of fine-grained measurements from 5 parallel data streams, and
one live feed accruing a few ground-truth outcomes per day (rate fixed).
Daily cycle: a generator reading a registry of failure write-ups proposes
5 novel candidate rules; each is implemented, evaluated once against the
archive under a realistic cost model, and receives a pass/fail verdict
plus a failure analysis. Registry state: {n_ideas} rules tested across
{n_rounds} batches, {n_lessons} general lessons. We have measured our own
detection power and the predictability ceiling of our current feature
set, added blind pre-mortems before implementation and blind second
readings of the failure analyses, and begun collecting an auxiliary data
stream our archive lacked. Budget: one small server, modest LLM spend,
one part-time human.

A competing team with identical resources credibly claims 10x more
validated learning per week. Reverse-engineer their pipeline stage by
stage: what do they have that we lack NOW? Rank the differences by how
much of the 10x each explains. Concrete mechanisms only; no generic
advice; do not re-propose what we already listed.""")
PYEOF
)
if timeout 900 claude -p "${DISGUISE}" --model claude-sonnet-5 \
    --allowedTools "" > "reviews/outside/audit-${MONTH}.md" 2>>"${LOG}"; then
  echo "rival audit ok" >> "${LOG}"
else
  echo "ALERT: rival audit FAILED" >> "${LOG}"
fi

# ── 2. Literature refresh (web-enabled) ──────────────────────────────
LIT_PROMPT="Survey NEW published evidence (academic + credible practitioner, prioritize the last 6 months) on short-horizon cryptocurrency predictability at small retail scale: funding-rate/open-interest signals, order-book effects, momentum/reversal at horizons from 24 hours to 8 weeks, and realized retail trading costs on Coinbase/Kraken/Alpaca. Compare against the priors in docs/literature-priors.md (read it first) and report ONLY what is new or contradicts those priors, with citations. Output markdown; do not modify any file except printing your report."
if timeout 1800 claude -p "${LIT_PROMPT}" --model claude-sonnet-5 \
    --allowedTools "WebSearch WebFetch Read" \
    > "reviews/outside/literature-${MONTH}.md" 2>>"${LOG}"; then
  echo "literature refresh ok" >> "${LOG}"
else
  echo "ALERT: literature refresh FAILED" >> "${LOG}"
fi

git add reviews/outside >>"${LOG}" 2>&1
git commit -m "Outside eyes: ${MONTH} (rival audit + literature refresh)" \
  -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>" >>"${LOG}" 2>&1 \
  || echo "nothing to commit" >> "${LOG}"
git pull --rebase --autostash >>"${LOG}" 2>&1 && git push >>"${LOG}" 2>&1
echo "=== done $(date -u +%FT%TZ) ===" >> "${LOG}"
