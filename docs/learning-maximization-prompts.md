# Prompt pack — eliciting "more ways in" from the claude.ai Project

Purpose: extract genuinely NEW ideas for maximizing learning quality
and volume from a Claude that hasn't been anchored by our internal
discussion. Method matters as much as prompts:

**Rules of engagement**
1. Do NOT show any session our existing improvement list until the
   end — anchoring kills novelty. Blind first, critique second.
2. Harvest: anything new goes to build_queue.md; anything that
   duplicates our list is independent confirmation (also useful).

**Context tiers — the seed docs are themselves an anchor.** The
Project's corpus (philosophy.md etc.) encodes founding doctrine
(no-ML, capital model, falsification culture); ideas generated inside
it stay inside it. Run each framing at the LOWEST tier it tolerates:

- **Tier 0 — outside the Project, domain-disguised.** No docs. Abstract
  restatement only: "a lab runs ~5 expensive experiments/day against a
  fixed historical dataset plus one slow live stream; most experiments
  fail; lessons feed the next batch; maximize learning per week." Not
  even the word 'trading'. → Framings 1 (rival) and 4 (imports).
- **Tier 1 — fresh chat, facts without doctrine.** Paste mechanics
  only (capital model, costs, cadence, what's been tried); omit
  philosophy.md and the locked-architecture list and SAY you've
  omitted the commitments: "propose freely, we filter." → Framing 5
  (bits per experiment).
- **Tier 2 — inside the Project, full corpus.** Needed where the data
  is the point. Tell the referee that philosophy.md is on trial too:
  attack the doctrine documents, not just the results. → Framings 2,
  3, 6.

---

## Framing 1 — Design the rival (inversion)

> A competing team with the same budget ($100/mo VPS, ~$50/mo LLM
> spend, one part-time human, same 5 crypto pairs, same 2.5 years of
> 5-minute bars) claims their research machine learns 10x more per
> week than ours. Assume they're right. Reverse-engineer their
> pipeline: what are they doing that we are not? Be concrete —
> describe their daily loop stage by stage, then rank the differences
> by how much of the 10x each explains.

Attach: the project brief (already in knowledge).
Expect: pipeline-architecture ideas we haven't considered — batching,
triage funnels, surrogate pre-screens, different allocation of live
vs backtest attention.

## Framing 2 — The hostile referee (methodology audit)

> You are a quantitative-methods referee reviewing this project for
> publication. Its headline claims: (a) 28 strategy ideas falsified;
> (b) 16 general lessons extracted; (c) 5-min OHLCV alone likely has
> no retail-scale edge after costs. Your job is to REJECT the paper:
> list every way these conclusions could be artifacts of the method
> rather than facts about the market — selection effects, unverified
> causal stories, power problems, leakage, survivor logic, metric
> choices. Rank your attacks by severity. For each, state the cheapest
> additional analysis that would defend against it.

Attach: dead-ideas.json + one full gauntlet report.
Expect: every successful attack IS a learning-quality upgrade —
the defenses are our to-do list.

## Framing 3 — Fragility ranking (counterfactual historian)

> Here are all 28 post-mortems, each with a verdict and a claimed
> mechanism of death. For each: how confident should we actually be,
> on 0-100, that the MECHANISM claim (not the verdict) is correct?
> What single cheap re-analysis of already-collected data would most
> change that confidence? Output: the 5 most fragile epitaphs and
> their tests. A wrong mechanism-lesson poisons every future round
> that engages it.

Attach: dead-ideas.json.
Expect: a concrete ablation/re-analysis backlog, prioritized by how
load-bearing each lesson is.

## Framing 4 — Import from fields that industrialized learning

> Fields that turned expensive trial-and-error into industrial
> learning: drug discovery (funnel design, high-throughput screens),
> large-scale A/B platforms (sequential testing, variance reduction,
> overlapping experiments), evolutionary computation (population
> methods, fitness shaping), active learning / Bayesian optimal
> experiment design (query by expected information gain), and
> aviation safety (incident analysis without blame). For THREE of
> these, name the single most transferable practice and translate it
> into a concrete modification of our loop — file-level, not vibes.

Attach: brief only.
Expect: structural imports — e.g. bandit allocation of gauntlet
compute, surrogate scoring before full backtests, pooled incident
(trade) databases, information-gain-ranked idea queues.

## Framing 5 — Bits per experiment (information audit)

> Treat every activity in our pipeline as a measurement channel with
> a cost and an information yield: a 930-day gauntlet run, a live A/B
> trade, a premise check, an epitaph, a synthesis round, a Friday
> review. Estimate (order-of-magnitude) the information gained per
> unit cost for each channel about the question we actually care
> about: "does any implementable strategy beat costs?" Which channel
> is most under-used relative to its yield? Which is saturated?
> What NEW channel — something we don't measure at all today — would
> have the highest yield per dollar?

Attach: brief + a digest email.
Expect: reallocation arguments and possibly a genuinely new channel
(cross-idea pooling, market-condition conditioning, external data).

## Framing 6 — This week, this data (constraint-forced creativity)

> Constraint: no new data sources, no new live arms, no architecture
> changes. Using ONLY artifacts that already exist (2.5y bars, 28
> idea implementations, their gauntlet aggregates, the live trade
> table, decision log), list 10 analyses runnable in under an hour
> each that could each plausibly change a decision we'd make next
> month. For each: the exact question, the exact artifact, and what
> answer would change what decision.

Attach: dead-ideas.json + gauntlet reports + digest.
Expect: cheap re-mining of sunk-cost data; usually surfaces 2-3
things nobody thought to ask.

---

## Closing move (after all framings)

Paste our own improvement list (shadow arms, ablation verification,
trade-level persistence, both fill models, decidability gate,
pre-mortem critic) and ask:

> Here is what we came up with internally. Critique it: what's
> redundant with what you proposed, what did we miss that you rate
> higher, and what in our list is likely to produce LESS learning
> than we expect (and why)?

The disagreements are the highest-value output of the whole exercise.
