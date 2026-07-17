# Build queue

Operator-managed queue of code work that's been agreed but deferred to
a later session. Peer to pending.md, same YAML-in-markdown format. Read
by scripts/generate_surface.py for the punch list's § iv (build)
section. Not auto-generated — operator edits by hand.

When a build item ships, delete its line here. The punch list's
done-overlay is a UI affordance only; this file is the source of truth.

Phase 1b items (phase1-review.md § 5) carry their archive-trigger
deadlines in `when`. Sequencing is one-factor-at-a-time per
philosophy.md: loop-proof (null) → candidates-vs-null → external data
(v2). Live roster caps at 2 candidates + null — not a strategy zoo.

Each item:
  - `thing`    (required) — short headline
  - `detail`   (optional) — one-line clarification
  - `when`     (optional) — "Nd" for N days, or "open" (default open)
  - `kind`     — always `build` for this file

---

- thing: Null variant live on VPS
  detail: "random-signal placebo through signals.py → execute.py on the cron · first live loop · archive trigger 2026-07-24"
  when: 8d
  kind: build

- thing: Friday review automation
  detail: "full 4G bear-case mode in adversarial_cron.py + Friday crontab line · first machine-generated review 2026-07-17"
  when: 1d
  kind: build

- thing: compare.py A/B comparator
  detail: "candidate-vs-null, p<0.05 over 100+ trades · the gate-2 instrument · precedes the candidate roster"
  when: open
  kind: build

- thing: Sharpe + max drawdown in replay.py
  detail: "strategic-success bar (Sharpe>1.0, DD<15%) unmeasurable without them"
  when: open
  kind: build

- thing: Learnings ledger + dashboard
  detail: "keyed to philosophy.md's five knowledge-success questions · learnings.json + surface page + Phase 1b countdown · archive trigger 2026-07-31"
  when: 15d
  kind: build

- thing: LLM candidate synthesis + roster registration
  detail: "historical retail-algo lens · scored by edge-per-constraint-slot in 6-month replay · top 2 + null · archive trigger 2026-07-31"
  when: 15d
  kind: build

- thing: Model routing per LLM role
  detail: "Haiku 4.5 nightly skeptic · frontier model for Friday review + synthesis · CLAUDE_MODEL env on VPS"
  when: open
  kind: build

- thing: Close the seam — autonomous foundry
  detail: "decision-log 2026-07-17 spec · cloud agent (implement+epitaphs) + VPS cron conditions (synthesis+gauntlet) + escalating survival bar · FIRST TASK next session"
  when: 2d
  kind: build

- thing: Wire the digest email
  detail: "Gmail connector authorized · read reports/digest-*.md, send · trivial once tools load in a fresh session"
  when: 2d
  kind: build
