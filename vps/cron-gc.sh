#!/usr/bin/env bash
# DAILY git maintenance (weekly->daily 2026-08-03). The fetch loop commits trader.db/context.db
# every run (Option A backup); without regular packing the loose objects ballooned
# to 28 GB and filled the disk (auto-gc had fallen behind, likely disk/mem-starved).
# Weekly proved insufficient (~6.5 GB/day loose growth outran it); daily now. Pack memory is capped in repo config (pack.threads=1,
# pack.window=5, pack.windowMemory=96m) so pack-objects can't OOM the 3.7 GB box.

set -uo pipefail
REPO="/home/trader/algotrading-paper"
LOG="${REPO}/vps/logs/gc-$(date -u +%Y-%m).log"
exec 9>"${REPO}/vps/logs/gc.lock"
flock -n 9 || exit 0
cd "${REPO}" || exit 1

FREE_BEFORE=$(df -h / | tail -1 | awk '{print $4" ("$5")"}')
echo "=== gc $(date -u +%FT%TZ) · before ${FREE_BEFORE} · .git $(du -sh .git | cut -f1) ===" >> "${LOG}"
# nice + ionice so maintenance never starves the trading loop
if nice -n 15 git gc >> "${LOG}" 2>&1; then
  echo "gc ok · after $(df -h / | tail -1 | awk '{print $4" ("$5")"}') · .git $(du -sh .git | cut -f1)" >> "${LOG}"
else
  echo "ALERT: git gc FAILED $(date -u +%FT%TZ)" >> "${LOG}"
fi

# Disk guard: shout into the log if we ever cross 80% again
USE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "${USE}" -ge 80 ]; then
  echo "ALERT: disk ${USE}% after gc — investigate .git / logs growth" >> "${LOG}"
fi
