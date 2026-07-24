# Field Notes — building an honest empirical-search machine

A transferable retrospective. This project searched two financial markets
for a tradeable edge and (so far) found none that survives costs — but the
*method* and the *meta-lessons* generalize to any domain that runs many
expensive, mostly-failing experiments against limited data: drug
discovery, ML research, A/B platforms, materials science, quant finance.
If you are building a machine to search for a real effect in noisy data,
these are the things we learned the expensive way, so you don't have to.

**The headline result is itself the most transferable lesson:** after ~40
falsifications across two markets, every horizon, single factors and
combinations, we found no clean edge — and that is a *genuine, defensible
result*, not a failure, because we built the instrument to know the
difference between "we haven't found it" and "it isn't here." Most search
projects can't tell those apart, so they search forever. The product of a
good search machine is often the *credible negative* plus the instrument
that produced it.

---

## Part I — Transferable METHOD (disciplines to steal wholesale)

1. **Measure your instrument's power before trusting its verdicts.**
   Before believing any "X failed," plant a *known* signal of realistic
   size and confirm the pipeline recovers it; run it on shuffled/null data
   and confirm it finds nothing. We discovered our pass-threshold had a
   21% false-pass rate at small samples and near-zero power below a
   certain effect size — meaning many "failures" were coin flips. A
   telescope you've never pointed at a known star tells you nothing when
   it sees black.

2. **Measure the ceiling of your input space.** Run a flexible model with
   full hindsight over your features; if *it* can't extract signal, no
   hand-crafted rule from the same inputs will. This converts "we keep
   failing" into "we measured that the edge isn't in this input space" —
   a bounded, honest claim. Crucially, the ceiling is a property of the
   *data/structure*, not the world; it tells you when to change the space
   rather than tune within it.

3. **Every causal claim needs a control arm.** We audited our own failure
   write-ups and found the most load-bearing ones were *comparative*
   claims ("X carries information," "Y selects losers") where only one
   arm was ever measured. Requiring the control (a placebo, an ablation,
   a matched baseline) overturned one "dead" conclusion entirely. Verbal
   autopsy is not autopsy: "died of miasma" was accepted for centuries
   until someone put a slide under a microscope.

4. **The yardstick must match the thesis.** We measured the *same* signal
   three ways and got a kill, a null, and a strong pass — the difference
   was purely the exit/scoring rule. A reversion thesis scored with a
   continuation-rewarding metric looks dead; a risk-reduction factor
   scored by raw return looks dead. Before concluding an effect is absent,
   confirm you measured it with the instrument its mechanism implies.

5. **Compare to the right null, never to zero.** In a rising market,
   *everything* makes money; the honest benchmark is the drift/market
   null, not zero. Half of an apparent "edge" was often just the base
   rate of the asset going up. Any positive must beat the null a naive
   observer would already capture for free.

6. **Correct for multiple testing, and account for adaptive reuse.** The
   best of N noisy candidates looks good by construction (expected best-of-N
   ≈ √(2 ln N) standard deviations up). Apply the haircut. And remember
   that conditioning each round on the last round's results *on the same
   data* is adaptive data-mining — it inflates confidence in both
   directions and silently spends your dataset's statistical budget.

7. **Small samples make no claim, regardless of sign.** Our single most
   protective rule: below a fixed sample threshold, a result is quarantined
   — not a win, not a loss. Every near-miss that later evaporated was a
   small-sample glow someone wanted to believe.

8. **Pre-register kill criteria — and be willing to let the null win.**
   Write down, before the experiment, the number that would falsify the
   idea (and the *program*). The discipline that makes a search machine
   trustworthy is its willingness to stop. Guard hardest against mistaking
   "we can keep generating configurations" for "the edge is still hiding."

---

## Part II — Transferable META-LESSONS (the epistemics)

- **Fresh, unanchored eyes find what the project's own context cannot.**
  Our highest-leverage day came from handing the current state, blind, to
  fresh reasoning contexts (some domain-disguised) and asking them to
  attack it. Accumulated context becomes doctrine, and doctrine anchors;
  a fresh context re-derives from evidence. We institutionalized this as a
  standing pipeline stage, not a one-off. If you build an autonomous
  learner, give it a blind adversary on a schedule.

- **"Marginal signals exist" and "a tradeable edge exists" are different
  claims.** We repeatedly found real, directionally-correct, small effects
  — none survived the conjunction of costs + power + multiple-testing.
  That is the *expected* result at the boundary of an efficient system:
  real structure, too small to exploit. Don't confuse the two, and don't
  let the existence of the former imply the latter.

- **The denominator (cost) is as important as the numerator (signal), and
  it's usually assumed rather than measured.** Every verdict sat on top of
  a cost figure we hadn't measured. Costs are also *state-dependent* —
  worst exactly when the interesting events fire — so a flat cost model
  flatters event-driven strategies. Measure the denominator empirically.

- **Base-rate/frequency predictions from generative models are wildly
  miscalibrated** (we saw misses of 10× to 2000×). Before spending an
  expensive test, cheaply check the premise against the actual data
  distribution — a five-minute histogram kills a bad idea before a
  full experiment does.

- **Regime is often the hidden variable.** An effect that is real for
  years can invert. A result measured in one regime is not a fact about
  the system; condition on regime, and treat a single-regime finding as
  provisional until it survives another.

- **Distinguish parameter-tuning from structure-change.** When you hit a
  measured ceiling, tuning parameters inside the same structure can't
  escape it. The escape is a *different structure* or a *different input
  space* — a small number of decisive pivots, each following measured
  evidence, not infinite iterations of a structure already proven empty.

---

## Part III — What we tried, and how each failed (case studies)

1. **Naive backtest with no costs/constraints** → showed fake profit.
   Fix: model fees, slippage, and portfolio constraints *first*. "Fix the
   backtest before you trust one number from it" was the turning point.

2. **Textbook & documented retail strategies** (indicators, breakouts,
   lead-lag) → all died to the cost floor. Real-but-tiny structure,
   net-negative. The "gross-positive trap": finding signal is easy; the
   question is why the remainder survives costs.

3. **Self-referential "gate" family** (condition entries on the system's
   own recent state) → best-of-round three rounds running, one small-sample
   "pass" (n=7) that a hierarchical meta-analysis later showed was almost
   certainly the top card of a small shuffled deck. Closed via a
   pre-registered family-level kill. Lesson: a lineage can survive on the
   memory of its last outlier; make it prove itself out-of-sample or retire it.

4. **Horizon and cost levers** (multi-day holds, maker fills) → improved
   the arithmetic, never crossed zero alone. Levers reshape the search
   space; they don't manufacture edge.

5. **Predictability-ceiling study** → measured that short-horizon price
   data holds no net edge for the rule class; longer horizons were
   real-for-a-while but regime-dependent. Converted a vague "nothing works"
   into a bounded, measured claim.

6. **Equity cross-sectional price factors** (momentum, low-vol, reversal,
   52-week-high), single → horizon-swept → combined → all null after a
   survivorship correction that cut the raw signal to noise. Momentum was
   the only right-signed factor and stayed sub-threshold at every horizon;
   combining factors *diluted* rather than helped (only one real signal to
   deploy). Low-vol delivered its *risk-reduction* thesis (0.7× benchmark
   vol) but not excess return — a construction tool, not alpha.

7. **Event-driven shock-fade** (the current lead) → a measured post-shock
   reversion that a mismatched exit "killed" and a matched exit revived
   (+3.7%/trade, regime-consistent), but at a sample below our own claim
   threshold and horizon-unstable. Filed as a *lead*, pursued via forward
   out-of-sample accumulation — not promoted.

The through-line: at every stage, the honest, bounded negative was more
valuable than the hopeful maybe — and the discipline that produced the
negative is what makes the eventual positive (if any) believable.

---

## Part IV — Operational lessons (for autonomous/unsupervised systems)

- **Silent corruption outranks loud downtime.** Liveness checks ("is it
  running?") are easy and insufficient; correctness checks ("is it right?")
  are what matter. A subtly wrong number can fire a program-level decision
  while every dashboard reads green. Add golden-output regression tests
  and data contracts (assert row counts, ranges, no gaps) that fail loudly.

- **Alarms must forgive recovered incidents.** An alarm that keeps ringing
  after the incident is fixed trains the operator to ignore all alarms.
  Judge only the most recent run.

- **A dead-man's switch needs an external heartbeat.** "No email = system
  down" fails exactly when the email channel fails; humans are bad at
  noticing absence. Use an active external watchdog.

- **Autonomy is a state machine over durable artifacts, not a
  conversation.** Each unattended run should derive what to do from
  committed state (idempotent, crash-safe), carrying nothing in memory.
  The compounding "knowledge" lives in a versioned registry of results,
  not in any agent's context.

- **Reproducibility discipline compounds.** Single-writer data ownership,
  pinned dependencies, a locked "architecture" list, and a decision log
  that records *why* (not just what) — these are what let a months-long
  autonomous project stay coherent and auditable.

---

## The one-line takeaways

- Build the machine to know the difference between "we haven't found it"
  and "it isn't here." That difference is the whole game.
- Measure your instrument (power, ceiling, cost) before trusting its
  verdicts.
- Every causal claim gets a control arm; every effect gets the yardstick
  its mechanism implies; every positive beats the right null.
- Small samples make no claim. Correct for selection. Pre-register the kill.
- Fresh blind eyes on a schedule; be willing to let the null win.
- The credible negative plus the instrument is a real product — often a
  better one than a fragile edge would have been.
