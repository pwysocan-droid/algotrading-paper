#!/usr/bin/env bash
# Charter E — Stage 0 Kalshi venue cost-floor study (MEASUREMENT ONLY, no trading).
# `snapshot`: append two-sided quotes to a LOCAL, gitignored kalshi.db.
# `report`  : build + commit the compact reports/event-venue-floor-{date}.json.
# Raw snapshots are NEVER committed (heeds the trader.db 28 GB bloat lesson).
set -uo pipefail
MODE="${1:-snapshot}"
REPO="/home/trader/algotrading-paper"
LOG="${REPO}/vps/logs/kalshi-$(date -u +%Y-%m).log"
exec 9>"${REPO}/vps/logs/kalshi.lock"
flock -n 9 || exit 0
cd "${REPO}" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate || exit 1

if [ "${MODE}" = "snapshot" ]; then
  echo "=== snapshot $(date -u +%FT%TZ) ===" >> "${LOG}"
  python3 venues/kalshi/snapshot.py >> "${LOG}" 2>&1 || echo "ALERT: kalshi snapshot FAILED" >> "${LOG}"
elif [ "${MODE}" = "report" ]; then
  echo "=== report $(date -u +%FT%TZ) ===" >> "${LOG}"
  git pull --rebase --autostash >> "${LOG}" 2>&1 || true
  if python3 venues/kalshi/floor_report.py >> "${LOG}" 2>&1; then
    git add reports/event-venue-floor-*.json >> "${LOG}" 2>&1 || true
    if ! git diff --staged --quiet; then
      git commit -q -m "Charter E Stage 0: venue floor report $(date -u +%F)" \
        -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" >> "${LOG}" 2>&1
      git pull --rebase --autostash >> "${LOG}" 2>&1 && git push >> "${LOG}" 2>&1
    fi
  else
    echo "ALERT: kalshi floor_report FAILED" >> "${LOG}"
  fi
fi
