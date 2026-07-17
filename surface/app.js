// algotrading-paper · live surface
//
// Plumbing only. Fetches surface.json from the same directory every
// 5 minutes, populates data-bound elements, runs the paddle clock.
// No framework. No build step. No storage.

(function () {
  'use strict';

  // ---------- clock constants ----------
  const PADDLE_SWEEP_MS = 58 * 1000;
  const PADDLE_HOLD_MS = 2 * 1000;
  const PADDLE_CYCLE_MS = PADDLE_SWEEP_MS + PADDLE_HOLD_MS;

  // Cron cadence is sourced from vitals.cron_interval_seconds in the
  // JSON (the Python generator's source of truth — see decision-log
  // 2026-05-18). The initial fallback of 1h matches GH cron's observed
  // delivery in case the JSON is missing the field.
  let cronIntervalMs = 60 * 60 * 1000;

  // ---------- fetch cadence ----------
  const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
  const RETRY_INTERVAL_MS = 30 * 1000;
  // Both staleness thresholds are independent of cron cadence — they
  // measure infrastructure failures, not slow scheduling. 10 min for
  // fetch (network / Pages outage), 90 min for cron (scheduler stopped).
  const FETCH_STALE_THRESHOLD_MS = 10 * 60 * 1000;
  const CRON_STALE_THRESHOLD_MS = 90 * 60 * 1000;

  // ---------- runtime state ----------
  let lastSurface = null;       // last successfully parsed JSON
  let lastFetchAt = null;       // wall-clock ms of last successful fetch
  let lastRunAt = null;         // wall-clock ms of the cron's last ok run

  // ---------- DOM helpers ----------

  function $(sel) { return document.querySelector(sel); }
  function $$(root, sel) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function resolvePath(obj, path) {
    if (obj == null) return undefined;
    const parts = path.split('.');
    let cur = obj;
    for (const p of parts) {
      if (cur == null) return undefined;
      cur = cur[p];
    }
    return cur;
  }

  // Apply data-bind paths within `root` against `data`.
  //   data-bind="path"          → textContent
  //   data-bind-html="path"     → innerHTML (Kahneman body needs <em>)
  //   data-class="path"         → add/remove class derived from value;
  //                               previous dynamic class tracked via
  //                               dataset.dynClass for clean swaps on refresh
  //   data-class-if-emdash="X"  → toggle class X when textContent is "—"
  //   data-hide-if-empty        → display:none when textContent is empty
  function applyBindings(root, data) {
    $$(root, '[data-bind]').forEach((el) => {
      const path = el.getAttribute('data-bind');
      const v = resolvePath(data, path);
      el.textContent = (v == null || v === '') ? '' : String(v);
    });

    $$(root, '[data-bind-html]').forEach((el) => {
      const path = el.getAttribute('data-bind-html');
      const v = resolvePath(data, path);
      el.innerHTML = (v == null) ? '' : String(v);
    });

    $$(root, '[data-class]').forEach((el) => {
      const path = el.getAttribute('data-class');
      const v = resolvePath(data, path);
      const prev = el.dataset.dynClass;
      if (prev) el.classList.remove(prev);
      if (v) {
        el.classList.add(String(v));
        el.dataset.dynClass = String(v);
      } else {
        delete el.dataset.dynClass;
      }
    });

    $$(root, '[data-class-if-emdash]').forEach((el) => {
      const cls = el.getAttribute('data-class-if-emdash');
      const isEmdash = (el.textContent || '').trim() === '—';
      el.classList.toggle(cls, isEmdash);
    });

    $$(root, '[data-hide-if-empty]').forEach((el) => {
      const empty = !el.textContent || !el.textContent.trim();
      el.style.display = empty ? 'none' : '';
    });
  }

  // Clone the <template>'s child once, apply per-record bindings, return
  // the resulting element. rowClassFn (optional) returns a single class
  // string to add to the row (e.g. "promoted", "now").
  function cloneRow(templateId, record, rowClassFn) {
    const tpl = $('#' + templateId);
    if (!tpl) return null;
    const fragment = tpl.content.cloneNode(true);
    const row = fragment.firstElementChild;
    if (!row) return null;
    applyBindings(row, record);
    // Session-marker support: accum records carry a stable key + raw value;
    // expose them as data-* so applySessionMarkers can diff across visits.
    if (record.key != null) row.dataset.key = record.key;
    if (record.value != null) row.dataset.value = String(record.value);
    if (typeof rowClassFn === 'function') {
      const cls = rowClassFn(record);
      if (cls) row.classList.add(cls);
    }
    return row;
  }

  function populateRowList(containerId, templateId, records, rowClassFn) {
    const container = $('#' + containerId);
    if (!container) return;
    container.replaceChildren();
    if (!Array.isArray(records)) return;
    records.forEach((rec) => {
      const row = cloneRow(templateId, rec, rowClassFn);
      if (row) container.appendChild(row);
    });
  }

  // ---------- populate the surface ----------

  function populate(surface) {
    if (!surface || typeof surface !== 'object') return;

    // Compute helper fields the markup binds against but the JSON doesn't
    // ship literally.
    const anchor = surface.state && surface.state[3] && surface.state[3].qual;
    const stateQualifier = (anchor && anchor !== 'not yet started')
      ? `phase 1 · day ${dayInCurriculumFromVitals(surface)}`
      : 'phase 1 · not yet started';
    const pendingQual = `${(surface.pending || []).length} · awaiting human`;

    const enriched = Object.assign({}, surface, {
      state_qualifier: stateQualifier,
      pending_qualifier: pendingQual,
    });

    // Top-level scalar bindings (masthead title/sub, vitals, kahneman fields,
    // state_qualifier, pending_qualifier).
    applyBindings(document, enriched);

    // Kahneman visibility — block disappears entirely when no trigger.
    const kahnemanEl = $('#kahneman');
    if (kahnemanEl) {
      kahnemanEl.classList.toggle('visible', !!surface.kahneman);
    }

    // Topline health goes red when the pipeline tripwire has fired.
    const healthEl = $('#tl-health');
    if (healthEl) {
      healthEl.classList.toggle(
        'warn', !!(surface.topline && surface.topline.health_warn));
    }

    // Repeating sections — clone the template once per record.
    populateRowList('state-rows', 'state-row-template', surface.state);
    populateRowList(
      'pending-rows',
      'pending-row-template',
      surface.pending,
      (rec) => rec.promoted ? 'promoted' : null,
    );
    populateRowList('accum-rows', 'accum-row-template', surface.accumulating);
    populateRowList(
      'tt-rows',
      'tt-row-template',
      surface.timetable,
      (rec) => rec.row_class || null,
    );

    // Cache for the clock's reference + stale detection.
    lastSurface = surface;
    lastFetchAt = Date.now();
    if (surface.vitals && surface.vitals.last_run_iso) {
      lastRunAt = Date.parse(surface.vitals.last_run_iso);
    } else {
      lastRunAt = null;
    }
    if (surface.vitals && typeof surface.vitals.cron_interval_seconds === 'number') {
      cronIntervalMs = surface.vitals.cron_interval_seconds * 1000;
    }
    checkStale();

    // Must run after the accum rows exist and their data-value attrs are set.
    applySessionMarkers();
  }

  // ---------- session markers ----------
  //
  // Tracks what changed since the operator's previous *visit*. A visit is
  // "new" when >1h has passed since the last recorded page load. On a new
  // visit, accum rows whose value differs from the previous snapshot get a
  // teal ‣ marker. Within an hour, reloads keep the markers (same session)
  // so the operator can re-check without losing the indicators.

  const SESSION_GAP_MS = 60 * 60 * 1000;
  const SESSION_KEY = 'algotrading_paper_session_v1';

  function applySessionMarkers() {
    let prev;
    try {
      prev = JSON.parse(localStorage.getItem(SESSION_KEY) || 'null');
    } catch {
      prev = null;
    }

    const now = Date.now();
    const rows = $$(document, '.accum-row[data-key]');
    const currentValues = {};
    rows.forEach((row) => { currentValues[row.dataset.key] = row.dataset.value; });

    const isNewSession = !prev || (now - prev.timestamp) > SESSION_GAP_MS;

    if (isNewSession && prev) {
      rows.forEach((row) => {
        const before = prev.values ? prev.values[row.dataset.key] : undefined;
        const after = row.dataset.value;
        if (before !== undefined && before !== after) {
          row.querySelector('.marker')?.classList.add('active');
        }
      });
      const qual = $('#session-qualifier');
      if (qual) {
        const hoursAgo = Math.max(1, Math.round((now - prev.timestamp) / SESSION_GAP_MS));
        qual.textContent = `since ${hoursAgo}h ago`;
      }
      localStorage.setItem(SESSION_KEY, JSON.stringify({ timestamp: now, values: currentValues }));
    } else if (!prev) {
      // First visit ever — snapshot, no markers.
      localStorage.setItem(SESSION_KEY, JSON.stringify({ timestamp: now, values: currentValues }));
    }
    // Continuing session (<1h): leave existing markers as they are.
  }

  // The surface JSON only carries day-1 info in the qualifier. Derive a
  // best-effort current-day-in-curriculum from the last_run_iso if anchored.
  function dayInCurriculumFromVitals(surface) {
    if (!surface || !surface.vitals || !surface.vitals.last_run_iso) return 1;
    // Use the timetable to find the "now" row's offset, fall back to 1.
    if (Array.isArray(surface.timetable)) {
      for (const row of surface.timetable) {
        if (row.row_class === 'now' && typeof row.what === 'string') {
          const m = row.what.match(/day\s+(\d+)/);
          if (m) return parseInt(m[1], 10);
        }
      }
    }
    return 1;
  }

  // ---------- stale indicator ----------

  function setStale(isStale, msg) {
    const el = $('#stale-indicator');
    if (!el) return;
    if (isStale) {
      el.textContent = msg || 'surface stale';
      el.classList.add('visible');
    } else {
      el.classList.remove('visible');
      el.textContent = '';
    }
  }

  // Two independent staleness conditions:
  //   - cron stale:   last successful cron run is far behind expected
  //                   (GitHub Actions cron is best-effort; this catches
  //                   "scheduler appears stopped" vs "just running late")
  //   - fetch stale:  the PWA's surface.json fetches have been failing
  //                   (network down, GH Pages outage, JSON corrupt)
  // Each shows a distinct masthead message so the operator can tell
  // which side is broken.
  function checkStale() {
    const now = Date.now();

    if (lastRunAt && (now - lastRunAt) > CRON_STALE_THRESHOLD_MS) {
      const min = Math.floor((now - lastRunAt) / 60000);
      setStale(true, `cron stale · last run ${min}m ago`);
      return;
    }
    if (lastFetchAt && (now - lastFetchAt) > FETCH_STALE_THRESHOLD_MS) {
      const min = Math.floor((now - lastFetchAt) / 60000);
      setStale(true, `surface stale · last fetch ${min}m ago`);
      return;
    }
    if (!lastFetchAt) {
      setStale(true, 'surface stale · waiting for first data');
      return;
    }
    setStale(false);
  }

  // ---------- vitals ticker ----------
  //
  // The populator writes initial "last run" / "next run" text from the
  // JSON snapshot, but those strings would freeze for the 5-min refresh
  // interval if we left it at that. Recompute every second from cached
  // lastRunAt so the elapsed/remaining display ticks live.

  function fmtElapsed(ms) {
    if (ms < 0) ms = 0;
    const totalSec = Math.floor(ms / 1000);
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    return `${m}m ${s.toString().padStart(2, '0')}s`;
  }

  function tickVitals() {
    if (lastRunAt == null) return;
    const now = Date.now();
    const lastEl = $('#last-run');
    const nextEl = $('#next-run');
    if (lastEl) lastEl.textContent = `${fmtElapsed(now - lastRunAt)} ago`;
    if (nextEl) {
      const remaining = (lastRunAt + cronIntervalMs) - now;
      if (remaining > 0) {
        nextEl.textContent = fmtElapsed(remaining);
      } else {
        // Past the expected next-run time. Show "now" for the first
        // minute of overdue (GitHub cron is usually a touch late), then
        // switch to "+Xm overdue" so the operator can see the magnitude
        // of the lag at a glance instead of "now" sticking for hours.
        const overdueMin = Math.floor(-remaining / 60000);
        nextEl.textContent = overdueMin === 0
          ? 'now'
          : `+${overdueMin}m overdue`;
      }
    }
  }

  // ---------- masthead timestamp (current wall-clock UTC) ----------

  function updateTimestamp() {
    const now = new Date();
    const yyyy = now.getUTCFullYear();
    const mm = String(now.getUTCMonth() + 1).padStart(2, '0');
    const dd = String(now.getUTCDate()).padStart(2, '0');
    const hh = String(now.getUTCHours()).padStart(2, '0');
    const min = String(now.getUTCMinutes()).padStart(2, '0');
    const el = $('#timestamp');
    if (el) el.textContent = `${yyyy}-${mm}-${dd} · ${hh}:${min} UTC`;
  }

  // ---------- paddle clock ----------

  function updateClock() {
    const now = Date.now();
    const paddle = $('#paddle');
    const ringArc = $('#ring-arc');
    if (!paddle || !ringArc) return;

    // Paddle: 58s sweep + 2s hold per minute
    const intoCycle = now % PADDLE_CYCLE_MS;
    const angle = (intoCycle < PADDLE_SWEEP_MS)
      ? (intoCycle / PADDLE_SWEEP_MS) * 360
      : 360;
    paddle.style.transform = `rotate(${angle}deg)`;

    // Ring arc: fills over cron cycle from the last ok run
    if (lastRunAt != null) {
      const elapsed = (now - lastRunAt) % cronIntervalMs;
      const pct = Math.min(100, (elapsed / cronIntervalMs) * 100);
      ringArc.setAttribute('stroke-dashoffset', String(100 - pct));
    } else {
      ringArc.setAttribute('stroke-dashoffset', '100');  // empty
    }
  }

  // ---------- fetch ----------

  async function fetchSurface() {
    const url = `./surface.json?t=${Date.now()}`;
    const resp = await fetch(url, { cache: 'no-store' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const text = await resp.text();
    if (!text || !text.trim()) throw new Error('empty body');
    return JSON.parse(text);
  }

  async function refresh() {
    try {
      const data = await fetchSurface();
      populate(data);
    } catch (err) {
      console.warn('surface refresh failed:', err);
      if (!lastSurface) {
        setTimeout(refresh, RETRY_INTERVAL_MS);
      }
      checkStale();
    }
  }

  // ---------- boot ----------

  function start() {
    updateTimestamp();
    updateClock();
    refresh();
    setInterval(updateClock, 100);
    setInterval(tickVitals, 1000);
    setInterval(updateTimestamp, 30 * 1000);
    setInterval(refresh, REFRESH_INTERVAL_MS);
    setInterval(checkStale, 60 * 1000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
