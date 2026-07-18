#!/usr/bin/env bash
# Layer-2 context tape — every 5 minutes (2026-07-18).
# Records funding/OI/book-shape snapshots to context.db. Never touches
# git or trader.db; cron-fetch's commit picks context.db up.

set -uo pipefail
REPO="/home/trader/algotrading-paper"
LOG="${REPO}/vps/logs/context-$(date -u +%Y-%m-%d).log"
exec 9>"${REPO}/vps/logs/context.lock"
flock -n 9 || exit 0

cd "${REPO}" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate || exit 1
python scripts/collect_context.py >>"${LOG}" 2>&1 \
  || echo "WARN collect_context failed $(date -u +%FT%TZ)" >> "${LOG}"
