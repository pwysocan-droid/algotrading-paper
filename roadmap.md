# Roadmap — algotrading-paper

A navigational document. Outline + to-do for the project as it stands
post-reframe (2026-04-26 entry on Claude as epistemological backbone).

This file is derived from PROJECT.md, philosophy.md, decision-log.md,
playbook.md, setup.md, and report-format-spec.md. If those disagree
with this file, those win. This file is for orientation — when
planning a week, glance here; when making a decision, go to the
source files.

---

## Thesis

Try wild ideas, leave behind whole categories of conventional wisdom,
let the LLM be radically unconventional in what it surfaces — paired
with statistical and financial discipline. Epistemological aggression
with methodological rigor. Phase 1 (paper, $0) tests whether the
*system* works through aggressive iteration. Phase 2 (real, $1,000)
is earned by data through three gates, not chosen by calendar.

---

## Outline

### What's being built

- Six-layer auto-trading system: Data → Context → Signal → Execution
  → Analytics → Learning
- Eight-table SQLite schema: bars, context_data, signals, trades,
  decisions, runs, recommendations, llm_calls (the eighth added by
  the reframe to log every Claude API call)
- Strategy registry supporting arbitrary parallel variants under a
  single shared position-limit ceiling
- Walk-forward tuner producing recommendations that humans review
  and promote (never auto-promoted)
- Claude API integrated from Week 1 in three roles:
  (a) feature extractor for sentiment / news, (b) weekly adversarial
  reviewer of results, (c) decision-log pattern-surfacer
- Markdown reports in v1 (snapshot) and v2 (temporal) patterns,
  rendered through a shared render module per the report-format spec
- INDEX.md at the repo root as the project hub page, regenerated
  after every artifact commit

### Phase structure

- **Phase 1 — paper, 9 weeks** (Week 0 synthesis + Weeks 1–8)
- **Phase 2 entry — all three gates pass:**
  1. ≥95% uptime over prior 4 weeks
  2. ≥1 A/B-validated promotion (p<0.05, 100+ trades)
  3. +30d P&L OR written override in decision-log
- **Phase 2 — real $1,000**, frozen variants and sources, parallel
  paper instance for continued experimentation
- **Phase 2 exit — any one fires:**
  1. Account drops below $700 (-30%)
  2. Real diverges from paper >50% over any 2-week window
  3. 8 weeks elapsed → mandatory review

### Operating constraints

- $200/trade max, $1,000 total exposure, 5 concurrent positions
- Risk controls: -3% stop, +5% target, 24h time exit, 1 trade per
  symbol per hour cooldown
- Crypto only Phase 1 (BTC, ETH, SOL, LINK, AVAX) — equities deferred
  to v2
- One factor at a time, no factorial designs at retail scale
- LLM never decides trades, never decides what the project is

---

## To-do

### Pre-flight (before Week 0)

- [x] Alpaca paper account created, API keys saved outside repo
- [x] GitHub repo created, `.env` gitignored, GitHub Actions secrets
      configured
- [x] Five project files committed: PROJECT.md, philosophy.md,
      decision-log.md, playbook.md, setup.md
- [ ] **Anthropic API key generated** (Week 0, not Week 7, per
      reframe)
- [x] Reframe entry pasted into top of decision-log.md
- [x] week-0-synthesis.md committed
- [x] report-format-spec.md committed
- [x] roadmap.md committed
- [x] philosophy.md and decision-log.md updated with the two
      animating disciplines

### Week 0 — Synthesis (complete)

- [x] Session 1: criteria question — six demotion criteria, five
      elevation criteria with paired discipline checks
- [x] Session 2: ranked strategy candidates across five clusters —
      24 candidates surfaced, 13 kept (6 clean / 7 probational), 11
      demoted
- [x] Session 3: methodological-principles audit — 10 existing
      methodologies audited, 3 kept clean, 4 kept with notes, 1 kept
      as stance, 2 flagged for Week 8, 1 build-quality flag for
      Week 1
- [x] week-0-synthesis.md finalized

### Week 1 — Skeleton + LLM integrated + render layer

- [ ] Schema + migrations in `db.py` (versioned, paired
      `.up.sql` / `.down.sql`, `schema_migrations` table, tested);
      adds eighth table `llm_calls`
- [ ] `fetch.py` against both fixture and live
- [ ] `render.py` — v1 renderer + utility functions per the report-
      format spec; v2 renderer deferred to Week 4
- [ ] `signals.py` skeleton (no strategies registered yet)
- [ ] `execute.py` skeleton with position-limit enforcement
- [ ] `replay.py` with look-ahead-bias guard
- [ ] `render_index.py` — produces INDEX.md at repo root
- [ ] Claude API client + adversarial-review prompt template
- [ ] First weekly adversarial review session (Friday)
- [ ] Future-self-letter convention added to top of decision-log.md
      with worked example
- [ ] Deliverable: `replay.py --variant=null --period=30d` runs
      end-to-end and produces a v1-pattern empty-state report;
      `render_index.py` produces INDEX.md; week-1-status.md
      committed

### Week 2 — Two strategies + roster review (new gate)

- [ ] Register `bollinger_default` and `macross_default` per spec
      (or whatever the strategy-roster review decides)
- [ ] 6-month replay on both
- [ ] ~14 days live paper
- [ ] Cron / GitHub Actions wiring for the 5-minute schedule
- [ ] First A/B comparator output (likely insignificant — fine)
- [ ] **Strategy-roster review:** keep textbook strategies or replace
      with Week-0-surfaced candidates
- [ ] Decision-log entry committing the answer (either way) before
      Week 3 begins
- [ ] **Styled HTML surface review:** decide whether to build a
      Vercel-style deployed view of the markdown reports based on
      Week 1's actual reading experience. Decision-log entry either
      way. Reference: HTML previews in /mnt/user-data/outputs/ from
      Week 0 conversations
- [ ] Future-self letters written for Phase 2 entry gates and exit
      conditions in decision-log.md (deferred from Week 1 because
      letters need operator in the room)
- [ ] If neither strategy-roster outcome is achievable, postmortem
      the reframe per the falsifiable hypothesis

### Week 3 — Variant explosion

- [ ] 6–10 parameter variants per base strategy registered
- [ ] All run in parallel under shared position ceiling (variants do
      not increase total exposure)
- [ ] First statistically-suggestive A/B results

### Week 4 — Walk-forward tuner online

- [ ] `tune.py` runs nightly at 02:00 UTC
- [ ] Top-3 candidates per base strategy written to `recommendations`
- [ ] `compare.py` produces weekly A/B reports in `reports/ab/`
- [ ] `render_v2_report` added to render.py for the temporal pattern
- [ ] **Per Week 4 pushback:** observe but don't promote yet — first
      promotion target slips to Week 5 to avoid acting on tuner
      warm-up data

### Week 5 — First external source: Fear & Greed Index

- [ ] Layer 2 (Context) goes live
- [ ] F&G API integrated, cached in `context_data`
- [ ] One F&G-conditioned variant per strategy
- [ ] First human-promoted variant from walk-forward (deferred from
      Week 4)
- [ ] Note: 1 week of A/B data verifies integration, not signal —
      verdict deferred to Week 8 review

### Week 6 — Second external source (conditional)

- [ ] If F&G helped: add BTC dominance via CoinGecko
- [ ] If F&G didn't help: *cut* F&G and try alternative (e.g.,
      Glassnode exchange flows)
- [ ] Decision-log entry on the cut/keep call

### Week 7 — LLM news sentiment

- [ ] News sentiment variant alongside existing variants (this is now
      an A/B test, not the LLM debut)
- [ ] Twice-daily structured sentiment score per watched token
- [ ] Cached 12 hours, logged with input/output/model/latency in
      llm_calls
- [ ] 1 week of A/B data on whether LLM features add signal

### Week 8 — Decision week

- [ ] No new building
- [ ] Generate comprehensive 8-week review
- [ ] Three Phase 2 gates checked against evidence: pass/fail
- [ ] Sortino and Calmar reported alongside Sharpe (per Session 3
      audit flag A3)
- [ ] Sensitivity analysis on stop/target methodology (per Session 3
      audit flag B2)
- [ ] `phase1-review.md` committed with decision: proceed to Phase 2,
      extend Phase 1, or archive

### Phase 2 (if entered)

- [ ] Add `ALPACA_LIVE_API_KEY` and `ALPACA_LIVE_SECRET_KEY` to
      GitHub Actions secrets
- [ ] Flip `ALPACA_BASE_URL` to live URL — single config change
- [ ] Fund $1,000 to live Alpaca account
- [ ] Freeze variants and external data sources at qualifying
      configuration
- [ ] Spin up parallel paper instance for continued experimentation
- [ ] Weekly real-vs-paper variance check

### Phase 2 exit (when any condition fires)

- [ ] Halt execution layer for live account; data + signal layers
      continue
- [ ] Close real-money positions at market
- [ ] `phase2-postmortem.md` written before any decision on next
      steps

### Operational rhythms (every week, all phases)

- [ ] Friday: adversarial Claude review — bear case only, no hedging
- [ ] Decision-log review with Claude pattern-surfacing across recent
      entries (monthly)
- [ ] Daily digest auto-committed to git
- [ ] Weekly A/B report auto-committed (from Week 4)
- [ ] Open positions monitored daily, drawdown play (playbook §1)
      ready to fire

---

## What's NOT happening (and won't, without a decision-log entry first)

- Online ML / training models on trade history
- LLM-as-oracle for trade decisions
- Equities in Phase 1
- More than one new external source per week
- New strategy families mid-Phase-1 (the Week 2 review is the only
  roster decision point)
- High-frequency trading
- Real money before all three Phase 2 gates pass
- Styled HTML rendering surface during Week 1 (decision deferred to
  Week 2)
- Inline analytical prose in routine reports (analysis lives in
  reviews/, not reports/)

---

## Candidates for inclusion (not yet adopted)

These were surfaced in conversation but not formally adopted into the
project. Each requires a decision-log entry to add. Listed here for
visibility, not as commitments.

- **Permanent null variant** — random buy/sell signals as the placebo
  arm of the A/B comparator
- **Shadow factorial logging** — every trade records what each
  context source's signal *would* have been, enabling post-hoc
  factorial analysis without paying full sample-size cost
- **Pre-registered weekly hypotheses** — written prediction before
  each week starts, compared to actual at Week 8 (cluster-4 4A is
  the lighter version of this; the heavier version is parked here)
- **Decision audio log** — 5-min weekly voice memo, transcribed at
  Week 8, used to catch real-time reasoning that contradicts the data
- **"One year ago" replay** — stress test against a regime-different
  window (e.g., March 2020, November 2022)
- **Rejection-reason instrumentation** — small report counting *why*
  signals were rejected, to surface whether strategies are
  constraint-bound or signal-bound
- **Weekly pre-mortem** (cluster-2 2B, demoted as scope-creep but
  parked) — write the most-likely-failure-mode prediction at start
  of each week
- **Counterfactual analysis on rejected trades** (cluster-2 2D) —
  Layer 5 analytics feature; what would P&L have been if rejections
  hadn't fired
- **Continuous literature surveillance** (cluster-2 2E) — weekly
  scan of what's been published; demoted on operability but parked

---

## Canonical file list

The project's canonical files, in the order they should be read by a
human (or by Claude Code) coming to the project fresh:

1. `PROJECT.md` — build spec
2. `philosophy.md` — what this experiment is, what success means,
   the two animating disciplines
3. `decision-log.md` — running record of decisions, newest on top
4. `playbook.md` — pre-compiled responses to specific situations
5. `week-0-synthesis.md` — Week 0 deliverable: criteria, ranked
   candidates, methodological audit
6. `report-format-spec.md` — markdown report formats, INDEX page,
   v1/v2 patterns
7. `setup.md` — pre-flight infrastructure setup
8. `roadmap.md` — this file (navigational, derived)

`INDEX.md` (generated, not authored) sits above all of these as the
runtime entry point once the project is operational.
