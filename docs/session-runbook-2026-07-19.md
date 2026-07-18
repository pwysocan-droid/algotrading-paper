# Claude.ai session runbook — 2026-07-19

Eight runs, in order. Rules for every run: one FRESH chat per run
(except where noted), paste the prompt verbatim, do not volunteer our
internal conclusions before the session answers, bring the full
response back to Claude Code for scoring and integration.

Runs 1-2 feed decisions you are making tomorrow. Runs 3-5 need the
Project (its knowledge base). Runs 6-8 are fresh plain chats.

---

## Run 1 — Devil's advocate: the program kill criterion
**Where:** fresh plain chat. **Feeds:** your ratification of the
decision-log draft. **Note:** ratify only after reading its strongest
attack; if it finds a hole, bring the rewrite back before signing.

```
I run a systematic trading-research program (paper trading, small retail
scale). After measuring our backtest engine's detection power and the
predictability ceiling of our data, we drafted a pre-registered
program-level kill criterion:

"If (a) measured round-trip execution costs exceed 0.5% on BTC/ETH, AND
(b) a walk-forward ML ceiling study on our augmented feature set (price +
funding + order-book data) shows gross predictive edge below measured
costs at every horizon out to 2 weeks — then the research program stops
and the project archives."

Argue AGAINST ratifying this criterion as written. Attack it from every
angle: ways it could fire wrongly (killing a viable program), ways it
could fail to fire (letting a dead program run), ambiguities that will be
litigated later, measurement dependencies that make it circular, and
incentives it creates for whoever operates the pipeline. Then — only
after the strongest attack you can make — propose the minimal rewrite
that survives your own objections.
```

## Run 2 — Referee: the real-money cost experiment design
**Where:** fresh plain chat. **Feeds:** the pre-registration you sign
before any real order (waiting on Alpaca live approval). **Note:** its
design revisions get folded into measure_execution.py before the
pre-registration entry is finalized.

```
Review this experiment design before we run it. Goal: measure the true
round-trip execution cost of small crypto trades on one US brokerage
(assumed ~0.6%: 0.5% fees + spread + slippage), because every research
conclusion downstream depends on this number.

Design: ~50 tiny real-money round trips ($20-50 notional each), factorial
across: order type (market vs post-only limit) × symbol (BTC, ETH, SOL) ×
time-of-day (US day vs overnight) × volatility regime (calm vs elevated,
classified from realized 1h volatility). Each trade records quoted
mid-price at decision time, realized fill price, latency, and fees.
Budget: ~$15 total in fees, max $100 concurrent exposure.

Critique: is the factorial allocation optimal for estimating the MINIMUM
achievable cost (the quantity we actually care about) rather than the
average? Which cells deserve more replicates? What's missing from the
measurement record? What would a sequential/adaptive allocation buy over
a fixed design at n=50? And what could make the results misleading
(venue promotions, size-dependence, market impact at these sizes,
post-only rejection bias)? Concrete revisions only.
```

## Run 3 — Hostile referee (Project)
**Where:** fresh chat INSIDE the Project; ensure dead-ideas.json and one
reports/gauntlet-*.md are in project knowledge. **Feeds:** the defense
backlog — every attack we can't answer becomes queued work. **Note:**
the doctrine is explicitly on trial, not just the results.

```
You are a quantitative-methods referee reviewing this research program for
publication. Its headline claims: (a) 28 trading-strategy ideas falsified
against 2.5 years of 5-minute data under a realistic cost model; (b) 17
general failure lessons extracted; (c) short-horizon OHLCV data likely
holds no retail-scale edge after costs — now backed by a measured
predictability ceiling. The project's own documents, including its
philosophy and decision log, are part of the submission — attack the
doctrine, not just the results.

Your job is to REJECT the paper. List every way these conclusions could be
artifacts of the method rather than facts about the market: selection
effects, unverified causal stories in the post-mortems, statistical power
problems, data leakage, survivorship in the lesson registry, metric
choices, the feedback loop between the lesson registry and idea
generation. Rank your attacks by severity. For each, state the cheapest
additional analysis that would defend against it.
```

## Run 4 — Fragility ranking of the 28 epitaphs (Project)
**Where:** fresh chat inside the Project (needs dead-ideas.json).
**Feeds:** the retroactive-ablation worklist. **Note:** rounds from 005
onward get this automatically (blind second reader); this covers the
back catalog once.

```
The attached dead-ideas registry contains 28 post-mortems, each with a
verdict and a claimed mechanism of death. The verdicts (dead/alive) and
the mechanisms (WHY it died) are different claims with different evidence.

For each entry: score 0-100 how confident we should actually be that the
MECHANISM claim is correct, given only the evidence cited. Then output the
5 most fragile mechanism-claims, and for each, the single cheapest
re-analysis of already-collected data that would most change its score.
A wrong mechanism-lesson poisons every future idea round that engages it,
so fragility here matters more than the verdicts themselves.
```

## Run 5 — This week, this data (Project)
**Where:** fresh chat inside the Project. **Feeds:** the cheap-analysis
queue. **Note:** expect 2-3 gems in a list of 10; that's a good hit rate.

```
Constraint exercise: no new data sources, no new live arms, no
architecture changes. Using ONLY artifacts that already exist — 2.5 years
of 5-minute bars for 5 coins, 28 implemented strategy ideas with
trade-level backtest records for the recent rounds, a live paper-trade
table, a registry of failure lessons, a measured power-calibration table,
a measured predictability ceiling, and a decision log — list 10 analyses
runnable in under an hour each that could each plausibly change a
decision we'd make in the next month. For each: the exact question, the
exact artifact it uses, and which decision flips depending on the answer.
Rank by decision-impact per hour.
```

## Run 6 — Bayesian read of the gate-family evidence
**Where:** fresh plain chat. **Feeds:** whether round-006+ touches gates
again, and with what design. **Note:** the explicit skeptical-vs-
sympathetic prior split is the point — bring back both numbers.

```
A statistics question about sequential evidence. Across four rounds of
trading-strategy backtests (930 days, ~$200 positions, net-of-cost
returns, per-trade std ≈ 3%), a family of related "meta-gate" designs —
strategies that suppress entries based on the system's own recent
outcomes — produced:

- Round 1: gate variant A — best of its round: n=460 trades, mean
  −0.65% per trade, 43.3% win rate (its underlying entry signal alone
  was clearly worse).
- Round 2: gate variant B — only idea of its round positive on a 180-day
  subsample (n=35, +0.22%/trade), but negative over the full window
  (n=109, −0.75%/trade).
- Round 3: gate variant C — passed its pre-registered success bar:
  n=7, +1.75%/trade, 71% win. (We computed the false-pass rate of that
  bar at n=7 under pure noise: 21%.)
- Round 4: gate variant D (different gate inputs, stronger underlying
  engine): n=39, −0.75%/trade, 25.6% win — worst of its round.

The variants share the family concept but differ in gate inputs and
underlying engines. Give a principled hierarchical/Bayesian treatment:
what is a reasonable posterior probability that the FAMILY concept
("self-referential gating concentrates edge") has any real positive
effect, versus the pattern being selection artifacts (each round's
best-looking variant was gate-shaped partly by chance)? State your prior
choices explicitly and show how the conclusion changes under a skeptical
vs sympathetic prior. Then: what single next experiment would most
efficiently update this posterior?
```

## Run 7 — SRE review of the automation
**Where:** fresh plain chat. **Feeds:** the ops-hardening queue.
**Note:** we've bug-audited the code internally; this is the OPS layer
(disk, credentials, spend, decay) which nobody fresh has seen.

```
Review the reliability design of a small automated research system and
list its most likely failure modes in order of expected damage. Setup:
one Linux VPS runs cron jobs: every 5 min (fetch market data, run
scripts, commit + push to a git repo); nightly (analysis reports +
an email digest via SMTP); twice daily (long-running backtest jobs);
twice daily (a coding-assistant CLI implements queued code changes from
spec files, runs the test suite, commits and pushes only if green);
monthly (report-generation jobs). Guards that exist: per-job flock
locks, git pull-rebase with retry on push, a health check that puts
warnings in the daily email when the newest pipeline artifact is >3 days
old or the latest job logged a failure, an "email absent = system down"
convention, and a test suite (~370 tests) gating code commits.

What's missing? Think: disk exhaustion, git repo growth, credential
expiry, API rate limits and price changes, silent partial failures,
clock drift, dependency rot, the coding-assistant introducing subtle
regressions the tests don't catch, unbounded LLM API spend, and
recovery when the operator is away for two weeks. Rank by expected
damage × likelihood, and give the one-line mitigation for each.
```

## Run 8 — Design panel: trading ideas for the admissible territory
**Where:** fresh plain chat. **Feeds:** Claude Code converts the output
into a round-spec file; it then runs the STANDARD pipeline — blind
premortem, implementation, gauntlet, epitaphs. Outside ideas get no
special treatment; that is what makes their results trustworthy.
**Note:** this is the direct answer to "can claude.ai create a list of
trading ideas to test" — yes, and this prompt constrains it to the two
bands our measurements license, so none of its ideas are dead on
arrival.

```
Design task. Constraints, all hard: crypto spot, BTC and ETH only,
5-minute OHLCV bars plus funding-rate history as inputs, ~$200 positions,
max 5 concurrent, entries must be limit-order-friendly (price comes to
you; no chasing), holding periods of either ~24 hours or 2-8 weeks
(nothing in between — shorter horizons are measured to be unprofitable
after our ~0.6% round-trip costs, and our data cannot evaluate
in-between horizons), and every strategy must state a pre-registered
kill criterion reachable within a 930-day backtest (expected 100+
trades).

Propose 3 strategy designs for the 24-hour band and 2 for the 2-8 week
band. For each: the causal mechanism and why it isn't already arbitraged
at retail scale, the exact entry rule, exit parameters, expected trade
frequency with the arithmetic shown, and its kill criterion. Novelty
matters less than mechanism honesty and statistical decidability.
```

---

## After all eight

Bring every response back to Claude Code. Integration path per run:
1-2 → tomorrow's decision-log entries; 3-5 → queue + defense backlog;
6 → round-006 direction; 7 → ops hardening; 8 → external round file
through the standard pipeline. Anything that contradicts an existing
lesson or measurement gets flagged loudly, not absorbed quietly.
