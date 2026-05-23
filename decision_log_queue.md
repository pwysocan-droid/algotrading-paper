# Decision-log queue

Operator-managed queue of decision-log entries that need writing but
haven't been written yet. Peer to pending.md, same YAML-in-markdown
format. Read by scripts/generate_surface.py for the punch list's
§ iii (log) section. Not auto-generated — operator edits by hand.

When an entry is written and committed to decision-log.md, delete its
line here. Items are not "done-toggled" away — the punch list's
done-overlay is a UI affordance; the source of truth is this file.

Each item:
  - `thing`    (required) — short headline
  - `detail`   (optional) — one-line clarification
  - `when`     (optional) — "Nd" for N days, or "open" (default open)
  - `kind`     — always `log` for this file

---

- thing: Variant-explosion-to-Day-1 entry
  detail: names parameter-sweep vs factor-exploration distinction · 12 variants list
  when: open
  kind: log

- thing: Shadow-signal schema + discipline entry
  detail: exploration vs validation boundary · table schema · graduation criteria
  when: open
  kind: log

- thing: ".env.template exposure entry"
  detail: caught, rotated, unlogged · post-incident write-up
  when: open
  kind: log
