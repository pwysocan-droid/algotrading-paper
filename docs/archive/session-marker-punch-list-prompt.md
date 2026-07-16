# Session marker + punch list — for Claude Code

Two related changes. Ship as one logical unit since they share
the same data sources and navigation contract.

---

## The prompt

```
Two additions to the surface. Same commit, since they're a
logical unit and share data sources.

# Required reading first

1. /surface-philosophy.md — the design discipline. Most
   relevant: the canonical row grammar, three-color discipline,
   the "shortening the time between a problem existing and the
   operator seeing it" framing.

2. /surface/index.html — the live surface. You'll modify this.

3. /surface/punch-list.html — new file. The reference design
   for this is in mobile-preview.html in the project root (look
   for the punch-list block). Copy its structure exactly.

4. /pending.md — source of truth for pending items. The punch
   list reads from here.

# Addition 1 — Session marker on the live surface

The live surface tracks what the operator has and hasn't seen
since their last visit. On a new visit (defined as >1 hour gap
since previous page load), accumulating rows whose value has
changed get a small teal ‣ marker between count and delta.

## Data model

Two localStorage entries:

- algotrading_paper_session_v1 — { timestamp, values: {key:
  count} }

The "key" is a stable identifier per row (bars, cron_runs,
llm_calls, decisions, letters, reviews, bar_coverage). The
"count" is the row's current numeric value as a string.

## DOM changes

Each .accum-row gets two new data attributes set by app.js
from surface.json:

  <div class="accum-row" data-key="bars" data-value="41927">

And a new cell between .count and .delta:

  <div class="marker">‣</div>

Grid template for .accum-row changes from
"1fr 80px 50px 90px" to "1fr 80px 12px 50px 90px".

## CSS (add to existing stylesheet)

.accum-row .marker {
  font-size: 11px;
  color: var(--teal);
  text-align: center;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.2s;
}
.accum-row .marker.active { opacity: 1; }

## JS logic (add to app.js)

Function applySessionMarkers() runs after populate() fills the
DOM with surface.json data. Read localStorage's previous
snapshot. If (now - previous.timestamp) > 1 hour:

  - For each .accum-row, compare current data-value to
    previous.values[data-key]. If different, add .active to
    the row's .marker element.
  - Update the section-label qualifier from "last 24h" to
    "since Nh ago" where N is hours since previous timestamp.
  - Store new snapshot.

If no previous snapshot exists (first visit ever): store
snapshot, no markers.

If gap is <1 hour: do nothing. Markers from current session's
initial load (if any) stay visible until next gap. This is
deliberate — operator can reload to re-check without losing
the indicators.

# Addition 2 — Punch list page

Separate page at /surface/punch-list.html. Same design language
as the live surface but focused on task tracking. Mobile-
preview.html in project root contains the reference design —
copy its markup, CSS, and JS exactly.

## Page structure

- Masthead: project title left, "← live" link right.
- Summary bar: 4 stats (due ≤7d, due ≤14d, open, done this
  week). Each pulls from the data, not hardcoded.
- Four sections, each with section-label idx/name/count:
    i. gates       — kind=gate items from pending
    ii. ops        — kind=ops items from pending
    iii. log       — decision-log entries to write
    iv. build      — code work deferred from earlier sessions

## Data sources

- pending.md: same file the live surface already reads.
  Sections i and ii filter by `kind` field.
- decision_log_queue.md: NEW file, peer to pending.md, same
  YAML-ish format. Holds the queue of decision-log entries that
  need writing but haven't been written yet. Section iii reads
  this.
- build_queue.md: NEW file, peer to pending.md, same format.
  Holds code work that's been agreed but deferred. Section iv
  reads this.

Create both new files with the items currently shown in the
mobile-preview.html reference design. Document the format
inside each file as a comment block at the top.

## generate_surface.py changes

Currently generates surface.json. Now also generates
punch_list.json — same JSON shape but with:

  {
    "summary": { "due_7d": N, "due_14d": N, "open": N, "done_this_week": N },
    "gates": [...],
    "ops": [...],
    "log": [...],
    "build": [...]
  }

Each item array has the same shape as pending entries
currently do (when, when_class, thing, detail, kind, promoted).

The punch list page fetches punch_list.json on load, populates
the page from it. Same template-cloning pattern as the live
surface.

## Done-state tracking

Click-to-toggle on the .checkbox glyph. Toggled state persists
to localStorage under algotrading_paper_punch_v1 (a Set of item
IDs). Done rows get .done class — items stay visible with
strikethrough so the operator can see what's been cleared.

This is operator-side state only. It does NOT modify pending.md
or the queue files. Those are only modified through normal
editing. The done-overlay is purely a UI affordance for visual
acknowledgment.

When generate_surface.py regenerates punch_list.json (e.g., an
item is removed from pending.md), the page reflects that on
next load. localStorage IDs that no longer have matching items
in the JSON are silently ignored.

## Navigation

- Live surface (/surface/index.html): in the pending section's
  qualifier, the word "all" is a quiet underlined link to
  punch-list.html. Reference design shows exact placement and
  styling (.ql-link class).
- Punch list (/surface/punch-list.html): "← live" link in
  top-right of masthead, links to ./

# Order of operations

1. Create /decision_log_queue.md and /build_queue.md, populated
   from the reference design's hardcoded items. Document format
   in each.
2. Update generate_surface.py to also write
   /surface/punch_list.json. Run once locally to confirm output
   shape.
3. Create /surface/punch-list.html. Wire it to fetch
   punch_list.json. Verify it renders.
4. Update /surface/index.html with the session marker DOM
   changes and CSS.
5. Update /surface/app.js with the applySessionMarkers()
   function.
6. Add the "all" link in the pending section qualifier of
   /surface/index.html.
7. Verify both pages locally before commit.

# What you do NOT do

- Do NOT redesign anything. mobile-preview.html is the spec.
- Do NOT add server-side state for done-tracking. localStorage
  only.
- Do NOT auto-generate decision_log_queue.md or build_queue.md
  from other files. They are operator-edited.
- Do NOT add notifications, badges, or any push affordances.
  The punch list is consulted, not pushed to.

Ship as one commit. Commit message:
"Session marker on live surface + punch list page."
```

---

## After Claude Code finishes

1. Visit `https://[username].github.io/algotrading-paper/surface/`
   — verify no markers appear (first visit ever, by definition).
2. Close the tab. Wait at least one cron cycle so a value
   changes. Reopen.
3. The first reload within the hour should still show no markers
   (same session). Force-close and reopen >1 hour later — markers
   should appear on changed rows.
4. Click "all" in the pending qualifier — should navigate to the
   punch list.
5. Mark a few items done on the punch list. Reload. Verify they
   stay struck through.
6. Click "← live" — should return to the surface.

If the session marker never appears even after a >1 hour gap,
check that `applySessionMarkers()` is being called after
`populate()` (not before — it needs the data-value attributes
populated first).
