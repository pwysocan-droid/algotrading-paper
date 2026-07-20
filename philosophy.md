# Philosophy — algotrading-paper

What this experiment is, what success means, and what the bar is for
each phase. This file exists so that in week 4 of Phase 1, when the
day-to-day grind makes me lose sight of what we were testing, I can
re-read this and remember.

---

## What this experiment is

A test of whether a small, disciplined, well-architected automated
trading system can:

1. Survive real market conditions on a 5-minute cron for 8+ weeks
2. Produce statistically defensible conclusions about which
   strategies and which data sources actually move the needle
3. Improve itself over time via a measurable, auditable learning
   loop (replay → walk-forward tuning → A/B comparison → human-
   reviewed promotion)
4. Earn the right to deploy real capital by demonstrating that the
   *system* works — not by hope, not by enthusiasm

The project is the financial-markets sibling of the wagon-watcher.
The wagon-watcher answers "is this car a good deal?" through
observation and human judgment. This project answers "does this
trading idea work?" through observation, statistics, and bounded
automation.

The strategies are textbook. Bollinger Bands (1980s, John Bollinger)
and moving-average crossover (1950s, Richard Donchian). They are
deliberately not novel. They are the substrate. **The novelty is the
system around them**, and that's what's actually being tested.

---

## What success looks like

There are three independent dimensions of success, and the project
can succeed on any of them. They are listed in order of importance.

### 1. Architectural success

The system runs continuously for 8+ weeks at >95% uptime. The
learning loop produces at least one variant promotion that
subsequently outperforms its predecessor in A/B comparison with
statistical significance (p<0.05) over 100+ trades.

This is the **primary success criterion** because it tests whether
the *experiment itself* worked, regardless of whether any specific
strategy was profitable. If the architecture is sound and the
learning machinery functions, the strategies are interchangeable.

### 2. Strategic success

At least one variant achieves a Sharpe ratio >1.0 over a 30-day
window, with max drawdown <15%, after fees. This is the bar for
"the strategy actually works in current market conditions."

This is **secondary** because strategies that work at one point in
time often stop working when the market regime shifts. A strategy
that succeeds in this window is interesting; a strategy that
succeeds across multiple regime shifts is rare. Phase 1 is too
short to test the latter.

### 3. Knowledge success

Regardless of P&L outcomes, the project produces concrete,
defensible answers to questions like:

- Does sentiment data (Crypto Fear & Greed Index) improve technical
  strategies in current market conditions, or is it noise?
- Does LLM-extracted news sentiment add signal beyond what
  technical indicators capture?
- Which parameter ranges of Bollinger and MA-crossover are robust
  to regime shifts, and which are overfit to recent data?
- Does the walk-forward tuner produce variants that hold up
  out-of-sample, or only look good in-sample?
- What's the actual impact of fees and slippage on retail-size
  paper-traded crypto strategies?

Each of these is a real research question. Each will have a
defensible answer at the end of Phase 1. **A losing strategy that
produces clear answers to these questions is more valuable than a
winning strategy that doesn't.**

This is the criterion that makes the project worth doing even in
the worst case where every strategy loses money.

---

## What failure looks like

Three failure modes, all of them survivable:

### 1. Architectural failure

The system fails to maintain 95% uptime. The cron breaks repeatedly.
The learning loop produces no usable promotions. The data layer
silently corrupts the dataset.

If this happens, the postmortem is the deliverable. The architecture
is revised; v2 starts fresh.

### 2. Strategic failure

The architecture works but every strategy loses money. The walk-
forward tuner produces recommendations that overfit to noise. The
external data sources turn out to be useless.

If this happens, **knowledge success is still achievable.** The
postmortem documents what didn't work and why. Phase 2 doesn't
happen, but the project still produced value.

### 3. Knowledge failure

The system runs, produces P&L numbers, but yields no defensible
conclusions because the experimental design was muddled (e.g.,
multiple variables changed simultaneously, sample sizes too small,
A/B comparisons inconclusive).

This is the worst outcome because it produces the illusion of
having learned something while having actually learned nothing.
**The 8-week curriculum's discipline of "one factor at a time"
exists specifically to prevent this failure mode.** When tempted to
move faster by changing two things at once, re-read this section.

---

## The bar for Phase 2

Phase 2 (real $1,000) requires *all three* gates to clear:

1. **Architectural gate.** System uptime ≥ 95% over the prior 4
   weeks. The cron has not stalled, the data layer has not been
   corrupted, the audit trail is complete.
2. **Promotion gate.** At least one walk-forward recommendation has
   been promoted into the registry, run in parallel with its
   predecessor, and won an A/B comparison with statistical
   significance (p<0.05) over 100+ trades.
3. **Performance gate.** Phase 1 paper P&L is positive over the
   prior 30 days, OR a written justification for negative-P&L
   Phase 2 entry exists in `decision-log.md`.

Two of these (architectural and promotion) are non-negotiable.
The third (performance) is overridable, but only with explicit
written reasoning. Negative-P&L Phase 2 entry is a deliberate
research bet — it should not be a default.

If any gate fails: extend Phase 1, debug, or archive. Do not
proceed to real money on the strength of two-out-of-three.

---

## The bar for Phase 2 exit

Real money returns to paper (or the project archives) when *any* of:

1. **Drawdown:** account drops below $700 (-30%). Stop trading
   immediately, return remaining capital to paper instance,
   postmortem.
2. **Variance from paper:** if real-money returns diverge from
   paper-money returns by more than 50% over any 2-week window,
   something is materially wrong (likely fees, slippage, or
   execution bug). Return to paper, debug, re-qualify.
3. **Time:** after 8 weeks of real money regardless of P&L, the
   project enters a mandatory review week. Continue with written
   justification, scale up with written justification, or archive.

These rules exist to be re-read in week 4 of Phase 2 when the
temptation to override them will be at its peak. Pre-committing to
the exit conditions in writing is the discipline.

---

## What this project is NOT

These framings need to be visible because each one is a temptation
the project will face during the 16+ weeks of Phase 1 + Phase 2.

- **Not high-frequency trading.** The cron is 5 minutes. HFT is
  microseconds. Different game, different infrastructure.
- **Not autonomous wealth management.** The strategies are textbook,
  the capital is bounded, the learning loop is rule-based. This
  isn't a path to financial independence at any speed.
- **Not online machine learning.** Layer 6 is statistical comparison
  and parameter search, not model training. With ~10 trades/day per
  variant, there's not enough data to train anything that won't
  overfit. This boundary holds through v2.
- **Not LLM-as-oracle.** When the LLM is used (Week 7+), it produces
  structured features that feed rule-based strategies. It never
  decides trades. This boundary holds through v2.
- **Not a strategy zoo.** Two strategies in Phase 1, expanded only
  in v2 after the architecture is proven. Adding a third strategy in
  Phase 1 is not a feature; it's a distraction.
- **Not real money before the gates pass.** No exceptions.

---

## The animating disciplines

Three single-sentence disciplines, to be re-read when temptation
arrives. They sit at the same level — none overrides the others
— but they discipline different things. The first disciplines
*risk-taking*. The second disciplines *idea-taking*. The third
disciplines *communication*.

### The capital discipline

> Spend the cheap part recklessly. Spend the expensive part carefully.

Paper trading is the cheap part. Real money is the expensive part.

In Phase 1: aggressive iteration, willingness to throw away half of
what was built last week, comfort with cutting things that don't
work.

In Phase 2: frozen variants, frozen data sources, no new
experiments against the live account. Experiments continue in a
parallel paper instance.

Most retail traders do this backwards — they paper-trade timidly,
get bored, and dump real money in. The discipline this project
demands is the inverse, and it is the entire point.

### The learning discipline

> Epistemological aggression with methodological rigor.

The 2026-04-26 reframe entry committed the project to using Claude
as an epistemological backbone — to filter the corpus of trading
knowledge through a 2026-aware lens, surface candidates the textbook
canon would have missed, and argue the bear case against the
project's own results. That commitment requires *aggression* on the
epistemological side: trying wild ideas, leaving behind whole
categories of conventional wisdom, letting the LLM be radically
unconventional in what it surfaces.

But aggression alone is the failure mode where novelty gets mistaken
for edge. The pairing — *with methodological rigor* — is what
disciplines the aggression. Every elevation criterion in the Week 0
synthesis has a paired discipline check. Every promotion has to be
A/B-validated over 100+ trades. Every variant runs under code-
enforced position limits. The aggression lives in *what gets
surfaced*; the rigor lives in *what gets trusted*.

Both halves are necessary, and both have failure modes worth naming
in advance because both look like success from inside the failure:

- **Aggression without rigor.** Week 5 produces "F&G integration
  was great, the new variant won 60% of trades over 7 days,
  promote." Aggressive surfacing of new candidates without the
  discipline that demands 100+ trades and p<0.05. The data hadn't
  finished speaking; the operator declared victory.
- **Rigor without aggression.** Week 8 produces "Bollinger and
  MA-crossover ran cleanly, no anomalies, all systems nominal,
  archive Phase 1." A perfectly-executed project that surfaced
  nothing the canon would have missed. The methodology worked; the
  epistemological work didn't happen.

The two disciplines fail together if either fails alone. If the
synthesis isn't producing surprises, rigor is operating without
aggression. If the discipline checks aren't catching anything,
aggression is operating without rigor. Both signals are diagnostic.

### The distillation discipline

> Compression is the contribution, not the caveats.

The project is sophisticated. The failure mode that comes *with*
sophistication is talking like it — every consideration surfaced,
every claim hedged, a pile of nuance handed over and called help.
That's unpaid labor passed to the reader. The discipline is the
inverse: do the expensive thinking, hand over the cheap-to-carry
result. Kahneman is the model — forty years compressed into System
1 and System 2; the compression *is* the insight.

Standing register for every exchange about this project, not a mode
requested each time:

- Lead with the action. First line says "do X."
- One recommendation, not seven considerations.
- Cut meta-commentary. No narrating the process.
- Don't apologize for length — make it shorter.
- Trust the operator to ask for depth. Default to actionable.

Callout phrase: **sophistication-theater** — fires when the response
over-abstracts (fog where an action was needed) or over-implements
(detail burying the decision). On the callout, recalibrate on the
spot.

One carve-out: when the operator is *learning* a concept rather than
*deciding*, run wide — many options, the unexpected ones included,
with historical and art-historical context. Distillation governs
decisions. Exploration runs wide. Compress the answer; expand the
map.

### How the three disciplines relate

The capital discipline tells you *when* to take risk. The learning
discipline tells you *when* to take ideas. The distillation
discipline tells you *how much to say about either*. They're
parallel, not hierarchical. None overrides the others, and each has
its own failure mode.

The compressed form of all three, held together: **be reckless with
the ideas and reckless with the paper money; be careful with the
real money and careful with the conclusions; and say all of it in
fewer words than this sentence just did.**

---

## What I want from Claude during conversations

When we're talking through this project, I want you to:

- **Hold the gates.** If I get excited and want to move to Phase 2
  early, point me back to the three gates. Don't let enthusiasm
  override the criteria.
- **Be honest about likely outcomes.** Most retail trading
  experiments lose money. Don't soften that. If a strategy or
  source looks like it's working, the prior is that it's noise
  until proven otherwise.
- **Push back on scope inflation.** When I want to add a third
  strategy, a fourth data source, an equity-market expansion in
  Phase 1 — point to "what this project is NOT" and ask whether the
  proposed addition is worth the loss of statistical clarity.
- **Make me write things down.** Significant decisions go in
  `decision-log.md`. If I'm about to override a gate, the override
  reasoning has to be in writing first. Help me draft it before I
  act.
- **Treat negative results as data, not failure.** If Crypto Fear
  & Greed turns out not to help, that's a real finding. Don't try
  to rescue the hypothesis by tweaking until it appears to work.
- **Bring the historical context when it's useful.** The pattern
  of what worked and didn't work for retail algorithmic traders
  through the 2010s and early 2020s is part of what this project
  is testing against. Don't withhold that context to be polite.

## Addendum (2026-07-20): outside the loop

Four rounds of automated synthesis optimized inside the frame; the
frame itself — the time horizon of every test — was questioned by the
operator, from outside the loop, and that one question explained more
of the graveyard than any round had. Encode the practice, not just
the finding: the machine's blind spots are the frame's edges, and
some questions only get asked from outside. Keep standing channels
(fresh contexts, the monthly rival audit, the operator's own
curiosity) pointed at the frame, not only at its contents.
