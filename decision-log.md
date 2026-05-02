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
