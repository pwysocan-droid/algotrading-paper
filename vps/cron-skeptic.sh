#!/usr/bin/env bash
#
# Nightly adversarial skeptic (see adversarial_cron.py). Runs at 03:32
# UTC — deliberately between the */5 fetch cycles (03:30, 03:35) so the
# two jobs never race each other's git operations.
#
# Commits ONLY reviews/nightly/* and pending.md. The llm_calls row this
# writes into trader.db is deliberately NOT committed here — the 5-min
# cron-fetch.sh already commits trader.db on every cycle and will carry
# it within minutes; two jobs committing the same binary file is the
# conflict shape the single-writer discipline exists to avoid.

set -uo pipefail

REPO="/home/trader/algotrading-paper"
VENV="${REPO}/.venv"
LOG_DIR="${REPO}/vps/logs"
NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LOG="${LOG_DIR}/skeptic-$(date -u +%Y-%m-%d).log"

mkdir -p "${LOG_DIR}"
log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "${LOG}"; }

log "=== skeptic run ${NOW_UTC} ==="

cd "${REPO}" || { log "FATAL: cannot cd to ${REPO}"; exit 1; }
# shellcheck disable=SC1091
source "${VENV}/bin/activate" || { log "FATAL: cannot activate venv"; exit 1; }

git pull --rebase --autostash >>"${LOG}" 2>&1 || log "WARN: git pull failed; continuing"

if ! python adversarial_cron.py >>"${LOG}" 2>&1; then
  log "adversarial_cron.py FAILED — no commit"
  exit 1
fi

git add reviews/nightly pending.md
if git diff --staged --quiet; then
  log "nothing to commit"
else
  git commit -m "nightly skeptic ${NOW_UTC}" >>"${LOG}" 2>&1 || log "WARN: commit failed"
  for attempt in 1 2 3; do
    if git push >>"${LOG}" 2>&1; then
      log "push ok (attempt ${attempt})"
      break
    fi
    log "push failed (attempt ${attempt}); pull --rebase and retry"
    git pull --rebase --autostash >>"${LOG}" 2>&1 || break
  done
fi

log "=== done ${NOW_UTC} ==="
