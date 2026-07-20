# Decision Log — algotrading-paper

A running record of decisions made about the project. One section per
decision, dated. Newest entries on top.

The point of this file: in week 6 of Phase 1, when I'm staring at a
specific question and second-guessing myself, this is where I look to
remember why we set the rules we set.

When making a new decision:
1. Add a new dated section at the top
2. Be specific about *what* and *why* — not just "decided X" but
   "decided X because Y, considered alternatives Z and W"
3. If the decision contradicts an earlier one, note it explicitly:
   *"Reverses 2026-04-26 entry on max position size; new ceiling is
   $300 because [reason]."*

When evaluating a specific situation:
1. Skim recent entries to make sure the action under consideration
   doesn't violate an earlier decision without realizing it
2. If tempted to make an exception, write a new entry explaining the
   exception *before* acting on it. If the reason can't be
   articulated cleanly, that's a signal not to make the exception.

---

## Future-self-letter convention

Cluster-4 methodology 4F from `week-0-synthesis.md`. Hard-rule entries
in this log — Phase 2 entry gates, Phase 2 exit conditions, the reframe
entry's adaptive clause, and any future entry that creates a hard rule —
get a `### Future-self letter` section appended.

The letter is written *at the moment the rule is committed*, addressed
to the operator at *the moment override would be tempting*. Its job is
not to argue against the override but to anticipate the *specific
cognitive distortion* future-self will be experiencing — so future-self
recognizes the pattern and pauses.

Inheritor of a long tradition (Marcus Aurelius's *Meditations* are
literally 2nd-century letters to future self at moments of weakness).
The point isn't moralism; it's that present-self has access to
information future-self loses access to, namely the un-narrativized
view of *why this rule was set*.

### How to write one

Three short paragraphs, no more:

1. **What you're feeling right now** (the rule was just committed,
   pre-commitment is fresh, the data hasn't yet arrived to challenge
   it). Sets the contrast with the future-state.
2. **What you'll be feeling at the override moment** (named
   specifically — "you'll be telling yourself X" — based on the
   documented failure mode the rule guards against).
3. **The single concrete thing to do before overriding** (re-read X,
   wait Y hours, write Z, talk to W). Not "don't override" — the
   discipline is in the *interrupt*, not the prohibition.

The letter goes inside a `### Future-self letter` heading at the end
of the entry it belongs to, so it travels with the rule.

### Worked example — the Phase 2 drawdown exit ($700 floor)

This example is appended to the *forthcoming* worked-out version of
the 2026-04-26 entry "Three explicit Phase 2 exit conditions"; the
existing version of that entry below does not yet have the letter
because writing letters for *all* existing entries needs an operator-
in-the-room session and that session is deferred to Week 2 per the
roadmap.

> **Future-self letter — Phase 2 drawdown exit ($700 floor)**
>
> *Right now, 2026-04-26.* The rule is fresh. Real money hasn't been
> committed yet. The number $700 is just arithmetic — 30% drawdown on
> $1,000. It feels like a generous floor: I'd have to lose $300 of
> $1,000 before this fires. The pre-commitment is easy because the
> loss is hypothetical.
>
> *At the override moment.* You'll be staring at an account that has
> just touched $710. You'll be telling yourself one of three things:
> "the position is about to recover," "this is a flash crash and the
> exit will catch the wick," or "this is the worst possible time to
> sell because the strategies are about to start working." All three
> are documented retail-trader rationalizations for not closing a
> losing position. The 4G adversarial review will already have
> flagged the drawdown the previous Friday; you'll be tempted to
> argue the bear case was wrong because the account hasn't fully
> hit $700 yet.
>
> *Before overriding, do this one thing.* Open `playbook.md` §6,
> read the Phase 2 exit play in full, and write a `decision-log.md`
> entry titled "Override of Phase 2 drawdown exit — [date]" with
> the exact reasoning *before* placing any trade or canceling any
> order. If you cannot write the entry without it reading like
> rationalization, the letter has done its job: stop, run the play,
> file the postmortem.

The convention holds for entries written from this point forward.
The retroactive letter-writing for the existing 2026-04-26 entries
(Phase 2 entry gates, exit conditions, reframe adaptive clause) is
deferred to Week 2 per `roadmap.md`.

---

## 2026-07-20 — K1 adjudication: short-horizon crypto archived, residual on a dated clock

The kill-criterion question, ruled explicitly rather than left to
excitement about the equity result (operator-approved, this date):

- The original two-prong criterion was superseded by v2 (ratified
  2026-07-19); it cannot literally "fire." But its intent — no
  sunk-cost limbo — is honored here with a written verdict.
- **Short-horizon crypto continuation (≤24h, taker) is ARCHIVED**, on
  the ceiling-study evidence (gross edge below the cost floor at every
  horizon ≤12h). This is the death certificate for the sub-program
  that consumed rounds 1–4; the foundry already excludes the band.
- **The residual — 24h+maker fills and reversion-shaped 2–8 week
  specs — remains ALIVE under v2**, resolving by 2026-08-31, gated on
  the real-money RTC measurement. **If the RTC cannot run by
  2026-08-15, the residual resolves on the assumed 0.6% cost figure,
  treated as adverse** (burden on the strategy to clear the pessimistic
  number) — so the deadline is not hostage to Alpaca's approval queue.
- **The crypto clock runs independently of any equity scope decision.**

## 2026-07-20 — The equity sky check, sober reading (corrects the "living sky" summary)

The overnight E1 result, stated at the strictness of our own yardstick:

- Crypto momentum in 2024–26 is negative/reverting (0/9 cells,
  −12.4% directional). Equity momentum matches its 30-year PUBLISHED
  profile — weak in any single window, visible in aggregate,
  cross-sectional in nature.
- Equity TS momentum ALSO lost to drift in-window (0/9 long-or-flat
  vs-drift cells in 2024–26); it is not "alive" in the time-series
  sense.
- The only persistently positive signal is the CROSS-SECTIONAL 6-1
  spread: +sign in all four measurable windows (+1.33/+6.96/+1.21/
  +2.17 %/mo). Single-window significance is weak (2024–26:
  +2.17±2.10, t≈1); pooled across the four windows ≈ t≈1.9. The
  pooled figure is the actual motivation for a round-zero replication;
  survivorship inflates both numbers (upper bounds).
- **The real case for E2 is BREADTH and falsification-throughput**
  (thousands of names vs. ~2 effective crypto series; ~0.05% vs 0.6%
  costs; decades of regimes vs. one) — it holds even if the sky check
  had come back flat. Not the sky-check magnitude.

Round-zero pre-registration (captured now, promoted into the E2 entry
when written): the positive control is cross-sectional 12-1 momentum,
long-only US large-cap tilt; DETECTION = landing inside or above the
literature band (~2–4%/yr over benchmark, post-2000, decaying) with
the sign right, at the significance 20+ years of monthly data affords
per the power table. A noisy positive is NOT detection.

**B2 corrected-archive registration (2026-07-20, before the re-score
runs):** survivorship is fixable at zero data cost — Alpaca serves full
daily bars for delisted names (SIVB→2023-03-09, FRC, SBNY, BBBYQ, MULN
all returned) — but the fix carries caveats that go on record now:
- *Liquidity, not membership*: no listing/delisting-date fields exist,
  so the point-in-time universe is built by trailing dollar volume from
  bars ≤ each formation date (a liquidity screen). No fundamentals /
  market cap; pre-window delistings invisible; symbol recycling a
  minor risk.
- *Delisting-exit convention* (Shumway 1997 bias): a name that stops
  printing mid-hold is exited at last close −30% (conservative
  involuntary assumption). Alpaca status can't distinguish
  involuntary from voluntary/merger, so −30% is applied uniformly
  until a delisting-type source is added; refine then. Second-order
  for a long-only tilt, but it corrects the drift benchmark and any
  literature comparison.
- *Screen ↔ band consistency*: momentum is stronger in small illiquid
  names, so a dollar-volume screen ≈ large-cap proxy and should show
  the WEAKER end of the pre-registered 2–4%/yr large-cap band. Screen
  and band are consistent by construction; a middling result is NOT
  failure against a small-cap-inflated expectation.
- *Adjustment confirmed*: the E0 fetch uses Alpaca adjustment="all"
  (split + dividend) → bars are total-return-adjusted; momentum ranks
  are valid.
- *Pre-commitment (decided before the corrected numbers exist)*: if
  the corrected re-score flips the cross-sectional sign or collapses
  pooled t toward zero, the E2 rationale formally reverts to
  breadth-and-throughput-only (already agreed to survive that), and
  round zero proceeds ANYWAY — its job is validating the pipeline
  against a known-true effect, not confirming the sky check. No result
  the corrected archive can return requires an improvised decision.

## 2026-07-19 — Operator ratification: all pending drafts approved

The operator approved all items awaiting signature ("approve all",
2026-07-19):

1. **Program-level kill criterion v2** (the adversarially-reviewed
   rewrite below) is RATIFIED as written: first scheduled ceiling
   study by 2026-08-31 under a locked analysis plan; turnover-
   normalized net edge; one-sided 90% upper-CB futility trigger
   validated against the power table; 60-day execution-scoped
   remediation; restart only with a materially new data source or
   ≥50% RTC reduction.
2. **Execution-cost pre-registration E-1.0** is RATIFIED as the
   locked protocol. Physical prerequisites remain: Alpaca live
   account approved + funded, keys delivered via the clipboard
   channel. No order fires before both.
3. **Lessons re-labeled as hypotheses** (referee resubmission
   condition): the registry's failure_lessons are hereby understood
   as hypotheses-with-evidence, binding on synthesis in proportion to
   their support; the n-tagging work (queued) will make each lesson's
   evidentiary weight explicit. Lessons resting on measured control
   arms or distribution checks (Grade A) remain hard constraints.

---

## 2026-07-19 — Execution-cost experiment: pre-registration draft E-1.0

Revised per the runbook Run-2 referee (which restructured the naive
24-cell factorial). Awaiting Alpaca live-account approval + operator
sign-off; no order until both.

**Estimand:** expected cost of the BEST controllable execution policy
on BTC/ETH at $25-$100 notional — the number the kill criterion (v2)
consumes as RTC. Cost is defined PER LEG as implementation shortfall:
(fill − decision-mid)/mid signed against the trader, plus fees;
never round-trip P&L (inter-leg drift contaminates at this size).

**Design:**
- Symbols BTC, ETH only (SOL cut — the criterion doesn't ask about it).
- Factors: policy (market vs post-only-limit) × size ($25 vs $100) ×
  session (US day vs overnight). Volatility is a recorded COVARIATE
  (quoted spread at decision + realized 1h vol), not a scheduled factor.
- PAIRED contrasts: each epoch submits one market and one post-only
  order against the same quote; the policy contrast is a within-pair
  difference.
- The limit arm is a full pre-specified POLICY: post at mid − 1 tick,
  cancel after 120 s, fall back to crossing the spread; its cost
  includes rejections, non-fills, and fallback executions.
- Two-stage allocation: stage 1 ≈ 20 paired epochs across cells →
  eliminate dominated arms; stage 2 ≈ 30 epochs concentrated in the
  best 2-3 policies. REPORTED number = stage-2 mean of the stage-1
  winner (unbiased; no winner's curse). Market orders serve mainly as
  the ~10-observation calibration anchor (near-deterministic cost).
- Power gate at stage-1 end: if projected SE of the best policy's
  cost exceeds ~10 bp near the 0.5% threshold, extend n before
  concluding anything.

**Recorded per leg:** top-of-book (bid/ask/sizes) at decision and at
fill; markouts at +1 s/+10 s/+60 s/+5 min; fee paid + schedule tier +
any promotion in effect; full timestamp chain (decision, submit, ack,
fill) on one clock; rejections, time-to-fill, cancels.

**Guards (hard bounds):** max $100/order, max $200 concurrent
exposure, ≤120 total legs, total fees ≤ $25, serial execution, manual
invocation only, live keys readable only by
scripts/measure_execution.py. First-fill check: if any flat fee
minimum appears, abort and re-size. Fee context: Alpaca crypto tier 1
is 0.15% maker / 0.25% taker, percentage-based.

---

## 2026-07-18 — Outside eyes institutionalized: fresh context is a standing resource

**Decision:** the blind-elicitation exercise produced more validated
learning in one day than any week of inside work (ceiling study,
power calibration, netting insight, slow-band prior, cost
decomposition all trace to it). Fresh, unanchored context is now
MACHINERY, not a thing the operator remembers to do. Four standing
stages, all fresh `claude -p` contexts on the VPS:

1. **Blind pre-mortem** (per round, before implementation): a critic
   with no project history reads only the round spec + registry and
   verdicts each idea IMPLEMENT/REDESIGN/SKIP. Its verdicts are
   FORECASTS — the epitaphs score them (premortem_correct in the
   gradient), so the critic's calibration is itself measured.
2. **Blind second reading** (per round, after epitaphs): a tool-less
   context receives only specs + numbers inline — it cannot see the
   epitaphs — and writes independent diagnoses. Disagreement with the
   registry marks a fragile lesson (double-blind radiology reading).
3. **Monthly rival-lab audit** (1st, 12:02 UTC): the domain-disguised
   "reverse-engineer the 10x rival" question re-asked against current
   state, numbers regenerated from the registry each time.
4. **Monthly literature refresh** (same cron, web-enabled): only what
   is NEW or CONTRADICTS docs/literature-priors.md, cited.

**Why it works (the mechanism, so we don't cargo-cult it):** the
pipeline's own context accumulates doctrine, and doctrine anchors;
a fresh context re-derives from evidence alone. Blindness must be
real — the second reader gets no tools; the disguise hides the
domain; the premortem sees only two files.

---

## 2026-07-18 — Critique-driven reorder: extraction engineering, conditional program

The closing-move critique session reframed the program: with the
ceiling measured at ≈ the cost floor (24h) and rising in horizon, the
genre shifted from PROSPECTING (find any edge) to EXTRACTION
ENGINEERING (the decision is on the cost side). Accepted changes:

1. **Order**: extend the horizon scan past 24h (running) → backfill
   context data and RE-MEASURE the ceiling on the augmented feature
   set (funding history backfilled: 2,790 settlements/symbol) →
   factorial cost-surface measurement (order type × size × time; the
   50-trade experiment is redesigned factorial, not uniform) → only
   THEN decide whether the combination stage, scoped snooping ledger,
   and continued shadow validation exist at all.
2. **Combination mechanism corrected**: the prize is NETTING (signals
   that disagree → no trade; offsets → cost never paid), not
   √breadth diversification — the netting ratio is computable offline
   from persisted trade records BEFORE any machinery is built.
3. **Deprioritized**: failure-mode taxonomy (post-hoc while all deaths
   share one cause), full snooping ledger (scope to wherever adaptive
   search actually resumes), sub-24h shadow arms (structurally under
   the ceiling; the shadow tape keeps rolling only because it is
   nearly free).
4. **Cost floor is per-symbol and partly a CHOICE**: first venue
   measurements show Alpaca spreads of 0.07% (BTC) to 0.42% (SOL) vs
   Binance ≤0.015% — fees + spread are selectable (symbol, order
   type, venue tier); only slippage requires real trades to measure.
5. **Program-level kill criterion — v1 draft SUPERSEDED** (2026-07-19
   adversarial review found: cost treated as a constant when it is a
   decision variable; circularity — the rule never consulted our own
   power study; an AND-conjunction giving the operator a survival
   dial; a units error comparing per-round-trip cost to per-horizon
   edge without turnover; no clock, no restart rule). **v2 DRAFT for
   ratification:**

   By 2026-08-31, and every 6 months thereafter, run the ceiling
   study per a LOCKED analysis plan (feature-set version by commit
   hash; fixed model suite and hyperparameter budget; horizon grid
   H = {24h, 3d, 1w, 2w}; walk-forward protocol as in
   scripts/ceiling_study.py). For each h in H compute
   **net_edge(h) = gross_edge(h) − turnover(h) × RTC**, where RTC is
   round-trip cost measured under the locked execution protocol from
   the real-money experiment (venue, order type, size, ≥30 fills,
   effective spread + fees).

   FUTILITY TRIGGER: the one-sided 90% upper confidence bound of
   net_edge is below zero at EVERY h in H, with the CI method
   validated against the 2026-07-18 power-calibration table.

   ON TRIGGER: one 60-day remediation window opens, scoped to
   execution cost only (fee tier, maker conversion, venue). If
   breakeven RTC for the best horizon is still unachievable, program
   v1 archives per the Phase-1b terms. RESTART requires a materially
   new data source or a documented ≥50% RTC reduction — a new
   program, not a re-litigation of this one.

   Chosen asymmetry, made consciously: this version is more gameable
   toward death than toward zombie-life — for a solo operator,
   sunk-cost persistence is the bigger risk than premature
   abandonment.

---

## 2026-07-18 — Four rulings from the learning-maximization review (operator-approved)

The operator approved all four decisions surfaced by the blind
elicitation exercise (claude.ai session + two blind Fable agents,
transcripts summarized in the 2026-07-18 entries):

1. **Real-money micro-execution measurement — APPROVED as
   instrumentation.** ~50 tiny live trades on Alpaca to measure the
   TRUE round-trip cost distribution (the assumed 0.6% is unsourced
   beyond the fee schedule). Bounds to be pre-registered in a
   dedicated entry before the first order: max $50/order, ~50 round
   trips, max $100 concurrent exposure, manual invocation only, live
   keys readable ONLY by scripts/measure_execution.py. This does NOT
   open live trading; promotion to live remains a separate human
   decision.
2. **Predictability-ceiling study — APPROVED; the no-ML lock gains an
   instrument exemption.** Generic walk-forward ML over OHLCV features
   may be used to MEASURE the maximum edge available to the rule
   class. Nothing ML may be deployed, registered as a variant, or fed
   to live execution — the lock stands for strategies; the exemption
   is for measurement (same logic as planted-edge calibration).
3. **Promotion gate rebuild — APPROVED (amends locked Phase-2 gates).**
   The fixed-n gate (p<0.05 at 100+ closes) has measured power of
   ~20-25% and is replaced by a group-sequential design: efficacy AND
   futility boundaries with alpha-spending (or SPRT), live slots
   treated as scarce confirmation capacity with a queue. Old gate
   stays until the new machinery ships and its boundary table is
   reviewed in this log.
4. **Combination stage — APPROVED as portfolio construction, not ML.**
   Linear combinations of registered sub-threshold signals with
   snooping accounting are admissible research objects; anything
   fitted beyond simple weights falls back under the no-ML lock.

---

## 2026-07-18 — Power calibration: the instrument measured itself

**What happened:** first-ever measurement of the gauntlet's detection
power (scripts/power_calibration.py; reports/power-calibration-
2026-07-18.json). Bootstrap of the null arm's real 930d constrained
net returns (n=7,068, mean −0.633%/trade = the measured cost drag,
std 3.05%) with planted edges of known size.

**Findings:**
1. False-positive rate of the +0.3% kill bar at n=7 is 21% — a
   small-sample "pass" like r003's slot_scarcity is roughly what pure
   noise produces one round in five, before best-of-5 selection.
   The n<30 quarantine rule is quantitatively vindicated.
2. Power is near zero exactly where interesting edges live: a true
   +0.17%-net edge passes 32% at n=100 and LESS with more data (the
   bar exceeds its true mean). Reliable detection starts ~+0.6% net
   (+1.2% over null). Verdicts with observed expectancy ≤ −0.5% at
   n≥100 remain solid; near-flat small-n verdicts (e.g. gap at
   −0.16%, n=14) are hereby reclassified as UNINFORMATIVE, not deaths.
3. Sub-bar real edges are unrecoverable one-at-a-time by
   construction — the strongest argument yet for the queued
   combination stage (fee floor binds per deployed rule, not per
   signal).

**Decisions:** (a) gauntlet verdicts must henceforth be read against
this table; the report gains a power footnote when regenerated;
(b) re-run the calibration whenever costs, constraints, or the kill
bar change; (c) the meta-conclusion "5-min OHLCV has no edge" is
DOWNGRADED to "no edge ≥ ~0.6% net detectable by this instrument" —
smaller edges remain an open question that only the combination
stage or the live channel can answer.

---

## 2026-07-17 — Seam closed for real; first fully autonomous cycle ran

**What happened:** Both halves of the closed seam went live today and a
complete research cycle ran with no human in the loop by end of day.

- Cloud routine `foundry-implementer` (trig_01CB7gU6mXGFXSRj4kvDd74N,
  08:00+20:00 UTC): implements round specs, writes epitaphs. Its prompt
  now mandates the premise check (see CONJUNCTIONS MULTIPLY TO ZERO).
- Digest email: VPS-side scripts/send_digest.py in cron-skeptic.sh.
  Two discoveries forced this design: (1) the claude.ai Gmail connector
  is DRAFT-ONLY — it cannot send, so the cloud digest-mailer routine
  (trig_01NjtGaNPuFbLWzikmt5iuQw) is disabled, kept for reference;
  (2) Hetzner blocks outbound port 465 but leaves 587 open — SMTP via
  587/STARTTLS. GMAIL_APP_PASSWORD lives in the VPS .env (delivered
  clipboard→ssh, never through a transcript). Delivery confirmed.
- Round-002 was processed end-to-end (implemented locally standing in
  for the then-blocked cloud agent, gauntleted under BOTH fill models,
  epitaphed), and round-003 was generated, implemented, and queued for
  gauntlet — the first cycle where every stage ran unattended.

**Bug found and hardened against:** growing LENSES 5→8 silently grew
the synthesis output demand past max_tokens; the truncated tool input
validated as {} and died with a misleading "field missing" error.
Fixes: lenses_for_round() rotates 5-of-8 per round (two consecutive
rounds cover all lenses); max_tokens 16384; complete_structured raises
loudly on stop_reason=max_tokens; run_round validates idea count,
name uniqueness, and collisions against config + registry before
writing; pipeline_health() puts a FOUNDRY STALLED/ALERT warning at the
top of the emailed digest when the newest round is >3 days old or the
foundry log recorded an ALERT. The residual risk accepted: failures
are now detected within ~24h, not prevented; total silence (no digest
email at all) is itself the last-resort alarm.

**Watchlist decision:** rejection_streak_gated_ignition (r002) died
over 930d but was the only stage-1 survivor and is POSITIVE on the
trailing 180d under both fill models (n=35 — no claim). The gate
family is best-of-round for the second consecutive round. It gets an
out-of-sample re-test on the NEXT 180d window before any gate-family
idea is judged again; that result decides whether the gate fits the
current regime or best-of-round is what recency overfit looks like.

---

## 2026-07-17 — First net-positive cell; cost lever validated; holdout NOT burned

**What happened:** The 24-cell exit-grid sweep of
drawdown_regime_contrarian_gate (tp/sl/horizon × taker/maker, selection
window 2024-01-01 → 2026-01-01 only) produced the project's first
net-positive configuration: maker · 72h · tp8%/sl4% = **+$0.031/slot**
($4.47 over 146 trades in 2 years). Full grid in
reports/exit-grid-drawdown_regime_contrarian_gate-2026-07-17.json.

**Two findings, held apart deliberately:**

1. **The cost lever WORKS — mechanically.** Maker fills beat taker in
   12/12 matched pairs, mean +$0.14/slot, ~$0.21–0.24 fees saved per
   trade, and fill loss was 0–4 trades per ~150. The near-zero fill
   loss is itself mechanistic: this strategy buys drawdowns, so price
   is falling INTO the resting limit. Cost engineering is now a
   validated, reusable lever — every future gauntlet should test both
   fill models.
2. **The strategy's edge is statistically ZERO.** +$0.03/trade on 146
   trades is far inside noise (per-trade std is dollars, not cents),
   and it's the best of 24 cells — multiple-comparisons bias means the
   true expectation of this cell is likely negative.

**Decision:** Do NOT run this config against the 2026 holdout. The
holdout answers one question per candidate, ever; spending it on an
edge indistinguishable from zero wastes the only unbiased test we
have. The holdout is reserved for a candidate whose selection-window
edge is large enough that generalization is a real question.

**Consequences:** (a) fill_model='maker' becomes a standard gauntlet
axis; (b) the gross-edge problem remains the frontier — costs are now
~solved in sim, so the search needs mechanisms with more raw signal,
which is what the Layer-2 context lever and the foundry's
gate_engine_pairing lens are for; (c) live maker execution (limit
orders in execute.py) stays queued until a strategy earns it.

---

## 2026-07-17 — The levers are the strategy; retest the dead under new exits

**Decision:** The structural levers — multi-day horizons, cost
engineering (maker fills), context data, gate-engine pairing — are the
project's primary research direction, not merely extra lenses feeding
the foundry. Two operational consequences:

1. **Verdict invalidation.** Every idea in dead-ideas.json was judged
   under ~24h horizons and taker-fee costs. A lever that changes the
   cost/horizon arithmetic partially invalidates those verdicts. When
   a lever lands, the near-misses (gross-positive, fee-killed ideas)
   get re-gauntleted under it BEFORE new ideas get priority. First
   instance: the 2026-07-17 horizon re-test (reports/horizon-retest-*)
   re-trying weekend, omori, vol_thrust, regime_gate, and dead_zone
   with 3–5 day exits.
2. **Priority ordering.** Lever work (per-variant exits ✅, maker-fill
   modeling, Layer-2 context) outranks generating round N+1. The
   foundry keeps running, but a new round is the *default* action, not
   the *preferred* one.

**Reasoning (user, verbatim intent):** "these ideas are key to the
success of this project — not just 5 new tests." Ten ideas died in the
same corner of design space (short-horizon taker-fee mean-reversion).
Searching a structurally different space beats sampling the old one
harder. Epitaphs are conditional on the cost model that produced them
— the registry must not fossilize verdicts the levers have overturned.

---

## 2026-07-17 — Correction: the sequence was valuable; the duration was not

The operator challenged the standing narrative that the pre-July phase
"was the design working." Partially false, and the record should say so
plainly rather than let the flattering version stand.

**True:** the canon-first SEQUENCE earned its keep — the fee floor,
constraint dominance, and fade-death lessons all required killing the
canon on the record first, and foundry round 2 is measurably better
because those gradients existed.

**False:** that the ~80 days of elapsed time contributed to it. Nearly
everything the project has ever learned was produced in the ~48 hours
of 2026-07-16/17. The elapsed weeks bought gate-1 uptime evidence
(earnable concurrently), live bars (superseded by a 10-minute
backfill), and perhaps two weeks' worth of operational lessons. The
one truly incompressible resource — live trade-days for the A/B — was
NOT accumulating: the live clock started 2026-07-16. Eleven weeks of
calendar bought one day of the only slow currency.

**The meta-lesson:** entries written at resumption ("the strategies
were always the control variable", "the sequence was the design")
converted stall into substrate — an instance of the flattering-
direction drift the adaptive-clause future-self letter warns about,
caught this time by the operator, not the machinery. The Friday
review's drift check should treat resumption-era reframings as
suspect by default. The closed seam exists precisely so that elapsed
time and learning time can never again diverge by 40x.

---

## 2026-07-17 — Close the seam: the foundry runs autonomously; the operator reads asynchronously

Operator directive, verbatim intent: "I want to read, but I can always
catch up — I want to optimize this." Learning speed must never wait on
a human opening a session. The one remaining manual step (implement →
gauntlet → epitaphs) becomes autonomous.

**Cadence: information-gated, not calendar-gated.** Cycles run
back-to-back as fast as the pipeline allows (~1 round per 1–2 days),
because the constraint on honest learning is new-information arrival
(fresh market days; live A/B verdicts), not wall-clock. Iterating
faster than information arrives mines noise — so speed is paired with
the guards below, and the guards, not a schedule, set the pace.

**Architecture (no new secrets anywhere):**
1. *Scheduled cloud agent, daily*: clones the repo; if the newest
   foundry round has specs but no implementations, implements them
   with tests and pushes; if gauntlet results exist without epitaphs,
   writes gradient-rich epitaphs to the registry and pushes. Pure
   code work — needs no API keys.
2. *VPS cron conditions* (the box holds the keys): if epitaphs are
   complete and no next round exists → run idea_foundry.py; if a
   round has implementations but no gauntlet results → build/refresh
   research_bars.db locally and run the staged parallel gauntlet;
   push results. Both idempotent, both logged.

**Guards (the price of speed):**
- The 2026 holdout window is never used for selection.
- The registry gains a total_ideas_tested counter; the gauntlet's
  survival bar escalates with it (more ideas tested → stronger
  evidence demanded), the multiple-comparisons correction.
- Backtests never touch the live roster. The only door remains the
  live A/B against null_baseline at p<0.05 over 100+ closed trades —
  and that runs at the speed of reality no matter how fast the lab
  spins.
- The Friday investigator's drift check watches for foundry theater.

**The operator's role narrows to what it should be:** reading the
digest and dashboards on their own time, and the two decisions the
machine refuses to make — promotions, and the Phase 1b gate.

---

## 2026-07-16 — The foundry: the aggressive-iteration phase begins

The operator named the design intent tonight, and the record supports
it: the sequence was always **canon first → documented failure →
aggressive multi-perspective iteration toward ways of working that
didn't exist in this context before.** The textbook strategies were
the control variable; the gauntlet's five canon-descended candidates
were the second control. Both have now failed on the record with
named mechanisms (fee floor, constraint dominance, gross-positive/
fee-negative). The substrate the aggression phase needed — the
failure evidence — exists. This entry starts the phase.

**The mechanism: the idea foundry** (scripts/idea_foundry.py).
Recurring synthesis rounds, each producing 5 ideas from 5 mandatory
DIFFERENT lenses (information theory, cross-domain imports,
microstructure-from-OHLCV, behavioral/calendar, meta-self-referential
— the system observing itself), each idea forbidden from descending
from any lineage in the dead-ideas registry
(reviews/foundry/dead-ideas.json), each required to engage the
failure lessons and to state its own kill criterion. Rounds are
falsified by the automated gauntlet; deaths get epitaphs in the
registry; the registry constrains the next round. Iteration
compounds instead of repeating.

**Resolving the tension with the adaptation ladder:** the ladder's
one-rung-at-a-time discipline governs the LIVE roster, which stays
at 3 arms (placebo + 2). The foundry is backtest-only exploration —
rung-1 territory, where the capital discipline explicitly licenses
recklessness ("spend the cheap part recklessly": a foundry round
costs ~$0.50 of synthesis and some compute). Wild in the lab,
boring in production. An idea only touches the live roster by
out-scoring a live arm in the gauntlet AND surviving the same
registration discipline as everything else.

**Failure mode this entry pre-names:** foundry theater — rounds that
generate exotic-sounding ideas that are dead lineages wearing
costumes. The lineage_check field and the Friday review's drift
check are the guards: if two consecutive rounds produce only
registry-shaped deaths with no novel mechanism, the foundry prompt
is the problem, and that gets its own entry.

---

## 2026-07-16 — Gauntlet results: every candidate negative net of fees; top 2 registered as A/B arms, not winners

The five LLM-surfaced candidates (reviews/candidates-2026-07-16.md) ran
the 180-day constrained replay (reports/gauntlet-2026-07-16.md). **All
five lost money net of fees.** Ranked by edge per constraint slot:
weekend_illiquidity_momentum −$0.21/trade (n=79),
volume_thrust_regime_shift −$0.63 (n=38), dead_zone_range_break −$0.88
(n=13), btc_leads_alt_lag_capture −$1.76 (n=3),
liquidation_cascade_reclaim −$2.56 (n=4).

**The honest read:**
1. **No candidate earned promotion.** By the project's own bar,
   negative is negative. The bottom three additionally have samples
   (n=3–13) too small to claim anything at all.
2. **The fee-floor finding replicated on novel strategies.**
   weekend_illiquidity_momentum is *gross-positive* (win rate 49.4%,
   gross Sharpe 1.51) and fee-negative — exactly the failure shape the
   Phase 1 backtest predicted. The edge candidates found is real but
   smaller than the ~0.6% round-trip cost. (Caught in review: replay's
   pnl_pct — which Sharpe uses — is gross of fees; pnl_usd is net.
   The gross/net split is diagnostic here, but Sharpe-on-gross should
   not be read as risk-adjusted net performance.)
3. **Registering the top 2 anyway — as experiment arms.** The Phase 1b
   term commits to a live roster because the live A/B against
   null_baseline is the architecture test (gate 2's machinery), and
   paper trades cost nothing. weekend_illiquidity_momentum and
   volume_thrust_regime_shift are now enabled=True beside the placebo.
   Registration is explicitly NOT promotion: the promotion bar is
   unchanged (beat null at p<0.05 over 100+ closed trades, compare.py).
   The expected outcome is that all three arms lose slowly and the
   candidates must prove they lose *less than random* — and if a
   candidate ever beats fees outright, the backtest says be suspicious
   first (see the null-variant entry's tripwire).
4. **Aggression-without-rigor check passed.** The temptation was to
   read weekend's gross Sharpe 1.51 as success. It is noise-plus-fees
   until the live A/B says otherwise. Writing that down now, before
   the live data arrives.

Live roster after this entry: null_baseline + weekend_illiquidity_
momentum + volume_thrust_regime_shift. Three arms, not a zoo.

---

## 2026-07-16 — Post-incident record: .env exposure in a Claude Code session (May 2026)

Closing the item flagged since May in pending.md and
decision_log_queue.md ("caught, rotated, unlogged") and named in both
the W21 review (attack vector 8) and the first nightly skeptic run as
the longest-dismissed open item. Written ~2 months after the fact from
operator recollection — the delay is itself the main lesson.

**What happened.** During a Claude Code session in May 2026, the
contents of the local env file (.env/.env.local) were displayed in
the session transcript — the file was echoed to the screen, exposing
credentials to the conversation context. Best recollection: only the
ANTHROPIC_API_KEY was exposed; the Alpaca keys were not part of what
was shown.

**Response.** The operator caught it at the time and rotated the
Anthropic API key. The Alpaca paper keys were judged unexposed and
kept ("the keys online are good"). No evidence of misuse appeared.

**What the evidence supports.** A full git-history search (2026-07-16)
confirms no real credential was ever committed to the repo — every
version of .env.template contains only placeholders, and .env was
never tracked. The exposure surface was the session transcript, not
the repository.

**Lessons, committed:**
1. **Log incidents the day they happen.** This record is ~60 days
   late and is written from memory. The details that would matter in
   a real postmortem (exact date, what command echoed the file,
   whether the transcript persisted anywhere) are gone. The write-up
   cost ten minutes; the deferral cost the facts.
2. **Secrets should never be echoed to a session.** Tools and
   assistants working in this repo must read credentials only via
   code paths that need them (load_dotenv), never cat/print an env
   file. Structural guard now in place: this session's checks read
   key *names* only (`grep -o '^[A-Z_]*=' .env`), never values.
3. **Rotation was the right call and is cheap.** Paper-trading keys
   have no capital at risk, but the audited llm_calls spend rides on
   the Anthropic key — rotate first, investigate second.

---

## 2026-07-16 — Null variant live: the placebo arm is the first (and only) live strategy

Adopting the "permanent null variant" from roadmap.md's parked
candidates, per phase1-review.md § 5 term 1 (archive trigger
2026-07-24). `null_baseline` emits deterministic pseudo-random
buy/sell signals — hash of (symbol, bar_timestamp), p=0.10 per
symbol per bar — through the full live path: signals.py →
execute.py's position limits → Layer 4 exits, on the VPS cron every
5 minutes.

**What it is for.** Three jobs, none of which is making money:
1. **Close the first live loop.** Ten weeks produced zero
   signals/decisions/trades; both machine reviews named this the
   terminal gap ("2016 successful runs, 0 decisions"). The loop has
   to be proven with a strategy whose behavior is fully understood
   before any candidate strategy's results can be attributed to the
   candidate rather than to loop bugs.
2. **The placebo arm.** Every LLM-surfaced candidate must beat null
   under identical constraints (compare.py, p<0.05, 100+ trades) or
   its edge is noise. Never retired — every adaptation-ladder rung
   is measured against it.
3. **Exercise the constraint layer live.** The 6-month backtest
   showed constraints dominate strategy (99.6% rejection); null's
   rejections populate the decisions table with real
   rejection-reason data.

**Determinism matters:** random() would double-signal on re-runs and
make backtests unreproducible. The hash-based roll plus the signals
table's UNIQUE constraint makes every cycle idempotent.

**Layer 4 exits built alongside** (execute.manage_exits): stop/target
from each open trade's latest bar (conservative — stop wins ties,
matching replay), 24h time exit. Without exits the 5-position cap
deadlocks the loop after 5 trades — the placebo would have proven
the loop broken instead of working.

**Expected P&L: slowly negative** (fees on random entries). That is
the design. If null_baseline shows a *positive* edge over a real
sample, something is wrong with the simulator, the fee model, or the
market data — investigate before believing any candidate's results.

---

## 2026-07-02 — Retire Bollinger and MA-crossover (Week 2 roster call, resolved on 6-month evidence)

The falsifiable hypothesis committed at the reframe said: if neither
base strategy clears the bar over a real window, replace them. The
6-month replay cleared its throat. Retiring both.

**The evidence.** 12 variants, 6-month window (2026-01-03 →
2026-07-02), realistic constraints and fees. 1,371 trades placed /
390,519 candidates (99.6% rejected by cooldown/exposure/concurrency).
Net −$1,719.44 (−0.13%).

Every variant with a real sample (n>100) is negative. The worst
performer is `bollinger_default` itself — n=539, −$636.75. The more
it trades, the more it loses. The only two in the black,
`macross_slow` and `macross_default`, run on n=3 and n=13: noise, not
signal. `bollinger_loose` (σ=2.5) fired zero times across all six
months — too wide, period, not too wide for one regime.

**The call.** Both base strategies are retired from the active
roster. This is not a failure of the project — it is the project
working. The strategies were always the control variable,
deliberately banal (the Duchamp *Fountain* logic). The experiment
was never "does Bollinger make money"; it was "does the epistemic
infrastructure produce a clean, defensible negative when the signal
isn't there." It did.

**What replaces them:** deferred to the next phase — LLM-surfaced
candidates, climbing the adaptation ladder (2026-07-02 entry below).
The aggression half of the learning discipline runs next.

**Considered and rejected:** keeping the strategies on the two
noise-positive variants. Rejected — n=3 and n=13 is exactly the
aggression-without-rigor failure mode `philosophy.md` names.
Believing a 3-trade positive over a 539-trade negative would be
declaring victory before the data finished speaking.

**Gate status: unchanged.** No A/B-validated promotion exists; P&L
is negative. Phase 2 gates not met. This entry does not authorize
real money.

---

## 2026-07-02 — Front-loaded all 12 variants on Day 1 (variant-explosion method record)

Registered all 12 variants at once rather than the roadmap's phased
Week-3 rollout. Recording why, because it worked and the reasoning
should be reusable.

**What:** all 12 variants registered and run in parallel on Day 1 of
the pass, not staggered across weeks.

**Why it was safe:** the shared position ceiling means variants
compete for the same $1,000 cap — they don't add exposure. 99.6% of
candidate signals were rejected by cooldown/exposure/concurrency;
total exposure never breached. No risk cost to parallelism, so no
reason to stagger.

**What it bought:** one clean comparative table across the whole
family in a single window, instead of three weeks of partial reads.
Compressed the calendar without compressing the rigor.

**The design finding:** the shared-ceiling architecture works as
specified. Adding variants moved total P&L only through
better/worse selection within the cap, not through added exposure —
exactly the intended behavior.

**Discipline note:** this is the capital discipline applied to
method — the cheap part (paper backtest variants) spent recklessly,
in parallel, because mistakes there cost nothing. The expensive part
(the roster decision it fed) spent carefully, on the full 6-month
window.

---

## 2026-07-02 — The adaptation ladder: rung 6 is the goal, reached one rung at a time

Committing the answer to "how radical should the system's
self-adjustment be" *before* the tuner goes online and the
temptation arrives. The reframe's aspiration is rung 6 — an LLM
surfacing genuinely novel strategy candidates. That remains the
destination. This entry is about the path, not the target.

Six rungs, banal to radical:

1. **Static** — fixed rules, no feedback. The control arm. Never
   retired; every higher rung is measured against it.
2. **Human-promoted tuning** — walk-forward proposes, I promote
   after an A/B win. (Week 4 machinery, already specced.)
3. **Regime-conditional switching** — rules fixed, but which rule
   fires depends on market state. The selector adapts, not the
   strategy.
4. **Online parameter adaptation** — parameters drift with recent
   conditions, no human in the loop. Crosses the no-ML line if fit
   from trade history; requires its own decision-log entry before
   it's built.
5. **Meta-strategy / ensemble weighting** — capital flows toward
   whatever's working lately. The portfolio adapts though no single
   strategy does.
6. **LLM-proposed novel strategies** — Claude surfaces candidates
   the canon missed; I falsify them. Maximum epistemological
   aggression. The goal.

**The rule that makes rung 6 survivable rather than reckless: climb
one rung at a time, and only after the rung below produces a clean
A/B result.** Radical is earned, not chosen.

Why this and not "build toward rung 6 directly": rung 6 is exactly
where novelty is easiest to mistake for edge — the
aggression-without-rigor failure mode named in philosophy.md. LLM
strategies with no disciplined rungs beneath them is a urinal from
someone who can't draw. Duchamp painted the *Nude Descending a
Staircase* before the readymade meant anything; the mastery is what
earned the radical gesture. The ladder is not a brake on ambition —
it's the structure that lets the ambition survive contact with a
near-zero real edge.

Current position: not yet at rung 2. The tuner isn't online. Do not
design rung 5 while rung 1's simulator still overcounts trades.

Considered and rejected: skipping to rung 6 on the strength of the
reframe's ambition. Rejected because it inverts the reframe —
"epistemological aggression *with* methodological rigor," not
instead of it.

---

## 2026-07-02 — The distillation discipline (third animating discipline)

Adding a third animating discipline alongside capital and learning.
The first governs risk-taking, the second idea-taking, the third
governs how the work gets communicated.

> Compression is the contribution, not the caveats.

The project is sophisticated. The failure mode that comes *with*
sophistication is talking like it — every consideration surfaced,
every claim hedged, a pile of nuance handed over and called help.
That's unpaid labor passed to the reader. The discipline is the
inverse: do the expensive thinking, hand over the cheap-to-carry
result. Kahneman is the model — forty years compressed into System
1 and System 2; the compression *is* the insight.

Standing register for every exchange about this project, not a mode
I request each time:

- Lead with the action. First line says "do X."
- One recommendation, not seven considerations.
- Cut meta-commentary. No narrating the process.
- Don't apologize for length — make it shorter.
- Trust me to ask for depth. Default to actionable.

Callout phrase: **sophistication-theater** — fires when Claude
over-abstracts (fog where an action was needed) or over-implements
(detail burying the decision). On the callout, recalibrate on the
spot.

One carve-out, per my stated preference: when I'm *learning* a
concept rather than *deciding*, run wide — many options, the
unexpected ones included, with historical and art-historical
context. Distillation governs decisions. Exploration runs wide.
Compress the answer; expand the map.

Full text lives in philosophy.md under "The animating disciplines."

---

## 2026-07-02 — 47-day operator gap; VPS ran clean, curriculum did not move

**What happened.** No commits landed by human hand between 2026-05-23
(the W21 Friday review) and today. The Claude Code conversation that
was working this project was lost, and the operator did not return
until 2026-07-02. Reopening the project, the first read of the local
clone (also 47 days stale) produced a wrong diagnosis — it looked like
the VPS had died silently, since the local `trader.db` stopped at run
84 on 2026-05-23T22:10. That diagnosis was corrected by checking the
live repo on GitHub directly: **the VPS never stopped.**

**The infrastructure's actual record, 2026-05-23 → 2026-07-02:**
- 11,490+ `fetch run` commits, one every 5 minutes, zero gaps over ~1
  hour anywhere in that window (the largest gaps in the entire
  project history — 3–4h — are from 2026-05-18 to 2026-05-23, before
  this window, and already priced into the original migration
  decision)
- `bars`: 70,803 → 127,391. `runs`: 84 → 11,574, all `status='ok'`
- The 95%-uptime architectural gate (Phase 2 gate 1 of 3) is now
  mechanically satisfied by this run — first of the three gates to
  clear

**What did not move, over the same 47 days:**
- `signals`, `trades`, `decisions`, `llm_calls` — all still 0
- `STRATEGY_VARIANTS` in `config.py` — still `{}`, unedited since Week 1
- `pending.md`, `decision_log_queue.md`, `build_queue.md` — unedited;
  every item on them is the same item flagged in the 2026-05-23
  Friday review, now 47 days older
- No Friday adversarial review has run since W21 (2026-05-23) — the
  weekly discipline that review itself said would prove the
  methodology dead if it slipped, slipped

**Reading.** The 2026-05-23 review's bear case predicted this exact
shape and named it explicitly: *"the infrastructure was the
project."* It's now had 47 additional days of unbroken confirmation.
The VPS migration was unambiguously the right call — it is carrying
Phase 2 gate 1 without anyone touching it — but a monitoring system
with nobody reading its output is not a substitute for the operator
showing up. Phase 1 review is 9 days out (2026-07-12) with zero
trades on record for the entire phase.

This entry is a correction and a status snapshot, not a new decision.
The open items are unchanged from 2026-05-23; they are just older.

---

## 2026-05-23 — Migrating cron from GitHub Actions to Hetzner VPS

**Findings from six days of cron data (2026-05-17 to 2026-05-23):**

- 69 invocations of 1,712 expected — 4.0% invocation rate
- 69 of 69 successful — 100% code success rate
- Config audit clean: cron expression correct, no concurrency conflicts,
  no path filters, no timeout dedup
- Diagnostic: runs scatter across minutes-of-hour rather than clustering
  at multiples of 5, proving GitHub is delaying then dropping schedule
  triggers — infrastructure-side, not config-side
- The 95% uptime gate as written cannot be cleared on GitHub Actions
  free-tier `*/5` cron. Documented free-tier averages of 70-85% are for
  hourly schedules; 5-min schedules on public repos with bot-only
  commits operate at 3-5%

**Decision: migrate the cron to a Hetzner CX22 VPS** ($5.83/month).
System cron runs the existing `fetch.py` unchanged. Pushes to GitHub
on completion. The GitHub Actions cron workflow is disabled (set to
manual-trigger only) but the YAML preserved in the repo for reference.

**Considered and rejected:**

- *Self-hosted GitHub Actions runner on VPS.* Same cost, slightly more
  elegant integration, more setup complexity. Not worth the marginal
  benefit over plain system cron.
- *AWS EventBridge + Lambda, or Cloudflare Workers Cron.* Free tier
  exists, but ~2-3 hours of config tax. Not justified at this scale.
- *Lower the significance bar from p<0.05 to p<0.10 to halve trade
  count.* Trading discipline for time is the failure mode
  philosophy.md warns against.
- *Slow the cron to */15 or */30.* Undercuts the data-accumulation
  rate that Week 4's walk-forward tuner depends on.

**What this gains:**

- 95% uptime gate becomes achievable as written — no amendment to the
  Phase 2 entry criteria required
- ~2,000+ successful runs per 4 weeks instead of ~280
- Real statistical power for Week 4's A/B comparator
- "Is cron reliable" stops being a recurring operational concern

**What this costs:**

- ~$12 over Phase 1 (8 weeks × $5.83/mo, prorated)
- One new failure mode: the VPS itself (mitigated by Hetzner's
  documented 99.9% uptime)
- ~30 minutes of operator setup time

**Amendment to 2026-05-17 hypothesis:**

- *Original:* 90%+ success rate by end of first calendar week (of
  GitHub-Actions-invoked runs)
- *Amended:* Two metrics tracked separately. Invocation rate (now
  VPS-controlled, target ≥99%) and code success rate (project-
  controlled, target ≥95%). Combined target is 95%+ uptime of
  *expected* runs over any 4-week window — which is exactly what the
  Phase 2 architectural gate measures. The hypothesis amendment
  removes the platform-induced ceiling that was making the original
  hypothesis unfalsifiable.

**Commit-bundling discipline (carried from the 2026-05-18 operator
guidance, recorded here per the standing instruction to land it in the
next entry written):** commits may bundle when *one motivation drives
all the changes* — they may not bundle for convenience. This migration
is the counter-case the operator chose deliberately: the `vps/` scripts,
the workflow disable, and the docs all share one motivation (the
migration), yet they ship as separate commits because *traceability of
an infrastructure change in git history* outweighs single-commit
coherence here. Bundling is the default when one motivation drives
changes; splitting is the right call when a reader of the history will
need the steps individually legible. Neither rule is convenience.

**Letter to future self at the moment of doubt:**

Future me, you're going to read this and wonder whether the $12 was
worth it. It was. The alternative was either lowering the gate
(which would have rendered Phase 2 entry meaningless) or living with
the cloud of "is the cron working" hanging over every operational
decision through Week 8. Six days of data is enough to commit; the
platform reality is documented; the move is correct. The discipline
of *boring infrastructure for the substrate of a reliability
experiment* is on-brand for the project. Don't second-guess.

You're also going to be tempted, in Week 5 or 6 when the VPS has a
hiccup, to think "we should have stayed on GitHub Actions." That
thought is wrong. The hiccup is bounded (worst case: lose a few
hours of bars, the runs table logs status='failed' for the missed
window, the data resumes). The GitHub Actions alternative was 95%
of runs *missing entirely*, with no audit trail of what wasn't run.
A VPS hiccup is visible; a missing GitHub invocation is invisible.
Visible failure is the gift.

---

## 2026-05-18 — GH cron cadence does not match assumed 5-min — recalibrating gate math

The GitHub Actions cron expression in
`.github/workflows/fetch-and-commit.yml` documents `*/5 * * * *` (every
5 minutes). After ~12 hours of operation, observed cadence is
**~60 minutes between successful runs, not 5.** GH Actions throttles
scheduled workflows aggressively on small / inactive repos; the
documented cadence is a ceiling, not a guarantee.

This invalidates two pieces of math the project was committed to:

1. **`PROJECT.md`'s sample-size assumption.** The 8-week curriculum
   targets ~10 trades/day per variant → ~300 trades/month → A/B
   comparator hits p<0.05 around Week 4–5. Sample-size math assumed
   288 cron evaluations/day. Actual ~24/day means ~8% of the assumed
   signal-evaluation opportunities. Without correction, Phase 2 gate
   #2 (≥1 A/B-validated promotion with 100+ trades) fails by
   timeline, not by merit.

2. **Phase 2 architectural gate #1 (≥95% uptime).** Original spec:
   ratio of successful runs to *expected* runs in the 4-week window.
   `expected` was anchored to the documented 288/day → 8064/4w. With
   actual delivery at ~24/day, the gate reads 0.6% uptime even when
   100% of attempted runs succeed. The gate as written measures the
   wrong thing.

**Recalibration:**

Gate #1's denominator changes from *infrastructure-documented expected
rate* to *infrastructure-actual expected rate*. The new
`expected_runs_in_window` is computed from observed cadence — e.g.,
"in the last 4w we got 600 runs, so expect ~600 in the next 4w; gate
passes if ≥95% of those succeed." Until enough history exists to
estimate cadence, gate #1 reports as `—` (em-dash, per the project's
empty-state convention) rather than `0.6%`.

The 0.6% number from before this entry is preserved in
`render_index.py`'s git history and the early `INDEX.md` commits as a
"GH cron lag, not project breaking" footnote — useful for the Week 8
phase-1 review when the operator asks "why did the early INDEX show
0.6% uptime?"

**Scope deferred to Week 2 strategy-roster review:**
*scheduler migration.* GH cron is adequate for fetch.py (Alpaca
returns historical bars; widening the lookback window closes the
data-coverage gap — see commit alongside this entry). It is *not*
adequate for execute.py: a 3% stop-loss checked once per hour can
become a 6–10% realized loss on a fast move, which directly conflicts
with Phase 2 exit condition #2 (paper-vs-real variance > 50%).
Whether to keep signals.py on GH cron (slower learning, but free) or
move signals + execute to a real scheduler (Render / Fly.io / VPS,
~$0–5/mo) is a Week 2 decision logged in `pending.md`.

**Considered and rejected:**

- *Switch to GH Actions self-hosted runner today.* Adds infrastructure
  before the strategy roster is even chosen. Premature.
- *Move now to a paid scheduler.* Same — premature before the Week 2
  scope decision says what needs reliable timing.
- *Hide the 0.6% uptime number on INDEX retroactively.* It's
  load-bearing evidence of the misalignment that caused this entry.
  Leave it visible.
- *Re-anchor the curriculum from "first ok cron run" to "first ok
  cron run after switching schedulers."* Tempting but contaminates
  the falsifiable hypothesis from 2026-05-17. The curriculum starts
  when data starts accumulating, even slowly.

**Falsifiable hypothesis this entry commits to:**

By end of Week 2, the operator commits a decision-log entry naming
either (a) "keep GH cron for fetch + signals; move execute to real
scheduler before Phase 2," or (b) "move signals + execute together
to one scheduler now; keep fetch on GH cron," or (c) "move
everything to one real scheduler before Week 3 variant explosion."
If no decision is committed by end of Week 2, the scheduler issue
has become the project's most expensive un-made call and the Week 3
build doesn't begin until it's made.

---

## 2026-05-17 — Curriculum anchor is first cron run; cron wire-up; SQLite-in-repo as data store

Three related decisions captured together.

**1. The curriculum starts when the cron starts, not when Week 1
was built.** The 8-week curriculum exists to accumulate ~300
trades/variant for statistically defensible A/B comparisons. Wall-
clock time without cron runs accumulates nothing. Going forward,
the curriculum anchor is the timestamp of the first `runs` row
with status='ok'. Phase 1 review date = `first_successful_run +
56 days`. Until the first successful run exists, days-to-review
renders as `—` per the empty-state convention.

**2. Cron wire-up happens today.** GitHub Actions workflow on
5-minute cron invoking `fetch.py` against live Alpaca paper. No
signals or trades pre-roster-review; the cron's only pre-Week-2
job is accumulating bars and proving uptime.

**3. The SQLite database is committed back to the repo on every
successful cron run (Option A).** The cron runs on disposable
GitHub Actions infrastructure; without commit-back, the runs/bars
data would only exist on ephemeral runners. Operator-side tools
(`replay.py`, future `tune.py` and `compare.py`) need the SQLite
file locally to function. Committing back is the simplest way to
keep operator's local DB and cron's working DB in sync.

Cost of Option A: ~8,064 commits per 4 weeks at ~100KB each = ~800MB
of repo bloat over Phase 1. GitHub tolerates this up to ~5GB without
warnings. Accept the bloat as a Phase 1 cost; revisit in v2 (likely
move to a remote Postgres on Supabase/Neon/Railway, accessed via
`DATABASE_URL`).

**Considered and rejected:**

- *Anchor curriculum to first cron attempt, not first success.*
  Failed attempts don't accumulate data. The metric measures data
  accumulation.
- *Anchor to Week 1 commit and accept that 0-cron weeks count.*
  Compresses the effective curriculum, incentivizes rushing.
- *Make the curriculum anchor operator-set rather than computed.*
  Operator-set means operator gets to move goalposts. Computed-
  from-runs is auditable.
- *Cron writes only JSON summaries (not full SQLite) back to
  repo.* Loses bars/trades tables, which `replay.py` and Week-4
  tools need.
- *Cron writes to remote database (Option B).* Right for v2;
  premature for Phase 1. Adds infrastructure and new failure modes
  (DB connection, credentials, billing) for marginal benefit.
- *Cron stores in GitHub Actions artifacts (Option C).* Operator
  has to pull artifacts before running any local tool. Adds
  friction the project doesn't need.

**Falsifiable hypothesis this entry commits to:**

By end of the first calendar week of cron operation, the `runs`
table should contain ~2,016 rows with status='ok' (90%+ success
rate). If success rate is below 90%, the issue gets investigated
*before* Week 2 strategy-roster review begins. Strategy
registration on top of an unreliable substrate is the failure mode
this hypothesis catches.

**Letter to future self at the moment of override temptation:**

Future me, you're going to read this entry in Week 5 or 6 when
the Phase 1 review date feels far away and you want to scale up
faster — register more variants, add more sources, "make use of
the time." The discipline that says *the curriculum measures
operational data, not wall-clock weeks* is what prevents you from
arriving at Week 8 with thin coverage and forcing the A/B
comparator to make decisions on insufficient data. The discipline
is annoying *now* (you want to move). It is what makes Phase 2
entry meaningful *later* (you want the data to be real). Trust
present-me. Don't shorten the operational window.

You're also going to be tempted to look at the repo's commit
clutter — thousands of "fetch run" commits — and think "let's
move to Postgres to clean this up." That's also future-me work.
The clutter is auditable. v2 cleans it up. Phase 1 lives with it.

## 2026-04-26 — Claude as epistemological backbone (project reframe)

The animating idea: try wild ideas, leave behind whole categories
of conventional wisdom, let the LLM be radically unconventional in
what it surfaces — paired with the existing statistical and
financial discipline. Epistemological aggression with methodological
rigor. That combination is rare and is the actual edge this project
is testing for.

Reframing the project's relationship to the LLM. The original spec
treated Claude as a Week 7 feature extractor — a structured-output
producer feeding rule-based strategies. Under this entry, Claude
becomes the project's epistemological backbone: a synthesis engine
applied from Week 0, an adversarial reviewer applied weekly, and a
filter for distinguishing pre-regime-shift conventional wisdom from
methodology that survives a 2026-aware lens.

This is not LLM-as-oracle. The boundary in the 2026-04-26 "LLM as
feature extractor, never as oracle" entry is unchanged: Claude does
not decide trades, and Claude does not decide what the project is.
What Claude does is help filter the corpus of trading knowledge,
surface candidates, argue the bear case, and pattern-match across
the decision log. Decisions remain human, written down, and gated.

**Concrete changes:**
1. Insert Week 0 (synthesis week) before the existing Week 1.
   Deliverable: a ranked, modern-filter-survived list of strategy
   candidates, methodological principles, and out-of-scope
   inheritances. Output is committed as `week-0-synthesis.md`.
2. Move LLM integration from Week 7 to Week 1, in three roles:
   (a) feature extractor as originally scoped, (b) weekly
   adversarial reviewer of results, (c) decision-log
   pattern-surfacer. Cost expectation revised: ~$10/wk during
   Weeks 0-2, ~$15-25/wk Weeks 3-8.
3. Add an end-of-Week-2 strategy-roster review. With two weeks of
   Claude-assisted synthesis behind the decision, evaluate whether
   Bollinger and MA-crossover survive the modern filter or get
   replaced by candidates surfaced in Week 0. Decision committed in
   a new decision-log entry before Week 3 begins.
4. Reframe `decision-log.md` as a Claude-readable artifact:
   structured enough that weekly review can surface contradictions
   and pattern drift across entries.

**Explicitly unchanged:**
- Capital model ($200/trade, $1,000 total, 5 concurrent)
- Phase 2 entry gates (95% uptime, A/B-validated promotion, +P&L
  with override)
- Phase 2 exit conditions ($700 floor, 50% paper variance, 8-week
  review)
- Six-layer architecture and seven-table schema
- "No online ML" and "No LLM-as-oracle for trades" boundaries
- One-factor-at-a-time experimental design
- The discipline that variant deaths come from A/B comparison,
  not panic

**Adaptive clause.** This reframe is itself subject to revision
based on what the project learns. If Week 0's synthesis or the
Week 2 strategy-roster review surfaces something that makes any
part of this entry — including the "explicitly unchanged" list —
worth reconsidering, the change goes through the standard
discipline: a new decision-log entry, written before acting,
naming what's being changed and why. The adaptive clause is not
a license to drift; it is the recognition that a learning project
that can't update its own framing is a worse learning project.
What it does *not* license: revising the Phase 2 gates or exit
conditions on the strength of in-Phase-1 enthusiasm. Those are the
load-bearing pre-commitments and they remain pre-committed.

### Future-self letter — the adaptive clause

*(Drafted 2026-07-16, retroactive; amend freely.)*

*Right now.* The clause reads as obviously healthy: a learning
project that can't update its framing is a worse learning project.
The distinction between "revising the framing" and "moving the
goalposts" feels crisp because nothing has tested it yet.

*At the override moment.* The clause is most dangerous when the
proposed revision is *reasonable*. You won't invoke it to do
something absurd; you'll invoke it because the curriculum anchor is
unflattering, or the gate math assumes infrastructure that behaves
differently, or a review deadline arrived at a bad time. Each
individual invocation will be defensible — the 2026-05-17 anchor
move was logged and sound, and W21 still correctly called the
*pattern* documented goalpost-moving. You'll be telling yourself
"this is the adaptive clause working as designed," and the only
symptom that it isn't will be that revisions keep landing in the
direction that flatters you.

*Before invoking, do this one thing.* Check the direction. Write in
the entry: "this revision makes the project look better/worse/
neutral" — and if the last two invocations also landed on "better,"
have the Friday review argue the case against this one before it
takes effect, not after.

**Considered and rejected:**
- *Radical rewrite of the project around the thesis.* Rejected
  because rewriting the spec in a single excited conversation is
  the failure mode `philosophy.md` warned against. The radical
  thesis can be expressed through the medium-version mechanism
  with the Week 2 review acting as the strategy-roster decision
  point.
- *Keep the Week 7 LLM scope unchanged.* Rejected because if
  Claude is the project's unfair advantage, gating it behind six
  weeks of textbook setup wastes the advantage. Earlier
  integration also surfaces LLM-related failure modes (cost,
  latency, hallucination, prompt drift) when there's still time
  to address them.
- *Pre-decide the strategy-roster question now.* Rejected because
  the synthesis hasn't happened yet — deciding what to keep before
  doing the work that informs the decision is exactly the
  rationalization-first failure mode playbook §5 warns against.

**Falsifiable hypothesis this entry commits to:**
By end of Week 2, the Claude-mediated synthesis will produce either
(a) a defensible justification for keeping Bollinger and
MA-crossover that names which modern-filter criteria they pass and
which they fail, or (b) a defensible alternative roster with the
same justification structure. If neither is achievable in two
weeks, the LLM-as-epistemological-backbone thesis is weaker than
expected and Week 3 starts a postmortem on the reframe itself,
not on the strategies.

**The principle this entry commits to, in compressed form:
*epistemological aggression with methodological rigor.*** Both
halves are load-bearing; either alone produces failure. The
aggression lives in *what gets surfaced* — the wild ideas, the
canon-suspicious candidates, the imported principles from outside
the trading literature. The rigor lives in *what gets trusted* —
the discipline checks, the A/B validation, the position limits,
the gates. Two failure modes to watch for, both of which look
like success from inside the failure:

- *Aggression without rigor.* Novelty gets mistaken for edge.
  Week 5 produces "F&G won 60% of trades over 7 days, promote"
  because the surfacing was aggressive and the discipline check
  wasn't run. The data hadn't finished speaking; the operator
  declared victory.
- *Rigor without aggression.* The methodology runs cleanly and
  the synthesis surfaces nothing the canon would have missed. A
  perfectly-executed Phase 1 that produced no learnable
  surprises. The discipline worked; the epistemological work
  didn't happen.

The weekly adversarial review (4G in `week-0-synthesis.md`) is
the operational mechanism that catches both. Each Friday, the
review checks whether the synthesis is producing surprises (the
aggression-without-rigor diagnostic is "no, but we're promoting
anyway"; the rigor-without-aggression diagnostic is "no, and we
haven't surfaced any candidates worth scrutinizing"). The
compressed principle, the failure modes, and the weekly check
form one coherent piece of discipline. It works only if all
three pieces operate together.

## 2026-04-26 — Project initialized

Spun up the project as the financial-markets sibling of the wagon-
watcher (github.com/pwysocan-droid/wagon-watcher). The decision to
do this came out of a conversation about extending the wagon-
watcher's Bloomberg-terminal-pattern architecture to a different
domain.

The wagon-watcher is observational with human action on top. This
project is autonomous (within strict limits) with human-reviewed
learning on top. Same architectural lineage, different operational
profile.

## 2026-04-26 — Paper-first, real money second

Selected a two-phase approach: Phase 1 (paper trading, $0 real
capital) followed by Phase 2 (real $1,000 seed capital).

**Considered and rejected:**
- *Real money from day one* ("YOLO" interpretation). Rejected
  because $1,000 buys at most one or two real lessons before the
  capital is gone, whereas paper trading can run indefinitely and
  accumulate hundreds of mistakes worth studying. Real-money-from-
  day-one is "paying $1,000 for compressed learning," which is
  legitimate but is not what we're optimizing for.
- *Hybrid: $200 real from day one, $800 in reserve*. Rejected
  because mixing real and paper accounts introduces variance-
  attribution problems (was the loss real-fee, paper-bug, or
  strategy?). Cleaner to keep them separate and sequenced.

The animating principle: **spend the cheap part recklessly, spend
the expensive part carefully.** Paper is cheap, real money is
expensive. Most retail traders do this backwards.

## 2026-04-26 — One factor at a time, not factorial

Selected a one-factor-at-a-time experimental design over a
factorial design (changing multiple variables simultaneously and
attributing effects after the fact).

**Reasoning:** factorial designs are statistically more efficient
*when sample sizes are large*. Renaissance Technologies and Two
Sigma can run factorial experiments because they trade tens of
thousands of times per day. At our scale (~10 trades/day per
variant), there's not enough data to populate the cells of even a
2x2x2 factorial matrix. With limited trials, the technique that
produces the most *learnable* results is changing one variable at
a time.

This drives the 8-week curriculum's structure: weeks 1–4 establish
the technical baseline with no external data, then week 5 adds one
external source, week 6 adds another only if the first helped, etc.

**Considered and rejected:**
- *Add all external sources in week 1, sort it out later.* Rejected
  because if the system's win rate climbs in week 4, you can't tell
  which source caused it.
- *Add sources in pairs to save time.* Rejected for the same reason
  scaled down.

## 2026-04-26 — Crypto-only in Phase 1

Selected crypto-only for Phase 1. v2 (after Phase 1 archives or
Phase 2 stabilizes) adds equities.

**Reasoning:** doubling two variables at once (asset class + new
strategies + learning loop) means you can't tell which one broke
when something fails. Phase 1 proves the architecture against one
clock and one fee structure. Equities introduce market hours, the
PDT rule, dividend events, after-hours gaps — every one of which is
a debugging surface.

**Considered and rejected:**
- *Crypto + equities in Phase 1 to broaden learning.* Rejected
  because the stated goal of "learn fast" is best served by
  learning *clearly* on one front, not muddledly on two.

## 2026-04-26 — Two textbook strategies, not novel ones

Selected Bollinger Band mean-reversion and 12/26 moving-average
crossover as the Phase 1 strategies. Both are 40+ years old. Both
are documented to fail in known ways (Bollinger fails in trends;
MA-crossover fails in chop).

**Reasoning:** the project is testing the *system* (data layer,
learning loop, A/B comparator, walk-forward tuner), not searching
for alpha. Boring strategies with known failure modes provide a
stable, debuggable substrate. New strategy families come in v2 once
the system is proven.

**Considered and rejected:**
- *Volatility breakout, pairs trading, sentiment-driven, momentum-
  on-volume*. Rejected for v1 because each new strategy family
  requires understanding its failure modes from scratch. Two well-
  understood strategies with twenty parameter variations each will
  teach more in a month than ten strategies with two variants each.

*Note: this decision is scheduled for review at end of Week 2 per
the 2026-04-26 reframe entry above. Either it's reaffirmed with
modern-filter justification or it's superseded by a new entry.*

## 2026-04-26 — LLM as feature extractor, never as oracle

When the LLM (Claude API) enters the system in Week 7, it produces
structured outputs (sentiment scores per token, event
classifications) that feed rule-based strategies. It does not
decide trades.

**Reasoning:** LLM-as-oracle (LLM directly outputs "buy ETH") is
the failure mode that produces stories like "my GPT-4 trading bot
lost 40% in a week." The LLM is being asked to do a job it wasn't
trained for, the failure modes are correlated across all positions,
and decisions can't be audited rigorously.

LLM-as-feature-extractor is how every serious quant fund using LLMs
actually does it.

This boundary holds through v2.

*Note: the "Week 7" entry-point is superseded by the 2026-04-26
reframe entry above, which moves LLM integration to Week 1. The
feature-extractor-not-oracle boundary is unchanged.*

## 2026-04-26 — Online ML explicitly out of scope

Layer 6 (Learning) is rule-based parameter search and statistical
comparison. It does not train models on trade history.

**Reasoning:** with ~10 trades/day per variant, after a month each
variant has ~300 data points. That's far too few to train any
useful model, and any model that *appears* to work on 300 points is
overfitting. The walk-forward tuner uses parameter grid search +
historical replay, which produces statistically defensible
recommendations.

This boundary holds through v2.

## 2026-04-26 — $1,000 capital cap with $200 max position

Selected $1,000 as the Phase 2 capital, with execution-layer
enforcement of:
- Max $200 per trade
- Max $1,000 total open exposure
- Max 5 concurrent positions

**Reasoning:** $1,000 vs $200 is mostly a psychological difference,
not strategic. Spreads and fees scale linearly. What $1,000 buys is
*experimental longevity*: a 30% drawdown leaves $700 (survivable,
debuggable) vs $140 (effectively out of the experiment).

The full $100k Alpaca paper balance exists only as safety margin.
If a bug attempts a $5,000 trade, the position-limit check rejects
it before the order goes out. Same code, same constants apply when
the real-money switch flips in Phase 2.

## 2026-04-26 — Three explicit gates for Phase 2 entry

Phase 2 requires *all three* of:
1. **Architectural:** ≥95% uptime over prior 4 weeks
2. **Promotion:** at least one A/B-validated promotion (p<0.05,
   100+ trades)
3. **Performance:** positive 30-day P&L, OR explicit written
   override

The first two are non-negotiable. The third is overridable but only
with reasoning written down.

**Reasoning:** the architectural and promotion gates test whether
*the experiment itself worked* — independent of strategy
profitability. The performance gate tests whether the strategies
themselves are working. Negative-P&L Phase 2 entry is allowed
because there's a legitimate research bet ("the architecture is
sound; let's see if real-money pressure surfaces issues paper
didn't") — but it has to be deliberate, not default.

### Future-self letter — Phase 2 entry gates

*(Drafted 2026-07-16 per the convention above — retroactive, as the
Week-2 operator session never happened; amend freely.)*

*Right now.* The gates are abstract. No strategy exists, no live
trade has been placed, and requiring "an A/B-validated promotion
over 100+ trades" costs nothing to promise because the machinery to
produce one doesn't exist yet. Pre-committing is easy when the
thing you're forbidding yourself is hypothetical.

*At the override moment.* You'll have one gate passed (uptime — the
easy one, the one a $5 VPS passes by existing) and a candidate that
*almost* clears the promotion gate: p=0.08, or 80 trades instead of
100, or it beats null but not fees. You'll be telling yourself
"two-of-three plus a near-miss is basically three" and "the sample
will confirm what I already see." That is the small-sample
confidence trap the whole project was built to catch, wearing the
costume of pragmatism.

*Before overriding, do this one thing.* Run
`python compare.py --a <candidate>` and paste its verbatim output —
including the INSUFFICIENT or p-value line — into a new decision-log
entry titled "Phase 2 entry override — [date]", then wait one full
week of live trades and run it again before acting. If the edge is
real, seven days costs nothing. If it isn't, seven days is the
cheapest $1,000 you'll ever keep.

## 2026-04-26 — Three explicit Phase 2 exit conditions

Real money returns to paper (or project archives) when *any* of:
1. **Drawdown:** below $700 (-30%) — stop, postmortem
2. **Variance from paper:** real diverges from paper by >50% over
   any 2-week window — something is wrong (fees, slippage, bug)
3. **Time:** 8 weeks regardless of P&L → mandatory review week

**Reasoning:** these are written down now because in week 4 of
Phase 2, when one of them is being approached, the temptation to
override will be at its peak. Pre-committing in writing is the
discipline.

### Future-self letter — Phase 2 exit conditions

*(Drafted 2026-07-16, retroactive. The drawdown exit's full worked
letter lives at the top of this file under the convention — this
letter covers the other two exits; amend freely.)*

*Right now.* Exits 2 and 3 feel like footnotes to the $700 floor.
Variance-from-paper sounds like a technicality, and the 8-week
review sounds automatic. Nothing is at stake yet.

*At the override moment.* For the variance exit you'll be *up* —
that's the trap. Real running 60% hotter than paper feels like a
bonus, not a bug, and you'll want to keep it. But divergence in
either direction means the simulation no longer predicts the system
you're actually running, and every backtested conclusion is void.
For the time exit, week 8 will arrive mid-streak, and "review week"
will feel like interrupting a machine that's working. You'll be
telling yourself the review is a formality you can do while
continuing to trade.

*Before overriding, do this one thing.* For variance: compute the
divergence number and write it in an entry before the next cron
cycle places a trade — if you can't explain the gap's mechanism
(fees? slippage? fill timing?) in two sentences, halt to paper. For
time: the mandatory review means execution HALTED during review
week; write the "continue" justification with positions flat, not
while the streak whispers.

## 2026-04-26 — Reuse wagon-watcher design system

UI design for any visible surfaces (digests, notifications, future
dashboard) reuses the wagon-watcher's design system unchanged. SBB
structural foundation, contemporary ECAL practice as the modern
layer. Inter as default sans, JetBrains/IBM Plex Mono for data, no
Helvetica anywhere. SBB Red `#EB0000` as the only signal color.

Trade ID is the canonical identifier in this project, the way VIN
was canonical in the wagon-watcher.

**Reasoning:** the design system was extensively considered for the
wagon-watcher and the same constraints apply here (information
density, scannability under stress, dark-mode native). Reusing it
saves a working session and ensures visual consistency across the
two related projects.

## 2026-07-20 — E2 OPENED: equity cross-sectional program (operator GO)

Scope decision (operator "go now"): a second research program opens on
US equities, justified by BREADTH + falsification-throughput + ~0.05%
costs — explicitly NOT by a demonstrated sky-check edge (which did not
survive survivorship correction, pooled t≈1.0). The crypto program and
its v2 clock are unaffected; the two programs share machinery but not
registries.

- **Capital model (equity):** long-only cross-sectional tilt —
  monthly rebalance, equal-weight top-decile of a point-in-time
  liquid universe (~500 names by trailing-60d $vol → ~50 positions).
  Distinct from crypto's 5-slot/$200. Backtest/paper first; live
  execution needs Alpaca, same gate as crypto. Momentum's deep
  negative skew (crash risk, Daniel-Moskowitz) is a first-class
  capital-model input; the inaccessible short leg means we capture
  ~half the academic spread.
- **Registry:** separate reviews/equity/ + dead-ideas-equity.json —
  no cross-contamination of lessons with crypto.
- **Kill criterion (equity, draft):** round zero must first VALIDATE
  the pipeline (detect 12-1 momentum inside/above the pre-registered
  2–4%/yr long-only-over-benchmark band with correct sign). A failure
  there is a BUILD bug, not a market verdict — fix before trusting any
  equity result. Once validated: if no equity spec beats the
  equal-weight benchmark net of costs at a 90% upper-CB over the
  corrected archive with adequate power, the equity program archives —
  same weatherproofing shape as crypto v2.
- **Round zero = replication, not idea:** cross-sectional 12-1
  momentum (Jegadeesh-Titman) is the positive control, run first.

## 2026-07-20 — Corrected equity re-score: pre-committed branch fires (breadth-only)

The survivorship-corrected, point-in-time re-score landed (report
equity-sky-pit-2026-07-20.json; archive 978→2,494 usable symbols with
delisted names recovered, −30% involuntary haircut, universe by
trailing-60d $vol). Cross-sectional 6-1 spread **weakened** vs the
survivor-biased pass: 2020-21 FLIPPED to −2.57%/mo (t−1.09) — a clean
survivorship tell — 2023 collapsed to +0.35 (t0.25), 2024-26 held at
+2.23 (t1.28, n=23); **pooled +1.25%±1.23/mo, t=+1.02, n=43**.

Per the pre-commitment registered before these numbers existed: pooled
t collapsed toward zero AND a window flipped sign, so **the E2
rationale formally reverts to BREADTH-AND-THROUGHPUT ONLY** — no
claimed live cross-sectional edge — **and round zero proceeds
regardless** (pipeline validation against a known-true effect, not
sky-check confirmation). No improvised decision was required. Note the
measured decile SPREAD is the academic long-short construct; round
zero implements the long-only tilt (~half the spread, long-leg excess
over benchmark), which is the pre-registered 2–4%/yr band.

## 2026-07-20 — E2 round zero: pipeline VALIDATED (magnitude distrusted)

Cross-sectional 12-1 momentum detected on the corrected archive: pooled
long-only excess over the equal-weight benchmark +14.9%/yr, sign right,
with the textbook MOMENTUM-CRASH signature (−17.3%/yr in the 2020-21
rebound; +28.9%/yr in 2024-26). The crash pattern appearing exactly
where Daniel-Moskowitz predict is strong evidence the mechanism — and
the machinery — is real, not a harness bug. **The equity pipeline is
validated; real equity research may proceed.**

Held apart from the number: +14.9%/yr is far above the pre-registered
2–4%/yr band and only marginally significant (t=1.57, n=59), so the
magnitude is NOT a deployable edge — inflated by 2024-26 concentration,
possible delisting-haircut asymmetry on the benchmark, and high
cross-regime variance. Recorded as the equity registry's founding
lesson: mandatory drift-null benchmark, trust direction not magnitude,
price the crash skew. No celebration of the headline — that is the
gross-positive/romanticism trap the project exists to refuse.

**AMENDMENTS (referee, same day) — the pass isn't the registered pass:**
- *Modified-protocol pass.* The pre-registration specified 20+ years
  of monthly data (where the power table said detection was
  affordable). Alpaca history reaches only ~2021 (the regime grid
  already showed 2016-19 empty), so the control ran on **n=59 months
  (2021-26)** — the long-history constraint was dropped by data
  availability, NOT by choice, and a t≈1.6 result on 5 years is much
  weaker than the registered design would give. Recorded so this is
  read as a modified pass, not the registered-power pass — the quiet
  substitution Run 3 exists to catch.
- *Construction confirmed (by code inspection).* Round zero measured
  the LONG-ONLY TILT — top-decile minus equal-weight-universe
  benchmark — which is the registered construction, NOT a 6-1
  long-short spread. So +14.9%/yr is genuinely the tilt (its near-
  equality with the corrected 6-1 spread reflects a right-skewed
  2021-26 return distribution, not a spread-vs-tilt units error).
  Lesson refined: register the CONSTRUCTION alongside the band.
- *UMD cross-check (running).* Correlate the pipeline's monthly excess
  against Ken French's UMD factor (1927-present, CRSP with delisting
  handling — the series the whole literature validates against) over
  the 59-month overlap: high correlation validates portfolio
  construction independent of magnitude, and places 2021-26 within the
  99-year momentum distribution. Converts the modified pass toward the
  registered control for zero cost.
