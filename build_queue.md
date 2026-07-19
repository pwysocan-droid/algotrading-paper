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

- thing: "Combination stage — ensemble of sub-threshold signals (Tier-0 harvest)"
  detail: "the fee floor binds per DEPLOYED RULE, not per signal: combine decorrelated real-but-small structures from the graveyard (weekend, regime gate, gap) into one portfolio-level rule that clears the floor jointly · Grinold-Kahn breadth · REQUIRES a human decision-log call on whether this crosses the no-ML lock"
  when: open
  kind: build

- thing: "Sequential e-value inference for the live A/B (Tier-0 harvest)"
  detail: "replace fixed-n gate (p<0.05 @ 100 closes) with always-valid sequential testing (e-processes/mSPRT) in compare.py — valid at every peek, no evidence wasted on the slowest channel we have"
  when: open
  kind: build

- thing: "Snooping ledger + multiplicity control (Tier-0 harvest)"
  detail: "count effective comparisons against the archive (ideas x params x ablations x registry feedback), apply deflated-Sharpe / Reality-Check style correction to every gauntlet verdict; today best-of-N selection is acknowledged only in prose"
  when: open
  kind: build

- thing: "Surrogate-archive false-positive rate (Tier-0 harvest)"
  detail: "re-run a sample of dead strategies on phase-randomized/shuffled bars — the pipeline's empirical false-positive rate; complements power calibration (planted edges) which shipped 2026-07-18"
  when: open
  kind: build

- thing: "Lessons as falsifiable claims (Tier-0 harvest)"
  detail: "restate each failure_lesson as a prediction, score it against each new round's outcomes, retire losers — the registry currently accretes prose that is never tested"
  when: open
  kind: build

- thing: "Failure-mode taxonomy + repeat-offender rate (imports harvest)"
  detail: "recode 28 epitaphs into a controlled defect vocabulary, Pareto by mode, coverage matrix; formulation gate: new ideas must clear top-3 modes; repeat-offender rate = the first metric OF the learning loop itself"
  when: open
  kind: build

- thing: "Winner's-curse shrinkage on any passer (imports harvest)"
  detail: "shrink a passing idea's effect toward the empirical prior of all prior effects (clustered near zero); the SHRUNKEN number feeds live-confirmation power calcs, not the raw backtest number"
  when: open
  kind: build

- thing: "10k-random-rules null distribution (audit harvest)"
  detail: "best-of-N benchmark for the daily pipeline: generate thousands of random rules matching our trade-frequency profile, record best-of-batch net effect distribution — deflates every future 'best of round' claim; uncontroversial half of the ceiling study"
  when: open
  kind: build

- thing: "Breadth expansion 5 -> 15+ symbols (audit harvest)"
  detail: "5 coins at 0.6-0.8 correlation are ~2 effective series; more coins = direct power gain + unlocks cross-sectional long-short (lower per-trade sigma); bounded by Alpaca's crypto list"
  when: open
  kind: build

- thing: "Registry compression audit (audit harvest)"
  detail: "do the 28 write-ups compress to <8 family-level exclusions? if yes the generator is resampling known-dead regions; one family-level exclusion is worth ~50 candidate tests"
  when: open
  kind: build

- thing: "Literature-prior candidate: slow momentum (survey harvest)"
  detail: "12-week BTC/ETH momentum, multi-week holds, maker-friendly entries — the 1-8 week persistence band is published, amortizes the fee floor, and sits OUTSIDE our archive's measurable range; register disabled, evaluate primarily via the live/shadow channel where our instrument still works"
  when: open
  kind: build

- thing: "Referee defense backlog (Run-3 hostile review, 2026-07-19)"
  detail: "exit-grid sensitivity on key corpses INCL SYMMETRIC exits + per-entry exit-type decomposition (attack 2); bootstrap CIs on every registry entry (4); per-idea vs-null two-sample test in gauntlet output (8); unconstrained expectancy alongside constrained (9); drawdown ruin-semantics audit — the 139.7% entry (1c); purged/embargoed CV + ML positive control for ceiling re-run (6); cost-tier sensitivity table over registry verdicts (7); lesson n-tagging with n<3 non-binding + blind-resurrection replication (3); spec-vs-code independent reimplementation spot check (10). Defenses already standing: end-to-end positive control now IN CI (1), 2026 holdout embargoed since inception (5), null distribution measured (8-partial), maker/cost sensitivity machinery (7-partial)"
  when: open
  kind: build

- thing: "Archival re-analyses (Run-5 harvest, need re-runs for trade records)"
  detail: "maker-fee re-scoring of all corpses (#1 — how many does the 24h+maker band resurrect); MFE/MAE exit autopsy + optimal tp/sl grid (#2); hold-extension census on time-exits (#6); pooled death-regime fingerprint (#8); symbol ablation (#9); live fill audit methodology now, powered in a month (#10); single-condition gate decomposition (#4, joins placebo-gate ablation). Note: trade-level records only exist r004+, so corpus items re-run r001-r003 variants first"
  when: open
  kind: build

- thing: "Cross-engine gate transfer test (Run-6 prescription; can CLOSE the family)"
  detail: "freeze r003's slot-scarcity gate rule; apply to ALL engines' historical trade streams (needs r001-r003 re-runs with trade capture); sign test on gated-minus-ungated delta per engine + shuffled-outcome placebo; null result closes the gate family permanently under the 2026-07-19 freeze lesson"
  when: open
  kind: build

- thing: "SRE hardening batch (Run-7, top items)"
  detail: "data contracts on fetch (gap/null/schema asserts, loud fail — the silent-partial-data hole); external watchdog ping (healthchecks.io — needs operator signup); credential weekly self-test; timeout wrappers on all cron jobs; git artifact-store split (trader.db/context.db out of git eventually); provider-side LLM spend cap (operator sets); VPS weekly snapshot + crontab-in-repo"
  when: open
  kind: build
