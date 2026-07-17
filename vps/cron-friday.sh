#!/usr/bin/env bash
#
# Weekly Friday 4G bear-case review (adversarial_cron.py --friday).
# Runs Fridays at 03:34 UTC — between the */5 fetch cycles, two minutes
# after the nightly skeptic slot so the two never overlap.
#
# Commits ONLY the reviews/*-friday.md artifact. The llm_calls row rides
# in trader.db via the next 5-min fetch commit (single-committer for the
# binary file, same as cron-skeptic.sh).

set -uo pipefail

REPO="/home/trader/algotrading-paper"
VENV="${REPO}/.venv"
LOG_DIR="${REPO}/vps/logs"
NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LOG="${LOG_DIR}/friday-$(date -u +%Y-%m-%d).log"

mkdir -p "${LOG_DIR}"
log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "${LOG}"; }

log "=== friday review run ${NOW_UTC} ==="

cd "${REPO}" || { log "FATAL: cannot cd to ${REPO}"; exit 1; }
# shellcheck disable=SC1091
source "${VENV}/bin/activate" || { log "FATAL: cannot activate venv"; exit 1; }

if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
  git rebase --abort >>"${LOG}" 2>&1 || true
fi
git pull --rebase --autostash >>"${LOG}" 2>&1 || { git rebase --abort >>"${LOG}" 2>&1 || true; log "WARN: git pull failed; continuing"; }

# Fresh calibration report first, so the investigator can read it.
python scripts/calibration_report.py >>"${LOG}" 2>&1 || log "WARN: calibration_report failed"

if ! python adversarial_cron.py --friday >>"${LOG}" 2>&1; then
  log "adversarial_cron.py --friday FAILED — no commit"
  exit 1
fi

git add reviews reports
if git diff --staged --quiet; then
  log "nothing to commit"
else
  git commit -m "friday adversarial review ${NOW_UTC}" >>"${LOG}" 2>&1 || log "WARN: commit failed"
  for attempt in 1 2 3; do
    if git push >>"${LOG}" 2>&1; then
      log "push ok (attempt ${attempt})"
      break
    fi
    log "push failed (attempt ${attempt}); pull --rebase and retry"
    git pull --rebase --autostash >>"${LOG}" 2>&1 || { git rebase --abort >>"${LOG}" 2>&1 || true; break; }
  done
fi

log "=== done ${NOW_UTC} ==="
