#!/usr/bin/env bash
# Foundry autopilot (decision-log 2026-07-17 "close the seam").
# Twice daily at 04:02/16:02 UTC — between fetch cycles, after the
# nightly jobs. Each run advances whichever pipeline condition is ready
# (gauntlet for implemented rounds; next-round synthesis when epitaphs
# land). Long-running (gauntlet ~1h on this box) — flock prevents overlap.

set -uo pipefail
REPO="/home/trader/algotrading-paper"
LOG="${REPO}/vps/logs/foundry-$(date -u +%Y-%m-%d).log"
exec 9>"${REPO}/vps/logs/foundry.lock"
flock -n 9 || { echo "autopilot already running" >> "${LOG}"; exit 0; }

cd "${REPO}" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate || exit 1
git pull --rebase --autostash >>"${LOG}" 2>&1 || true
echo "=== autopilot $(date -u +%FT%TZ) ===" >> "${LOG}"
if ! python scripts/foundry_autopilot.py >>"${LOG}" 2>&1; then
  echo "ALERT: foundry_autopilot FAILED $(date -u +%FT%TZ)" >> "${LOG}"
fi
echo "=== done $(date -u +%FT%TZ) ===" >> "${LOG}"
