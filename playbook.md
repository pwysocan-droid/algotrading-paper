# Playbook — algotrading-paper

What to do when specific situations arise. Compiled in advance so the
response isn't being invented under stress.

The format: each play has a *trigger*, an *immediate action*, a
*follow-up*, and an *anti-pattern* (what NOT to do). When the trigger
fires, work the play. If the situation doesn't match an existing
play, write a new one *before* acting.

---

## 1. The drawdown play

**Trigger:** any variant's running 30-day P&L drops below -10% of its
allocated capital. Or the portfolio-level P&L drops below -15% of
total exposure ($150 in Phase 1 paper terms, $150 in Phase 2 real
terms).

**Immediate action:**
1. The variant continues running. Do NOT disable it on the spot.
2. Open a `decision-log.md` entry titled "Drawdown investigation —
   [variant name]" with the date.
3. Pull the trade history for the variant. Bucket the losses by:
   reason (was it stop-loss hits, time-exits at small loss, or
   spread eating profitable trades?), market regime (was it
   trending or chopping?), and symbol (concentrated in one asset
   or distributed?).

**Follow-up:**
- If the losses are concentrated in one regime that the strategy is
  known to fail in (Bollinger losing in a trend, MA-crossover
  losing in chop), this is the strategy doing exactly what it's
  documented to do. *Don't disable.* The losses are tuition for
  the regime detection that A/B comparison will eventually surface.
- If the losses are unexplained — distributed across regimes,
  concentrated in fee/spread costs, or showing up as systematic
  stop-losses being hit — investigate the *execution layer*. Often
  the problem isn't the strategy; it's that fees or slippage are
  larger than the strategy expected.
- Phase 2 only: if the portfolio-level drawdown exceeds 30% (-$300
  on $1,000), trigger the Phase 2 exit play (see §6).

**Anti-pattern:** disabling the variant immediately. Variant deaths
should be the result of A/B comparison over 100+ trades, not panic
after a bad week. The whole point of the registry is that variants
compete; killing one without comparison data is killing the
experiment, not the strategy.

---

## 2. The too-good-to-be-true play

**Trigger:** the walk-forward tuner produces a recommendation whose
backtested P&L exceeds the live variant's by >40%. Or a live variant
shows >5% per-trade win rates over a sample of <50 trades.

**Immediate action:**
1. Stop. Do NOT promote.
2. Open the recommendation (or the trade history) and check for the
   following overfitting signatures:
   - Parameter values at the edge of the tested range (e.g.,
     `period=99` when the grid was `[10, 20, 50, 99]` — it's
     cherry-picking the boundary)
   - Performance concentrated in a small number of large wins
     rather than distributed across many trades
   - The win rate in the most recent 7 days dramatically exceeds
     the win rate in the prior 23 days of the 30-day window
   - The recommendation's parameters look "weird" — odd numbers,
     unusual combinations, no obvious connection to the strategy's
     theoretical sweet spot

**Follow-up:**
- If any overfitting signature is present, mark the recommendation
  as `promoted=0` with a `decision-log.md` entry explaining what
  was suspicious and what was rejected.
- If no signatures are present and the recommendation still looks
  exceptional, run the replay on the 30 days *prior* to the
  tuner's window. If it's still exceptional, the recommendation
  may be legitimate.
- Even legitimate exceptional recommendations should run in the
  registry alongside the predecessor for at least 100 trades
  before any capital reallocation. There's no scenario where a
  variant earns trust on backtest alone.

**Anti-pattern:** promoting based on backtest performance alone.
Backtest performance is by construction in-sample; real performance
is out-of-sample. The walk-forward methodology mitigates this but
does not eliminate it.

---

## 3. The API breaking play

**Trigger:** Alpaca returns 5xx errors for >2 consecutive runs, OR
an external context source (CoinGecko, F&G, news RSS) is unreachable
for >24 hours.

**Immediate action — Alpaca:**
1. The execution layer halts new orders. Existing positions remain
   open with their stop-loss / take-profit triggers in place
   (those are server-side at Alpaca).
2. The data layer continues attempting to fetch. Each failed run
   is logged to `runs` with status='failed'.
3. If Alpaca is down >12 hours, manually verify open-position
   state on the Alpaca dashboard. The local trades table may be
   out of sync.

**Immediate action — context source:**
1. The variants that depend on the failing source continue
   running but their context-using logic falls back to "no signal
   from this source" (treat the source as silent, not as zero).
2. A `runs` row is logged noting which source failed.
3. After 24 hours of failure, that source's variants are
   automatically disabled until the source returns. The
   technical-only variants continue.

**Follow-up:**
- Investigate whether the failure is on our end (rate-limited,
  changed authentication) or theirs (API outage, scheduled
  maintenance).
- For Alpaca outages >24 hours: write a `decision-log.md` entry
  about whether to extend the Phase 1 calendar or accept the gap.
- For context-source outages >7 days: consider whether that source
  is reliable enough to keep in the system. A source that breaks
  often is worse than a source that doesn't exist.

**Anti-pattern:** having the variants silently produce signals
based on stale context data. Stale data is worse than no data
because the strategy thinks it's seeing fresh information.

---

## 4. The promotion-decision play

**Trigger:** a walk-forward recommendation has been waiting in the
`recommendations` table for review.

**Immediate action:**
1. Read the recommendation's backtest stats (P&L, Sharpe, max DD,
   n_trades). Check for the too-good-to-be-true signatures (§2).
2. Run `replay.py --variant=[proposed_name] --period=60d` to see
   how the recommendation would have performed on the 60 days
   prior to the tuner's 30-day window. Out-of-sample sanity check.
3. Read the live variant's recent performance. If the live variant
   is performing fine, the bar for replacing it is higher than if
   it's struggling.

**Follow-up — promote:**
1. Add the new variant to `STRATEGY_VARIANTS` with `enabled=True`.
2. **Do NOT disable the predecessor.** Both run in parallel.
3. Update the `recommendations` row: `promoted=1`, `promoted_at=
   [timestamp]`, `promoted_by_decision_log_entry=[entry-id]`.
4. Write the `decision-log.md` entry justifying the promotion in
   2-3 sentences.

**Follow-up — reject:**
1. Update the row: `promoted=0` with a reason in
   `decision-log.md`.
2. Note whether the rejection is due to overfitting concerns, due
   to the live variant performing fine, or due to the
   recommendation being marginal.

**Anti-pattern:** auto-promotion without review. The walk-forward
tuner's *purpose* is to surface candidates, not to make decisions.
The whole architecture assumes a human (or human-supervised LLM) in
the promotion loop.

---

## 5. The "I want to add a new strategy/source" play

**Trigger:** mid-Phase-1 enthusiasm to add something not in the
8-week curriculum (a new strategy family, a third external source
in the same week, equities, etc.).

**Immediate action:**
1. Stop. Re-read `philosophy.md` § "What this project is NOT."
2. Re-read `decision-log.md` for the entries on "one factor at a
   time" and "two textbook strategies."
3. Ask: is the proposed addition worth the loss of statistical
   clarity for the *current* week's experiment?
4. If the answer is genuinely yes, write a `decision-log.md` entry
   explaining what's being added, why it's worth the muddiness it
   introduces, and what the expected new conclusion is.

**Follow-up:**
- If the entry can be written cleanly with a falsifiable
  hypothesis, proceed.
- If the entry reads like rationalization, that's the signal not
  to do it. Hold the addition for v2.

**Anti-pattern:** adding the new thing first and writing the entry
later. The discipline is the writing-down, not the having-decided.
Most retail trading projects fail by accumulating undocumented
additions until they can no longer be reasoned about.

---

## 6. The Phase 2 exit play

**Trigger:** any of the three Phase 2 exit conditions has fired:
account below $700, real diverged from paper by >50% over 2 weeks,
or 8 real-money weeks elapsed.

**Immediate action:**
1. Halt the execution layer for the live account. The data,
   signal, and paper-execution layers continue.
2. Close all open real-money positions (market orders, accept the
   spread). Calculate final real-money P&L.
3. Open `phase2-postmortem.md` and start filling it in.

**Follow-up:**
- For the drawdown trigger: postmortem focuses on what failed
  (strategy, execution, fees, regime). Real money does not return
  to the live account in this experiment.
- For the variance trigger: postmortem focuses on the
  paper-vs-real gap. The most likely cause is fee/slippage
  modeling — paper underestimated the cost of real trades. Document
  the gap with specifics.
- For the time trigger: postmortem reviews 8 weeks of real-money
  performance. Three options to write up: continue (with
  justification), scale up (with justification), archive (with
  postmortem).

**Anti-pattern:** holding open positions hoping for a recovery.
The exit conditions are pre-committed for exactly the situation
where holding feels right. Hold a postmortem instead.

---

## 7. The "Claude is being too cautious" play

**Trigger:** the user (you) reads back what Claude (me) just
wrote and feels like the response is overly hedged, defensively
listing risks without taking a position, or otherwise unwilling
to make a recommendation.

**Immediate action:**
1. Tell me directly. "Be more decisive on this one" is sufficient.
2. If I'm being cautious for a *real* reason (the request actually
   crosses a safety boundary, or the answer genuinely is
   "depends"), I'll say so explicitly rather than continuing to
   hedge.
3. If I'm being cautious without a real reason — defensive
   reflexes overriding the brief in `philosophy.md` to push back
   on scope inflation, hold the gates, be honest about likely
   outcomes — call it out and I'll recalibrate.

**Anti-pattern:** accepting a hedged answer as the final word when
you needed a recommendation. The project depends on me being
willing to say "this is overfit, don't promote" or "you're about
to violate your own gate, stop." If I drift toward "well, you
could go either way," push back.
