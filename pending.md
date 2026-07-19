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

- thing: Phase 1b review — extend-or-archive, hard stop
  detail: phase1-review.md § 5 terms · gate 2 re-posed against the live 3-arm roster
  when: 29d
  kind: gate
  promoted: true

- thing: First candidate-vs-null A/B readout
  detail: compare.py once arms accumulate closed trades · promotion bar p<0.05 over 100+
  when: open
  kind: ops

- thing: "Nightly skeptic · 2026-07-19"
  detail: "Your pipeline is running fine—which masks that nothing is actually happening. Seven consecutive c..."
  when: open
  kind: ops
