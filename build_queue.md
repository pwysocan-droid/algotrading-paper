# Build queue

Operator-managed queue of code work that's been agreed but deferred to
a later session. Peer to pending.md, same YAML-in-markdown format. Read
by scripts/generate_surface.py for the punch list's § iv (build)
section. Not auto-generated — operator edits by hand.

When a build item ships, delete its line here. The punch list's
done-overlay is a UI affordance only; this file is the source of truth.

Each item:
  - `thing`    (required) — short headline
  - `detail`   (optional) — one-line clarification
  - `when`     (optional) — "Nd" for N days, or "open" (default open)
  - `kind`     — always `build` for this file

---

- thing: Cron-variance row on surface
  detail: std dev of run intervals over 24h · add to generate_surface.py
  when: open
  kind: build

- thing: Shadow signals implementation
  detail: post-Week-2 if scheduler migration ships first · schema in decision-log
  when: open
  kind: build

- thing: Bar-coverage steady-state verification
  detail: confirm 70-90% target after 48h of --minutes=90 in effect
  when: open
  kind: build
