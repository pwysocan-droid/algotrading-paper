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

- thing: Nightly shadow-replay parity check
  detail: "replay last 24h over the live bars with the same variants; deterministic strategies must reproduce live signals 1:1 — any divergence = engine bug caught same-day"
  when: open
  kind: build

- thing: Weekly sim-to-live calibration report
  detail: "per live arm: fire rate / win rate / expectancy / exit-mix, live vs backtest-predicted · feeds Friday review + dashboard · validates the factory"
  when: open
  kind: build

- thing: "Audit Tier-2 backlog (2026-07-17 four-agent audit)"
  detail: "runs.bars_added counts upserts not inserts (17x inflated, feeds skeptic); parity_check must exclude the mutable trailing 90min of bars; replay entry-bar exit skip (bars[i+2:] vs live) + time-exit anchor one bar late; gate-1 uptime should filter kind='cron'; trade_cycle needs its own runs audit rows; entropy params half-plumbed (entropy_window/n_bins ignored in _entropy_at calls) + coil-persistence rule dropped; omori volume baseline includes signal bar; same-bar tie-break ordering live (id ASC) vs replay (alphabetical); system_state stop-out scope live-portfolio vs null-only in replay; pages.yml negative-staleness guard; log rotation on vps/logs"
  when: open
  kind: build

- thing: Maker/limit fills in LIVE paper execution
  detail: "replay half SHIPPED 2026-07-17 (fill_model='maker', validated 12/12 matched pairs) · live half = limit orders in execute.py, deliberately deferred until a strategy earns it (decision-log 2026-07-17)"
  when: open
  kind: build

- thing: Context layer (Layer 2) revival
  detail: "funding rates / F&G / on-chain via context_keys — data mined less exhaustively than OHLCV; needs decision-log entry per roadmap"
  when: open
  kind: build

- thing: Ablation harness — verify epitaph diagnoses
  detail: "learning-quality audit 2026-07-18 · foundry specs gain an ablation_spec (params override defining the placebo version); gauntlet runs idea+ablation pairs; retroactively run the ablations the big lessons rest on (r004 engine ungated; asian-london random-hour placebo; entropy term ablated)"
  when: open
  kind: build

- thing: Pre-mortem critic before implementation
  detail: "learning-quality audit 2026-07-18 · adversarial LLM pass over each round spec (registry + premise checks) that tries to kill ideas on paper before any implementation cost; would have stopped 2 of 5 r002 ideas"
  when: open
  kind: build

- thing: Shadow-arm forward report
  detail: "weekly aggregation of shadow signals (all disabled variants, live-recorded) vs their gauntlet-predicted fire rates + hypothetical outcomes from bars — the forward-test scoreboard"
  when: open
  kind: build
