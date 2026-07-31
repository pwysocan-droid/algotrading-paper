#!/usr/bin/env bash
# Charter T — SEC EDGAR 8-K forward-only collection (COLLECTION ONLY, no signals,
# no trading). Appends new filings to a LOCAL gitignored filings.db; raw is never
# committed (disk-bloat lesson). Contract status surfaces in the daily digest.
# Runs at 03:00 UTC, before the 03:32 skeptic/digest render.
set -uo pipefail
REPO="/home/trader/algotrading-paper"
LOG="${REPO}/vps/logs/edgar-$(date -u +%Y-%m).log"
exec 9>"${REPO}/vps/logs/edgar.lock"
flock -n 9 || exit 0
cd "${REPO}" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate || exit 1
echo "=== edgar_8k $(date -u +%FT%TZ) ===" >> "${LOG}"
python3 feeds/edgar_8k/ingest.py >> "${LOG}" 2>&1 || echo "ALERT: edgar_8k ingest FAILED $(date -u +%FT%TZ)" >> "${LOG}"
