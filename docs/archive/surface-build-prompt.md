# Surface Build Prompt — for Claude Code

The prompt to give Claude Code in the algotrading-paper repo to
turn the static `mobile-preview.html` into a live PWA that reads
data from a JSON snapshot the cron generates.

This is a focused, bounded build. The visual design is finished —
do not redesign anything. The job is **plumbing**: read the JSON,
populate the existing markup, refresh on a cadence.

---

## The prompt

```
We are building the live surface for the algotrading-paper
project. The design is settled — do not redesign anything. Your
job is plumbing: take the existing `mobile-preview.html`, make
it read project data from a JSON file, and ship it as a static
PWA hosted on GitHub Pages.

# Required reading first

Read these in order before writing any code:

1. /surface-philosophy.md
   The design philosophy. Establishes what the surface is and is
   not. Most relevant: the "function-driven poetic solutions"
   principle, the row grammar (name → number → delta →
   sparkline), the three-color discipline (red for mechanism,
   teal for accumulation, gray for everything else).

2. /mobile-preview.html
   The completed v1 visual. Treat this as the design spec. The
   classes, the markup structure, the CSS — all final. Your
   build inherits all of it.

3. /PROJECT.md
   The project's architecture, schema, and the seven tables you
   will be reading from. Most relevant: the `runs`, `bars`,
   `trades`, `signals`, and `decisions` tables.

4. /pending.md
   The source of truth for pending items. If this file doesn't
   exist yet, see the "pending sourcing" section below.

# Architecture decision (already made — implement, don't debate)

- Vanilla HTML/CSS/JS. No framework. No build step.
- Data source: a single `surface.json` snapshot file that the
  cron generates every 5 minutes alongside its other writes.
  The PWA fetches this JSON on load and refreshes on a cadence.
- Hosting: GitHub Pages. The PWA is a static site that lives in
  /surface/ in the repo. GitHub Pages serves it from the main
  branch's /surface directory.
- No backend. No API. No database access from the browser.

# Build scope — three deliverables

## 1. /surface/index.html

The live surface. Start from `/mobile-preview.html` — copy the
entire file into /surface/index.html. Then make these changes:

a. Replace every hardcoded data value (timestamps, counts,
   sparklines, pending items, timetable rows, Kahneman block,
   etc.) with placeholder elements that have stable
   `data-bind="..."` attributes. For example:

   Before:
     <div class="value" id="last-run">2m 14s ago</div>

   After:
     <div class="value" data-bind="vitals.last_run_human"></div>

b. Keep every CSS class, every grid structure, every animation.
   The clock JS at the bottom of the file stays — its `lastRunAt`
   value gets populated from JSON at runtime instead of being
   hardcoded to "2m 14s before page load."

c. The Kahneman block is conditional. If `surface.json` has no
   `kahneman` key (no trigger firing today), the entire block
   should be `display: none` rather than empty. Per
   surface-philosophy.md, the block earns its weight by being
   rare — when nothing's firing, it disappears entirely.

d. The accumulating, state, pending, and timetable rows are
   driven by arrays in the JSON. Each section gets a
   `data-template` element (one hidden row per section that
   serves as the template) and the loader clones it once per
   data item, populating each cloned row's `data-bind` fields.

## 2. /surface/app.js

The data-loading and refresh logic. ~150-200 lines. Structure:

a. On page load: fetch `./surface.json?t={now}` (cache-bust with
   the current timestamp). On success, populate the page. On
   failure, show a small stale-data indicator in the masthead
   (a faint mono italic line: `surface stale · last update Xm
   ago`) and retry in 30s.

b. After populating: schedule a refresh every 5 minutes (the
   cron cadence). When a refresh succeeds, do a silent in-place
   update of all data-bound elements — do not re-flash the
   whole page, do not animate transitions, just replace the text
   content. The paddle clock continues running uninterrupted.

c. Provide a `populate(surfaceJson)` function that takes the
   full surface.json object and applies it to the DOM. This
   function is the *only* place that knows the shape of the
   JSON. Keep all other code free of JSON path strings.

d. The clock JS gets one change: `LAST_RUN_OFFSET_MS` is now
   computed from `surfaceJson.vitals.last_run_iso` instead of
   being hardcoded.

e. Handle the edge cases:
   - JSON is empty: show stale-data indicator, don't blank the
     page.
   - JSON is malformed: log to console, show stale-data
     indicator, keep prior data on screen.
   - A row's data is null: the row's number cell shows `—` in
     ghost-faint, the sparkline cell shows the empty pattern
     `▁▁▁▁▁▁▁▁` also in ghost-faint. This is the empty-state
     pattern the design already supports.

## 3. /scripts/generate_surface.py

The cron-side script that writes `surface.json` to /surface/
every run. Reads the project's SQLite DB, queries the relevant
tables, and writes one JSON file. Runs at the end of every cron
execution, AFTER the data layer, context layer, signal layer,
and execution layer have all written their rows. Idempotent —
running it twice in a row produces the same output.

Output shape (write this schema into a docstring at the top of
the script for reference):

```json
{
  "generated_at": "2026-05-17T19:24:01Z",
  "masthead": {
    "title": "algotrading-paper",
    "sub": "live"
  },
  "kahneman": null,
  // OR, when a trigger fires:
  // "kahneman": {
  //   "trigger": "day 1 · planning fallacy",
  //   "body_html": "You will <em>underestimate</em> how long...",
  //   "attribution": "— after Kahneman & Tversky, 1979"
  // },
  "vitals": {
    "last_run_iso": "2026-05-17T19:22:00Z",
    "last_run_human": "2m 14s ago",
    "next_run_human": "2m 46s",
    "uptime_recent": "46 of 47 ok · 97.9%"
  },
  "state": [
    {
      "name": "system uptime",
      "qual": "46 of 8064 expected · 28-day window",
      "figure": "0.6",
      "unit": "%",
      "spark": "▇▇▇▇▆▇▇▇",
      "spark_class": "growing"  // or "empty" or null
    },
    // ... three more
  ],
  "pending": [
    {
      "when": "10d",
      "when_class": "urgent",  // or "open"
      "thing": "Week 2 strategy-roster review",
      "detail": "Bollinger and MA-crossover survive, or replaced",
      "kind": "gate",
      "promoted": true
    },
    // ... etc
  ],
  "accumulating": [
    {
      "name": "bars",
      "count": "41,927",
      "delta": "+271",
      "delta_class": null,  // or "zero" or "note"
      "spark": "▁▁▁▂▃▅▆▇",
      "spark_class": null  // or "empty"
    },
    // ... etc
  ],
  "timetable": [
    {
      "when": "sun 5/17",
      "what": "curriculum day 1 · now",
      "tag": "●",
      "tag_class": "teal",
      "row_class": "now"
    },
    // ... etc
  ]
}
```

Sparkline generation uses Unicode block characters
(▁▂▃▄▅▆▇█). For each numeric series, fetch 8 buckets covering
the last 24 hours, normalize to [0, 7], map to the corresponding
block character. If all buckets are zero, use ▁▁▁▁▁▁▁▁ and set
spark_class to "empty". If the series is monotonically
increasing, set spark_class to "growing".

The Kahneman trigger logic: read decision-log.md or a separate
`kahneman_triggers.yaml` (your choice — make it whatever's
simplest for the operator to maintain). Triggers fire based on
project state (day index since project start, week-within-
curriculum, days-to-gate, days-after-major-decision, etc.). On
days with no trigger, set "kahneman": null.

## Pending sourcing

If `pending.md` doesn't exist yet, the cron script reads its
own structured-text format. Create `/pending.md` as a markdown
file with this shape:

```
# Pending

- thing: Week 2 strategy-roster review
  detail: Bollinger and MA-crossover survive, or replaced
  when: 10d
  kind: gate
  promoted: true

- thing: Friday adversarial review · #1
  detail: first operational rhythm · bear case only
  when: 5d
  kind: ops
```

The script parses this format. (YAML-in-markdown is fine; or
front-matter, or a separate pending.yaml — pick the most
operator-friendly option and document the choice.)

# Cron integration

After your three deliverables exist, add `generate_surface.py`
to whatever runs after the cron's main execute.py. The
project's existing cron pattern is the right place to wire it
in — find that and add one line.

In the GitHub Action that powers the cron, add a step AFTER
generate_surface.py runs:

```yaml
- name: Commit surface.json
  run: |
    git config user.email "cron@algotrading-paper"
    git config user.name "cron"
    git add surface/surface.json
    git diff --staged --quiet || git commit -m "surface update"
    git push
```

This commits the new JSON file every 5 minutes. GitHub Pages
serves the updated file automatically.

# GitHub Pages setup

In the repo settings: Pages → Source → Deploy from a branch →
main → /surface. Visit
https://[username].github.io/algotrading-paper/ to confirm.

# What you do NOT do in this prompt

- Do NOT redesign anything visual. The CSS in mobile-preview.html
  is final.
- Do NOT add features. No notifications. No buttons. No
  drilldown. The surface is read-only per surface-philosophy.md.
- Do NOT add a framework. Vanilla only.
- Do NOT use localStorage or any browser storage beyond the
  in-memory fetched JSON.
- Do NOT add analytics, error tracking, or any third-party
  scripts.
- Do NOT touch any other part of the algotrading-paper codebase
  except as needed for cron integration.

# What "done" means

1. Visiting `https://[username].github.io/algotrading-paper/`
   shows the surface with current data from the cron.
2. The data refreshes every 5 minutes without page reload.
3. The paddle clock keeps running through refreshes.
4. The Kahneman block appears only when a trigger fires.
5. If the cron stops running, the stale-data indicator appears
   in the masthead.
6. The three new files (`/surface/index.html`, `/surface/app.js`,
   `/scripts/generate_surface.py`) plus `/pending.md` are
   committed.
7. The GitHub Action is updated to commit `surface.json` every
   run.

Build it. Show me the diff when done. Don't ask permission for
the steps explicitly listed above; do ask if anything in this
prompt contradicts something in PROJECT.md or
surface-philosophy.md.
```

---

## What you do after Claude Code finishes this prompt

**1. Local smoke test before pushing.**

```bash
cd algotrading-paper
python scripts/generate_surface.py    # produces surface/surface.json
cd surface
python -m http.server 8000
# open http://localhost:8000 in a browser, verify it renders
```

Look for: paddle clock running, all four state rows populated,
accumulating rows showing the latest counts, no JS errors in
the browser console.

**2. Verify the JSON shape matches the spec.**

```bash
cat surface/surface.json | python -m json.tool | head -50
```

If anything looks off, the bug is in `generate_surface.py`, not
in the PWA. Fix at the source.

**3. Enable GitHub Pages.**

Repo settings → Pages → Source: Deploy from branch → Branch:
main, folder: /surface → Save.

Wait ~30 seconds, then visit
`https://[your-username].github.io/algotrading-paper/`

**4. Verify the cron commits the JSON.**

The next cron run (within 5 minutes) should push a new commit
named "surface update." Check the Actions tab on GitHub. If the
commit doesn't appear, the GitHub Action needs the
`contents: write` permission set on the job — Claude Code may
not have added this.

Add to the workflow if needed:

```yaml
permissions:
  contents: write
```

**5. Open the surface on your phone.**

The whole point. Bookmark it. Optionally use Safari's "Add to
Home Screen" to give it an app icon.

**6. Watch the paddle.**

For at least one full 5-minute cycle. Verify:
- The paddle sweeps smoothly across each minute
- The red ring arc gradually fills around the rim
- When the cron runs (the arc completes), the page reloads its
  data without a flash
- The "last run" time resets

---

## What's deferred (not in this build)

- **Empty-state design** for the trades / phase 2 gates
  sparklines. Currently `▁▁▁▁▁▁▁▁` in ghost-faint. Earns iteration
  once it ships and gets used. Decision: leave as-is for v1; if
  it reads as broken in real use, hide entirely.
- **Pending filling bars** — the deferred idea about days-
  remaining as spatial-position-within-window. Hold for v2.
- **Real-time updates** (WebSockets / SSE) — out of scope by
  philosophy. The surface obeys the cron's cadence.
- **Authentication** — public read, no writes. Anyone with the
  URL can see the surface. None of this is private data; the
  repo is public anyway.
- **Mobile PWA install** (manifest.json, service worker, offline
  mode). Add later if you start using the surface heavily. v1 is
  just a webpage.

---

## What to give Claude Code, literally

After this prompt is committed to the repo, hand Claude Code
the prompt block above as a single message. The "required
reading" section tells it which files to load first; the
"build scope" tells it exactly what to produce.

The prompt is intentionally specific. Claude Code's failure
mode on this kind of build is over-engineering — adding
frameworks, build steps, abstraction layers, "what if we want
X later" speculation. The explicit "what you do NOT do" section
exists to cut that off.
