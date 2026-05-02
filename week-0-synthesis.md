# Week 0 Synthesis — algotrading-paper

A working document, built across three sessions in Week 0, that
delivers the criteria-and-candidates synthesis the 2026-04-26 reframe
entry committed to. This file is the deliverable for Week 0; if it
isn't defensible by end of Week 2, the falsifiable hypothesis in the
reframe entry says we postmortem the reframe itself.

**Status:** Week 0 closed. Sessions 1 (criteria), 2 (ranked
candidates), and 3 (methodological audit) all complete.

---

## What this document is and isn't

This is the deliverable for Week 0 of the post-reframe curriculum:
a ranked, modern-filter-survived list of strategy candidates and
methodological principles, with explicit reasoning for what got
elevated, what got demoted, and on what grounds.

It is not a strategy recommendation, a trade plan, or a piece of
financial advice. It is the upstream artifact that *informs* the
strategy-roster decision committed at end of Week 2 — at which point
either Bollinger and MA-crossover are reaffirmed with modern-filter
justification, or they're replaced by candidates surfaced here.

It is also not a substitute for the discipline embedded in
PROJECT.md, philosophy.md, decision-log.md, and playbook.md. Those
files remain the source of truth for gates, capital model,
architecture, and operational rules. Nothing in this synthesis
revises those — the reframe's adaptive clause is explicit that
in-Phase-1 enthusiasm cannot revise the load-bearing
pre-commitments.

---

## The criteria question

Before any candidate gets ranked, the criteria question has to be
settled: *what does the modern filter actually demote, and what does
it elevate?* Without an auditable answer, the ranking that follows
is preference dressed up as method.

The answer has two halves: demotion criteria (reasons to deprioritize
inheritances from the textbook canon) and elevation criteria
(reasons to surface candidates the canon would have missed). Each
elevation criterion is paired with a discipline check — the
mechanism that prevents epistemological aggression from collapsing
into "anything goes."

This pairing is the operational meaning of the thesis stated in the
reframe entry: *try wild ideas, leave behind whole categories of
conventional wisdom, let the LLM be radically unconventional in what
it surfaces — paired with the existing statistical and financial
discipline.* The aggression lives in the elevation criteria; the
rigor lives in the discipline checks. Neither half is optional.

---

## Demotion criteria

A strategy or methodological principle gets demoted in the synthesis
if it depends — implicitly or explicitly — on any of the following.

**1. Pre-microstructure-shift assumptions.** Strategies and analysis
written before the maturation of Reg NMS (mid-2000s), the rise of
HFT and internalizers (2007–2015), and payment-for-order-flow
normalization. Most pre-2010 retail strategy literature assumes a
market where retail orders sit in a fair queue alongside
institutional orders. They don't, and haven't for over a decade.
Anything implicitly relying on this assumption — most "exploit the
spread" or "fade the close" tactics from the 1990s — gets demoted.

**2. Pre-crypto, pre-24/7 assumptions.** Strategies that depend on
overnight gaps, market-open volatility, opening auctions, end-of-day
rebalancing flows. These are equity-market structural artifacts.
Crypto has no overnight, no opening auction, no closing print. A
strategy whose theoretical edge comes from one of those events
doesn't have an analog in your asset class. Filter it out for Phase 1.

**3. Pre-LLM-era asymmetry assumptions.** Strategies built around
the premise that retail traders can't process unstructured text at
scale. News-flow trading, sentiment trading, earnings-call analysis
— these were institutional-only because the labor cost of reading
was the moat. That moat dissolved in 2023. The modern filter
elevates strategies that *use* this dissolution, and is suspicious
of any strategy that justifies itself by the (now-obsolete)
information-processing asymmetry.

**4. Pre-zero-fee assumptions.** Strategies that worked at 0.5%
commission per trade and stop working at 0.05% — and the inverse:
strategies that *only* worked because fees crowded out smaller
competitors are now arbitraged away. Net effect: any strategy whose
backtest predates the fee compression should be re-tested at modern
fee levels before being trusted.

**5. Survivorship-bias-laden literature.** Strategy advice that
comes from "the books that got published" rather than "the
strategies that worked at retail scale." A permanent demotion
criterion, not regime-specific, but worth being explicit about
because most of the textbook canon is published-survivor output by
definition. Demote anything whose evidence base is "this worked for
[named author] over [named period]" without independent replication.
Elevate anything whose evidence base includes documented failures.

**6. Single-asset-class generalizations.** Strategies validated on
US equities and assumed to generalize. Most of the published quant
literature is implicitly equity-centric. Crypto's microstructure
(no uptick rule, no PDT, perpetual futures with funding rates, MEV,
exchange-specific liquidity) breaks many of the assumptions. The
modern filter treats "I learned this on SPY in 2010, applying it to
BTC in 2026" as a hypothesis, not a transfer.

### Considered and excluded

Two demotion criteria were considered and explicitly *not* adopted,
to keep the filter focused:

- *Pre-AI-trading-era assumptions* (the question of other algorithms
  now being on the other side of your trades). Excluded because at
  retail size the AI-on-the-other-side question is mostly noise.
- *Pre-regulatory-clarity crypto assumptions* (everything written
  before SEC/CFTC enforcement actions of 2022–2024). Excluded
  because most retail strategies don't depend on regulatory
  ambiguity, and the criterion is narrower than the others.

If subsequent sessions surface candidates that hinge on either of
these considerations, the criteria question gets reopened with a
decision-log entry. Until then, they stay excluded.

---

## Elevation criteria (with paired discipline checks)

A strategy or methodological principle gets elevated in the
synthesis if it satisfies any of the following — *and* survives the
paired discipline check.

**1. Strategies whose theoretical edge comes from a structural
feature that didn't exist before 2015.**

*Discipline check.* "Couldn't have existed before 2015" is necessary
but not sufficient. The strategy still has to have a defensible
mechanism. Funding-rate carry on perps is mechanism-grounded.
"AI-driven sentiment from Twitter" needs to specify *what* about the
sentiment is informative and *why* it isn't already priced. Name the
economic mechanism or assume the edge isn't real.

**2. Methodologies that became cheap or accessible in the LLM era,
not just data inputs that did.**

*Discipline check.* The methodology only counts if it produces an
artifact you can audit. A weekly adversarial review that doesn't
produce a written record is the same as not having one. Output of
LLM-assisted methodology has to be a committable file, not a
feeling.

**3. Strategies and frames the canon documented as failing, on
grounds that may have been regime-specific.**

*Discipline check.* This is the most dangerous criterion, because it
can be used to rationalize any failed strategy by claiming "the
regime is different now." Any candidate elevated under this
criterion has to specify *which* regime feature changed and *why*
that change reverses the documented failure mechanism. If the answer
is hand-wavy, demote.

**4. Principles from outside the trading canon that survive being
applied to it.**

*Discipline check.* Imported principles only count if they survive
translation to the specific operational context. An imported
principle that can't be translated to a concrete artifact in this
project is just intellectual flavor.

**5. Strategies and frames whose absence from the canon is itself
suspicious.**

*Discipline check.* Two parts. First: any candidate elevated under
this criterion has to be falsifiable by the system being built —
testable on paper for at least 30 days with the existing
infrastructure. Second: it has to be elevated *as a hypothesis*, not
as a conclusion.

---

## Ranked strategy candidates

Surfaced across five clusters in Session 2. First-pass generation
produced 24 candidates; honest scrutiny kept 13 (six clean passes,
seven probational/with-caveats), with eleven demoted. Each candidate
is tagged with its elevation criterion and the specific discipline
check it had to survive.

### Clean passes

**1A. Funding-rate carry on perpetual futures.** *(criterion 1)*
Mechanism: funding payments on perps are contractual cash flows
between longs and shorts, calibrated to keep perp price aligned with
spot. Strategy: short perp + long spot to capture funding while
delta-neutral. Substrate didn't exist before 2016 (BitMEX).
Discipline check passes: mechanism is a real cash flow; failure mode
is documented (funding flips negative in sustained downtrends, spot
leg can move against the position). Caveat: the original generation
skipped quantitative breakeven analysis; needs explicit modeling of
funding rate vs. borrowing cost on spot leg vs. exchange fees on
both legs before any live deployment.

**4A. Preregistration.** *(criterion 4)* From clinical trial
methodology. Each week, write the week's hypothesis to a committed
file before the week starts, with a numerical confidence level. By
Week 8, eight predictions and eight scorings exist. Concrete
artifact: `reviews/YYYY-WW-prediction.md`. Failure mode: predictions
become generic over time as novelty wears off; mitigation is that
the Friday adversarial review (4G) checks specificity.

**4C. Blast-radius analysis.** *(criterion 4)* From site reliability
engineering. Before any change, write a one-paragraph "worst case
if this fails / bounded by" statement. Forces explicit articulation
of what bounds the worst case — which catches cases where the
operator thinks something is bounded but it isn't. Concrete artifact:
a paragraph appended to every decision-log entry that introduces
something new.

**4F. Future-self letters.** *(criterion 4 — adopted from operator
contribution)* From Kahneman & Tversky on affective forecasting and
the remembering vs. experiencing self. At the moment each
pre-commitment is written, also write a "letter to future self at
the moment of override temptation" that anticipates the *specific
cognitive distortion* future-self will be experiencing. Inheritor of
a long tradition (Marcus Aurelius's *Meditations* are literally
2nd-century letters to future self at moments of weakness).
Concrete artifact: a section appended to specific decision-log
entries — the three Phase 2 exit conditions, the three Phase 2 entry
gates, the reframe entry's adaptive clause, and any future entry
creating a hard rule.

**4G. Weekly adversarial review.** *(criterion 4 — formerly 2A,
moved into cluster 4 conceptually)* Each Friday, a structured
session where Claude argues the bear case against the week's
results — forced steelmanning of "your strategies are overfit, your
promotion was lucky, the new data source is noise." Concrete
artifact: `reviews/YYYY-WW-friday.md`. Failure mode: Claude drifts
toward soft bear cases over time; mitigation is comparing each
Friday's bear case to the prior week's and flagging if the case is
getting milder.

**4H. Decision-log pattern surfacing.** *(criterion 4 — formerly
2C, moved into cluster 4 conceptually)* Once a month, Claude reads
the full decision log and surfaces contradictions, drift, or
patterns the operator wouldn't have noticed. Concrete artifact:
`reviews/YYYY-MM-patterns.md`. Failure mode: surfacing on superficial
textual similarity rather than actual decision drift; mitigation is
that every surfaced pattern must include quoted text from the
entries being linked.

**5E. Cross-asset conditioned strategies.** *(criterion 5)* Strategy
class where a technical pattern in asset A is conditioned on a state
in asset B (e.g., altcoin mean-reversion conditioned on BTC
dominance state; perpetual-funding mean-reversion conditioned on
overall-market funding aggregate). Canon underrepresents because the
*form* of single-asset strategies fits textbook chapters more
cleanly. Operability is strongest of the cluster: the project's
existing `context_data` schema is essentially designed for this.
Discipline check passes: testable directly, mechanism is concrete
(cross-asset conditioning leverages information that single-asset
technical strategies discard).

### Probational passes / kept with caveats

**1D. Funding-rate-conditioned mean reversion.** *(criterion 1)*
Distinct from 1A. Uses funding as a *signal* (extreme positive
funding suggests crowded longs and elevated mean-reversion-down
probability) rather than as a cash flow. Mechanism is sound
(positioning theory). Caveat: this is mean-reversion with a feature,
adjacent to the project's existing Bollinger candidate. Whether it
counts as a novel candidate or a feature-engineering layer on top of
existing mean-reversion depends on how strictly criterion 1 is
defined for the Week 2 review.

**3A. Crypto calendar effects.** *(criterion 3)* Calendar effects
in equities (January, Monday, turn-of-month) were arbitraged away by
deep professionalized arbitrage by ~2010 and treated as definitively
dead. Caporale & Plastun (2019) documented persistent calendar
effects in crypto, where the arbitrageur population was structurally
different. Caveat: by 2026, crypto market-making has substantially
professionalized; the regime difference may have closed since the
2019 evidence. Needs to be re-tested at 2026 conditions, not assumed
from cited literature.

**3B. Crypto pairs trading.** *(criterion 3)* Pairs trading in
equities deteriorated from the early 2000s due to crowding among
quants running the same pairs. Crypto has structurally fewer
cointegrated pairs but the pairs that do cointegrate are less
crowded. Caveat: the most-watched pairs (ETH/BTC vs. SOL/BTC) are
heavily covered by quant funds. The retail-accessible portion is
plausibly a long tail of less-watched pairs, but the discipline
check requires *specific* pair identification, not generic
"less-professionalized" gestures.

**3D. LLM-mediated news-flow trading.** *(criterion 3)* News-flow
trading at retail historically failed on speed (professionals
arbitraged news within hours). Speed disadvantage is partially
reversed by LLM-mediated parallel reading. Hidden assumption now
surfaced: this only works for *medium-frequency* news effects
(governance proposals, dev announcements, regulatory statements that
take hours-to-days to fully impact prices). High-frequency news
remains institutional. Already implicitly committed in the project
via the LLM-as-feature-extractor scope; criterion 3 lens makes the
inheritance explicit.

**4B. Calibration tracking.** *(criterion 4)* From Tetlock's
forecasting research. Each preregistered prediction (4A) gets a
numerical confidence; calibration plot at Week 8. Caveat: 8 weekly
predictions is too few for statistically meaningful calibration; this
is a *seeded* discipline whose data becomes useful in Phase 2 and
v2, not a Phase 1 deliverable.

**4E. Reference-class forecasting.** *(criterion 4)* From Flyvbjerg's
empirical work on the planning fallacy (downstream of K&T). Before
each promotion decision, ask "of similar walk-forward-tuned variants
in my last N decisions, what fraction subsequently outperformed?"
Caveat: same as 4B — Phase 1 will have 1-3 promotions total, so the
internal reference class isn't useful in Phase 1. Seeded practice.

**5A. Operator-discipline strategies (specific instance only).**
*(criterion 5)* Strategy class where the canon's "doesn't generalize"
verdict reflects unrealistic operator behavior assumptions. Caveat
is severe: kept *only* as specific instances (e.g., "trend-following
with code-enforced exits and code-enforced position sizing on a
single asset"), not as a class. The class is too easy to rescue with
discipline-scaffolding gestures. The bear case identified three
problems with the bull reading: (i) the discipline gap may not be
the binding constraint — fees and slippage often consume the edge
before operator error matters; (ii) the framing flatters the project
specifically and the bull reading was suspiciously self-serving; (iii)
the project's scaffolding addresses ~20% of the operator-error
surface, not the full surface the canon was actually documenting.

**5B. Sub-institutional capital scale strategies.** *(criterion 5)*
Strategy class with edge at $1,000-$100,000 of deployed capital but
not at $1,000,000+. Structurally invisible to canon's three main
author populations. Caveat: specific instances tend to require
venue-specific access (small DEXes, micro-cap exchanges with poor
APIs) that may fail operability on access grounds even though they
pass on system grounds.

### Demoted

These eleven candidates were surfaced in first-pass generation but
did not survive the discipline check. Demotions are listed so the
rejection is auditable.

**1B. DEX-CEX basis arbitrage at retail size.** *(criterion 1)*
Demoted for failing the falsifiability discipline check at $200
position size: gas costs eat margins on less-liquid pairs, and
heavily-arbitraged liquid pairs leave nothing for retail. The
candidate's "probationally pass with caveat" mark in first-pass
generation was conflating "interesting strategy class" with
"survives the filter."

**1C. On-chain-flow-conditioned spot strategies.** *(criterion 1)*
Demoted as theatrical — wrong cluster (closer to sentiment indicator
than structural arbitrage; belongs under criterion 3 if anywhere)
and the criterion 1 elevation rationale was waved through in
first-pass generation without surviving honest scrutiny.

**2B. Weekly pre-mortem.** *(criterion 2)* Demoted as scope-creep
beyond what the reframe committed to, but parked on the
"candidates for inclusion" list in `roadmap.md`. Methodology is
sound; cost is recurring weekly overhead that goes beyond the
reframe's adopted methodology budget.

**2D. Counterfactual analysis on rejected trades.** *(criterion 2)*
Demoted as scope-creep, but parked. Worth implementing as a Layer 5
analytics feature regardless of whether it's adopted as a formal
methodology.

**2E. Continuous literature surveillance.** *(criterion 2)* Demoted
on operability grounds — the failure mode (generative padding when
nothing actually warrants surfacing) is the hardest to discipline-
check, and the value capture is low at this scale.

**3C. Chart-pattern recognition.** *(criterion 3)* Demoted as
theatrical. The bull case argued LLM vision reverses the failure
mechanism (human cognitive limits + confirmation bias); the bear
case is that automated chart-pattern detection has existed for
decades via classical computer vision and was already part of the
documented failure. The "LLM vision is new" framing was cosmetic.

**3E. Sub-minute mean reversion.** *(criterion 3)* Demoted as
failing the basic operability check. The system runs on a 5-minute
cron and trades at $200 position size; sub-minute strategies aren't
operable by this system regardless of regime arguments.

**4D. Pre-mortems.** *(criterion 4)* Cross-reference only — already
parked under 2B. Not re-elevated; tagged to make the import-from-
decision-research lineage visible across criteria 2 and 4.

**5C. Retail-flow fade strategies.** *(criterion 5)* Demoted on
bear-case scrutiny. The publication-lag argument cuts both ways
(the *market* doesn't lag the academic literature, it leads it);
the specific edge cases cited (weekend buying in crypto, options
expiration pinning) are heavily traded by professional market
makers; the retail trader has lagged public data while market makers
have direct order-flow data — the information asymmetry runs the
wrong direction. Canon's underrepresentation isn't a structural
blind spot here; it's the canon being slightly slow to publish the
obituary on a class that's already been monetized.

**5D. Publication-lag strategies.** *(criterion 5)* Demoted on
operability. McLean and Pontiff (2016) document the mechanism
(anomaly returns degrade ~58% post-publication), and the working-
paper window before publication is real. But detecting the window
requires the literature-surveillance methodology that was cut as
2E. Without 2E, the strategy class is theoretically real but
practically unreachable by the project as currently scoped.

**Three candidates cut at front-loaded operability check, not
generated:** *Strategies requiring proprietary information access*
(failed operability immediately); *strategies requiring sustained
attention during market hours* (project is cron-driven specifically
to avoid this); *crowd anti-coordination strategies* (no concrete
way to define "the obvious game-theoretic optimum" that doesn't
require subjective operator calls each time — fails no-ceremony
test).

---

## Methodological principles audit

Session 3 audited the existing trading-canon methodologies the
project has inherited or adopted, against the same modern filter.
Most existing choices passed clean. Two were flagged for explicit
re-examination at Week 8. One surfaced as a build-quality concern
for Week 1.

The audit is structured by cluster, with each existing methodology
tagged: **kept clean** (no modification), **kept with note** (small
clarification or context flag), **kept as stance** (not an artifact
to build but a discipline to maintain), or **flagged** (worth
explicit re-examination at a specific later point).

### Cluster A — Backtest and validation

**A1. Walk-forward validation.** Already adopted via `tune.py` —
nightly run, 30-day window, parameter grid, top-3 candidates to
`recommendations`. The right choice for the regime: standard
cross-validation is broken for time-series because it leaks future
information into past predictions. Walk-forward is the correct
frame. **Kept clean.**

**A2. 30-day window for walk-forward.** Defensible default.
~10 trades/day × 30 days ≈ 300 trades — enough to be statistically
suggestive, not enough to be definitive. Shorter windows adapt
faster but suffer more noise; longer windows lag regime changes.
30 days is a reasonable middle. Multi-window walk-forward (7, 30,
90 days simultaneously) would surface regime-change adaptation
explicitly but is v2 scope. **Kept with note: single-window is
fine for Phase 1; multi-window is v2.**

**A3. Sharpe ratio as primary success metric.** The strongest
inheritance signal in the audit. Sharpe is canonical but has known
weaknesses: it assumes near-normal return distributions (crypto
returns have fat tails, so Sharpe systematically understates tail
risk); it penalizes upside volatility the same as downside; at 30-
day windows with ~300 trades, Sharpe estimates have substantial
standard error. Modern alternatives the canon underweights: Sortino
(penalizes only downside), Calmar (return / max drawdown),
Probabilistic Sharpe Ratio (López de Prado, 2012). **Flagged for
Week 8 review.** Don't change in Phase 1 — consistency matters for
the experiment. But the Week 8 phase-review reports Sortino and
Calmar alongside Sharpe, and the Phase 2 entry decision considers
all three rather than only Sharpe.

**A4. Statistical significance via p<0.05.** Textbook threshold,
fairly weak in multi-comparison contexts. With 10 variants, the
probability of at least one pair showing p<0.05 by chance alone is
~40%, not 5%. Standard fixes: Bonferroni correction (conservative),
Benjamini-Hochberg FDR (less conservative, more powerful), or pre-
specifying the comparison. The project's 4A preregistration
methodology addresses this: if each week's hypothesis is committed
in writing *before* the week starts, the comparison is pre-
specified and the multiple-comparison problem largely disappears.
**Kept with note: p<0.05 is fine *given* the preregistration
methodology; the connection should be explicit in the Week 2 review
and any future promotion-decision entries.**

### Cluster B — Position sizing and risk management

**B1. Fixed-fractional position sizing ($200/trade).** Simplest of
the position-sizing methodologies. Alternatives include Kelly
criterion (mostly wrong for retail — assumes you know your edge,
which you don't, and overestimating with Kelly produces ruinous
drawdowns), volatility-adjusted sizing (defensible but adds
complexity), risk parity across variants (similar tradeoff). Fixed-
fractional is the right choice for a project explicitly testing the
system rather than searching for alpha. **Kept clean.** Volatility
adjustment is a v2 candidate.

**B2. -3% stop-loss / +5% take-profit / 24-hour time exit.**
Highly inherited. The 3:5 ratio and 24-hour horizon don't have
specific theoretical justification — they're plausible defaults.
A specific concern: a fixed 3% stop on BTC behaves very differently
from a fixed 3% stop on AVAX, because volatilities differ
substantially. Cross-asset, the same percentage stop is inconsistent
risk. Modern alternatives: volatility-scaled stops (1 ATR rather
than fixed 3%), trailing stops, multi-stage exits. **Flagged for
Week 8 review.** Don't change in Phase 1 (consistency for the
experiment). Week 8 phase-review includes a sensitivity analysis on
stop/target methodology — was the 3:5 ratio actually right, or was
something else?

**B3. Maximum 5 concurrent positions.** Cap exists to bound
concurrent exposure. Hides a question about asset-level
concentration: if 5 strategies fire on BTC during a BTC sell-off,
you have 5 positions on the same asset taking the same loss. The
position cap doesn't address this. **Kept with note: the 5-
concurrent cap is fine; an additional rule like "max 2 positions
per asset" or "max 60% of exposure on any single asset" would close
the concentration gap. Worth flagging for Week 2 if not before.**

### Cluster C — Comparison and promotion

**C1. A/B comparison with 100+ trade minimum.** Right order of
magnitude. Below ~30 trades, Sharpe and win-rate estimates are too
noisy. Above ~300, regime may have changed. 100 is a reasonable
middle. What's not specified: how the 100 trades are distributed.
100 trades concentrated in a 2-week sideways market tells you
nothing about how the variant performs in a trend. **Kept with
note: the trade-count threshold is fine; an additional regime-
coverage check ("did these 100 trades occur across at least one
regime change, or were they all in one regime?") would strengthen
it. Worth implementing in `compare.py` as a context flag rather
than a gate.**

**C2. Human-in-the-loop promotion (no auto-promotion).** Modern
filter strongly affirms. At retail size, auto-promotion's failure
mode is overfitting amplification — the tuner produces in-sample-
best variants, auto-promotion deploys them, they fail out-of-
sample, the tuner re-tunes on the failure, repeat. Human review
is the firebreak. **Kept clean.** One of the project's strongest
design choices.

### Cluster D — Cross-cutting

**D1. Survivorship-bias correction in literature reading.**
Implicit in demotion criterion 5. The operational form: when
reading any strategy claim, ask "what's the population of
strategies that were tried and didn't get published?" Most
strategy literature can't answer this, so the operational rule is
*discount confidence in any strategy claim from the canonical
literature by a substantial factor*. Not a methodology to adopt but
a stance to maintain. **Kept as stance, not as methodology.** No
artifact change; the explicit naming here makes the stance
auditable.

**D2. Backtest-data quality and look-ahead bias.** Easiest mistake
to make in backtesting and one of the hardest to detect. Standard
guard: never let the strategy see information that wouldn't have
been available at the time of the trade. For OHLCV bars, this means
using the *open* of bar N+1 as the entry price for a signal
generated on bar N's close, not bar N's close itself. Whether
`replay.py` correctly implements this is a code-level detail.
**Build-quality flag for Week 1.** The Week 1 prompt to Claude Code
needs to specify the look-ahead-bias guard explicitly.

### Audit summary

- **Kept clean:** A1, B1, C2.
- **Kept with note:** A2, A4, B3, C1.
- **Kept as stance:** D1.
- **Flagged for Week 8 review:** A3 (Sharpe), B2 (stops/targets).
- **Build-quality flag for Week 1:** D2 (look-ahead bias).

The audit surfaces two specific places where existing choices are
inheritances worth examining at Week 8: the Sharpe ratio as primary
metric, and the stop-loss/take-profit methodology. Phase 2 entry
happens on the existing inheritances even if they're flagged —
changing the metric mid-experiment would muddy the results. The
flagged items are deferred re-examinations, not Phase 1 changes.

The no-online-ML and no-LLM-as-oracle boundaries were deliberately
not re-audited; their reasoning is in explicit decision-log entries
and remains unchanged.

---

## What this synthesis is committing to

Across five clusters in Session 2, first-pass generation produced
24 strategy candidates; honest scrutiny kept 13 (six clean passes,
seven probational/with-caveats), with eleven demoted. Across four
clusters in Session 3, ten existing methodologies were audited;
three kept clean, four kept with notes, one kept as stance, two
flagged for Week 8 re-examination, and one flagged as a Week 1
build-quality concern.

The cluster distribution in Session 2 was itself a finding. Cluster
4 (imported-from-outside-the-canon principles) produced six clean
or probational passes and zero demotions. Clusters 1, 3, and 5
collectively produced two clean passes, six probational, and ten
demotions. The asymmetry is structural, not accidental.

**The implication: methodology imports survive the modern filter
much more reliably than strategy candidates do.** The textbook
canon massively underweights methodology because methodology was
institutional-only until 2023. The largest single category of
newly-accessible advantage at retail size is not novel strategies
but newly-accessible *ways of deciding and reviewing decisions*.

Session 3 reinforces this finding from a different angle: the
existing canonical methodologies (Sharpe, fixed-percentage stops)
are mostly *inheritances* — picked because they're standard, not
because they're best. The two flagged for Week 8 re-examination are
exactly the methodologies the canon never seriously challenged
because the canon's culture treats them as default. The same
underweighting that opens space for *imported* methodologies (cluster
4 of Session 2) also leaves *existing* methodologies under-examined.

This finding has direct bearing on the Week 2 strategy-roster
review. If methodology imports are where the modern filter elevates
most reliably, then the strategy-roster question — whether to
replace Bollinger and MA-crossover with criterion-1/3/5 candidates —
should weigh that asymmetry. The unfair advantage isn't *what is
traded*; it's *how the deciding and reviewing happens around the
trading*. A roster of textbook strategies operated under a 2026-
aware methodology stack may be a stronger Phase 1 design than a
roster of novel strategies operated under conventional discipline.
The Week 2 review is where this gets decided; this synthesis is
where the evidence for the framing is set.

---

## Falsifiable hypothesis (from the reframe entry)

By end of Week 2, this synthesis will produce either:

(a) a defensible justification for keeping Bollinger and MA-crossover
that names which modern-filter criteria they pass and which they
fail, or

(b) a defensible alternative roster with the same justification
structure.

If neither is achievable in two weeks, the LLM-as-epistemological-
backbone thesis is weaker than expected and Week 3 starts a
postmortem on the reframe itself, not on the strategies.

The Session 2 finding that methodology imports survive more
reliably than strategy candidates does *not* answer the falsifiable
hypothesis — it reframes the question the hypothesis is asking. The
Week 2 review still has to commit to either (a) or (b). The new
information is that whichever roster gets chosen, it operates under
the cluster-4 methodology stack regardless. That's a finding worth
carrying into the Week 2 decision.

---

## Open questions surfaced for Week 2

1. **The strategy-roster question itself.** Whether Bollinger and
   MA-crossover survive the modern filter or get replaced — and on
   what grounds — is the Week 2 deliverable. The synthesis surfaces
   13 candidates the roster could be drawn from; the Week 2 review
   selects from them.
2. **The methodology-vs-strategy weighting.** The Session 2 finding
   suggests the unfair advantage is mostly methodological. Should
   the strategy roster be deliberately conservative (textbook
   strategies under the cluster-4 methodology stack) on the
   reasoning that methodology is where the filter elevates most
   reliably? Or does that conservatism waste the willingness to be
   epistemologically aggressive that the reframe committed to?
3. **The "specific instance vs. class" question for 5A.** If 5A is
   adopted, does the Week 2 review pick a specific operator-
   discipline strategy instance, or hold 5A for v2?
4. **Calibration of the seeded methodologies.** 4B and 4E generate
   data that doesn't become useful until Phase 2 / v2. Does that
   change the Phase 1 effort allocation, or is the seeding worth
   the cost on its own?
5. **Asset-level concentration cap.** B3 surfaced the question of
   whether the 5-concurrent-positions cap should be paired with an
   asset-level concentration rule. Worth deciding in Week 2 or
   earlier — before the variant explosion in Week 3 makes it
   actively relevant.

---

## Open questions deferred to Week 8

1. **A3 — Sharpe alone or Sharpe + Sortino + Calmar?** Phase 1 runs
   on Sharpe as the primary metric for consistency; Week 8 review
   reports all three and the Phase 2 entry decision considers all
   three.
2. **B2 — 3:5 fixed stop/target methodology, or volatility-scaled?**
   Phase 1 runs on the existing fixed methodology; Week 8 review
   includes a sensitivity analysis on whether the 3:5 ratio was
   actually right, or whether something else would have produced
   better results.

---

## Build-quality flag for Week 1

**D2 — Look-ahead bias guard.** The Week 1 prompt to Claude Code
must specify that `replay.py` uses the open of bar N+1 as the entry
price for signals generated on bar N's close, not bar N's close
itself. Without this guard, backtest results will be optimistic by
the size of the typical close-to-open move, which over hundreds of
trades is substantial. This is a code-level detail not visible in
PROJECT.md and needs to be in the Week 1 prompt explicitly.
