#!/usr/bin/env bash
# VRP harvester — Candidate #1, daily paper run (2026-07-24).
# Manages open spreads, writes new ones when premium is genuinely rich and the
# stand-aside clears. PAPER only, riskless. Weekdays mid-morning ET (liquid
# options). Commits its ledger + report so the operator can watch it.

set -uo pipefail
REPO="/home/trader/algotrading-paper"
LOG="${REPO}/vps/logs/vrp-$(date -u +%Y-%m-%d).log"
exec 9>"${REPO}/vps/logs/vrp.lock"
flock -n 9 || exit 0

cd "${REPO}" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate || exit 1
git pull --rebase --autostash >>"${LOG}" 2>&1 || true

echo "=== vrp $(date -u +%FT%TZ) ===" >> "${LOG}"
if PLACE=1 python scripts/vrp_harvester.py >>"${LOG}" 2>&1; then
  echo "vrp ok" >> "${LOG}"
else
  echo "ALERT: vrp run FAILED $(date -u +%FT%TZ)" >> "${LOG}"
fi

git add book/positions.jsonl reports/vrp-*.json >>"${LOG}" 2>&1 || true
if ! git diff --staged --quiet; then
  git commit -q -m "VRP paper run $(date -u +%FT%TZ)" \
    -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" >>"${LOG}" 2>&1
  git pull --rebase --autostash >>"${LOG}" 2>&1 && git push >>"${LOG}" 2>&1
fi
echo "=== done $(date -u +%FT%TZ) ===" >> "${LOG}"
