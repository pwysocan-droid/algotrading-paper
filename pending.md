# Pending

Operator-managed list of open items requiring human attention. Surfaced
in both INDEX.md (§ Pending decisions) and the live surface (§ Pending,
Tier 2). One source of truth, read by `render_index.py` and
`scripts/generate_surface.py`.

The format is a YAML list of records. Each item:

  - `thing`     (required) — short headline
  - `detail`    (optional) — one-line clarification
  - `when`      (required) — "Nd" for N days remaining, or "open"
  - `kind`      (required) — one of: gate, ops, log, build
  - `promoted`  (optional) — true marks the active gate (one max)

Order is rendered top-to-bottom. Add new items at the appropriate
position; resolve by deleting (and writing a decision-log entry if
the resolution is non-trivial). The "Nightly skeptic · ..." item is
machine-managed by adversarial_cron.py — replaced nightly, don't edit.

---

- thing: Phase 1 review — OVERDUE
  detail: review date 2026-07-12 passed unwritten · phase1-review.md decides extend-or-archive
  when: open
  kind: gate
  promoted: true

- thing: "Friday adversarial review · #2"
  detail: last full review W21 (2026-05-23) · Fridays 07-03 and 07-10 were missed · next 2026-07-17
  when: 1d
  kind: ops

- thing: Future-self letters · 2026-04-26 entries
  detail: convention set, letters pending since April
  when: open
  kind: ops

- thing: "Nightly skeptic · 2026-07-16"
  detail: "The pipeline is a metronome with no conductor. Seven consecutive clean runs, 81–82 bars added eac..."
  when: open
  kind: ops
