#!/usr/bin/env bash
#
# VPS cron entry point. System cron invokes this every 5 minutes on the
# Hetzner box (see decision-log 2026-05-23). Runs the full surface
# pipeline that the old GitHub Actions workflow ran:
#
#   git pull → fetch.py → render_index.py → generate_surface.py
#   → commit (trader.db + INDEX.md + surface/surface.json
#     + surface/punch_list.json + surface/index.html) → push
#
# Discipline:
#   - fetch.py writes a runs row (status='ok' or 'failed', kind='cron')
#     on every invocation — the audit trail is non-negotiable, so even
#     a failed fetch still produces a committable row.
#   - render_index + generate_surface always run, even on fetch failure,
#     so INDEX and the surface reflect the failure (honest uptime).
#   - exit 0 when fetch.py succeeded even if the push fails; the next
#     run retries the push. A failed fetch exits non-zero so cron logs
#     surface it.

set -uo pipefail

REPO="/home/trader/algotrading-paper"
VENV="${REPO}/.venv"
LOG_DIR="${REPO}/vps/logs"
DATE_UTC="$(date -u +%Y-%m-%d)"
NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DAY_LOG="${LOG_DIR}/cron-${DATE_UTC}.log"

mkdir -p "${LOG_DIR}"

log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "${DAY_LOG}"; }

log "=== cron run ${NOW_UTC} ==="

cd "${REPO}" || { log "FATAL: cannot cd to ${REPO}"; exit 1; }

# Prevent overlapping */5 runs (slow fetch + push retries can exceed 5min)
exec 8>"${LOG_DIR}/fetch.lock"
flock -n 8 || { log "previous fetch run still active — skipping"; exit 0; }

# Recover a wedged rebase from a prior crashed run (audit 2026-07-17:
# an unresolved rebase left the repo detached and froze all pushes).
if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
  git rebase --abort >>"${DAY_LOG:-/dev/null}" 2>&1 || true
fi


# shellcheck disable=SC1091
source "${VENV}/bin/activate" || { log "FATAL: cannot activate venv"; exit 1; }

# Receive any operator commits before we write/commit our own.
if ! git pull --rebase --autostash >>"${DAY_LOG}" 2>&1; then
  log "WARN: git pull failed; continuing with local state"
fi

# --- Fetch (default --kind=cron). Capture exit code; do not abort. ---
FETCH_RC=0
python fetch.py --minutes=90 >>"${DAY_LOG}" 2>&1 || FETCH_RC=$?
if [ "${FETCH_RC}" -eq 0 ]; then
  log "fetch.py ok"
else
  log "fetch.py FAILED rc=${FETCH_RC} (runs row logged status='failed')"
fi

# --- Trade cycle: signals → execution → exits, on the fresh bars. ---
# Non-fatal: a cycle failure is logged and visible in the surface, but
# doesn't block rendering/committing (honest-failure discipline, same
# as fetch). Skipped when fetch failed — no fresh bars to act on.
if [ "${FETCH_RC}" -eq 0 ]; then
  if python trade_cycle.py >>"${DAY_LOG}" 2>&1; then
    log "trade_cycle.py ok"
  else
    log "WARN: trade_cycle.py failed"
  fi
fi

# --- Regenerate surfaces regardless of fetch outcome ---
python render_index.py >>"${DAY_LOG}" 2>&1 || log "WARN: render_index.py failed"
python scripts/generate_surface.py >>"${DAY_LOG}" 2>&1 || log "WARN: generate_surface.py failed"

# --- Commit + push the artifacts ---
git add trader.db INDEX.md surface/surface.json surface/punch_list.json surface/index.html
if git diff --staged --quiet; then
  log "nothing to commit"
else
  MSG="fetch run ${NOW_UTC}"
  [ "${FETCH_RC}" -ne 0 ] && MSG="${MSG} (fetch failed; runs row logged)"
  git commit -m "${MSG}" >>"${DAY_LOG}" 2>&1 || log "WARN: commit failed"

  PUSHED=0
  for attempt in 1 2 3; do
    if git push >>"${DAY_LOG}" 2>&1; then
      log "push ok (attempt ${attempt})"
      PUSHED=1
      break
    fi
    log "push failed (attempt ${attempt}); pull --rebase and retry"
    git pull --rebase --autostash >>"${DAY_LOG}" 2>&1 || { git rebase --abort >>"${DAY_LOG}" 2>&1 || true; break; }
  done
  [ "${PUSHED}" -eq 0 ] && log "WARN: push failed after retries; next run will catch up"
fi

log "=== done ${NOW_UTC} ==="

# Exit reflects fetch success: a failed fetch is the signal cron should
# surface; a failed push is recoverable on the next run.
exit "${FETCH_RC}"
