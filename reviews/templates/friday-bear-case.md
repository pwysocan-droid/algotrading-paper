# Friday adversarial review — bear case prompt template

Cluster-4 methodology 4G from `week-0-synthesis.md`. Each Friday this
template is filled in with the week's data and sent to Claude; Claude's
response is committed as `reviews/YYYY-WW-friday.md`. The point is
*forced steelmanning*, not balanced review — the LLM is the bear case
on call.

Two failure modes this template exists to prevent:

1. **Aggression without rigor** — the surfacing is aggressive, the
   discipline check isn't run, the operator promotes too fast. Bear
   case here: "your data hasn't finished speaking; you're declaring
   victory on noise."
2. **Drift toward soft bear cases** — the bear case gets milder over
   weeks because the LLM is unconsciously rewarding the operator. The
   template explicitly compares this week's case to the prior week's
   and flags milder framings as a signal.

---

## How to use

Replace the `{{...}}` placeholders with the week's data. Send the
filled template to `ClaudeClient.complete(prompt, called_from="friday_bear_case")`.
Save the response verbatim as `reviews/{YYYY-WW}-friday.md`. Do not
edit Claude's reply — the unedited form is the artifact.

Inputs to gather before the session:

- `WEEK_NUMBER`: ISO-week number, e.g. `18`
- `WEEK_RANGE`: e.g. `2026-04-26 → 2026-05-02`
- `TRADE_HISTORY_TABLE`: pasted result of:
  `SELECT variant_name, symbol, side, entry_price, exit_price,
   exit_reason, pnl_usd, pnl_pct, entry_time, exit_time
   FROM trades WHERE entry_time >= ? ORDER BY entry_time DESC`
- `RUNS_LOG_SUMMARY`: pasted result of:
  `SELECT status, COUNT(*) FROM runs WHERE started_at >= ? GROUP BY status`
- `DECISIONS_TABLE`: pasted result of:
  `SELECT action, COUNT(*) FROM decisions WHERE decided_at >= ? GROUP BY action`
  plus the most recent rejection reasons (top 5 unique).
- `PROMOTIONS_THIS_WEEK`: variant names promoted this week, with
  the `decision-log.md` entry hash linking the justification.
- `PRIOR_BEAR_CASE`: the body of last Friday's review file
  (`reviews/{YYYY-WW-1}-friday.md`), or the literal string
  `none — first Friday review` if Week 1.

---

## The prompt

```
You are running the Friday adversarial review for week {{WEEK_NUMBER}}
of the algotrading-paper project. Argue the strongest possible bear
case against this week's results. Forced steelmanning: assume every
strategy is overfit, every promotion was lucky, every data source is
noise, every A/B significance hit is spurious until proven otherwise.

Do NOT hedge. Do NOT include "well, on the other hand" framings. Do
NOT soften the case to be polite. The user has explicitly asked for
the bear case. Other Claude conversations cover the bull case.

The four mandatory sections to produce, in this order. Each section
is required even when nothing fits — say "no rebuttable claim this
week" rather than skipping the section.

## 1. The trade history bear case

Pasted trade history for week {{WEEK_NUMBER}} ({{WEEK_RANGE}}):

{{TRADE_HISTORY_TABLE}}

For each variant with at least one trade: identify the single weakest
signal in the data. Examples to look for: wins concentrated in 1–2
symbols (variant works on BTC, fails on everything else); short hold
times paired with small per-trade P&L (you're collecting the spread
and calling it a strategy); win rate above 60% over fewer than 30
trades (small-sample confidence trap); 70%+ of P&L in the most recent
3 trading days (recency bias dressed up as edge).

If a variant has fewer than 30 trades: state explicitly that any
performance claim about it is statistically unreliable, and that the
correct response is "wait for more data" not "this is working."

## 2. The promotion bear case

Promotions this week: {{PROMOTIONS_THIS_WEEK}}

For each promoted variant, argue that the promotion was premature.
Specifically check for: the playbook §2 too-good-to-be-true signatures
(parameter at the edge of the tested range, performance concentrated
in a small number of large wins, win rate skewing in the most recent
days vs. the rest of the 30-day window, parameters with no obvious
connection to the strategy's theoretical sweet spot). If any of these
fits, say so directly: "promotion of {variant_name} matches signature
X — recommend reverse-promote and continue on the predecessor."

If no promotions happened this week: state that the absence of
promotions is itself a signal — either the tuner is producing nothing
worth promoting (in which case the tuner needs investigation), or the
operator is being too cautious (in which case the discipline of
human-in-the-loop is becoming a refusal to act).

## 3. The runs / decisions bear case

Runs status: {{RUNS_LOG_SUMMARY}}
Decisions breakdown: {{DECISIONS_TABLE}}

Bear case on the infrastructure: any failed runs in the period are a
data hole. The replay tool's results are conditional on bars existing
for the period; if 5% of expected runs failed, 5% of the period has
no data and the trades-or-no-trades observation for that window is
meaningless. State the percentage of failed runs and the implication.

If the rejected:placed ratio for decisions is below 5% (almost every
signal placed): the position-limit checks are not actually constraining
anything, which means either the strategies don't fire often or the
limits are too loose. Argue that the constraint that doesn't constrain
isn't a constraint — it's vestigial.

If the rejected:placed ratio is above 50% (more than half of signals
rejected): the strategies are firing but execution is starving them.
Argue that the system is producing signals it can't act on, which
means the cooldown / concurrent-position cap may need recalibration —
or the strategies are over-firing and the parameter set needs review.

## 4. The drift check

Last week's bear case (the prior {{WEEK_NUMBER - 1}} review):

{{PRIOR_BEAR_CASE}}

Compare this week's case (sections 1–3 above, that you just produced)
to last week's. Specifically:

- Are this week's claims weaker / more hedged than last week's? If
  yes, name the specific claim that softened, and warn that
  bear-case drift is the documented failure mode of this methodology.
- Are this week's concerns the same concerns as last week's? If yes,
  ask whether anything was actually done about last week's concerns —
  unaddressed bear cases that recur are not "ongoing risk" but
  "dismissed signal."
- Did anything that last week flagged as "should not be promoted"
  get promoted anyway this week? If yes, name it and ask whether the
  bear case was actually rebutted with new data, or just outvoted by
  enthusiasm.

If this is the first Friday review (no prior week), say so explicitly
and use this section to lay the baseline: which of this week's bear
points the operator should expect to revisit next week.

---

End your response with one sentence in the form:

> If the project does X this coming week, the bear case will weaken.
> If the project does Y, the bear case will strengthen.

Be specific. "Run more variants" is not specific. "Promote a
walk-forward variant whose backtest P&L exceeds the live variant's
by less than 20% over fewer than 100 trades" is specific.
```

---

## Operator notes (do not include in the prompt to Claude)

- Save Claude's reply unedited as `reviews/{YYYY-WW}-friday.md`. The
  raw form is the artifact; editing for tone defeats the methodology.
- If Claude produces hedged language or refuses to argue the bear
  case (e.g., "I can't make negative claims about your strategies"),
  the prompt is not strong enough or the LLM is misinterpreting the
  task. Adjust the prompt for next week, log the incident in
  `decision-log.md` under "methodology adjustments."
- The Friday review is *not* the place to decide promotions. It's
  the place to surface what the data is saying that the operator
  doesn't want to hear. Promotions go through playbook §4.
- This template was committed in Week 1 with no real trade data yet.
  The first actual review (Week 1) will have a near-empty trade
  history and the bear case will largely be about the infrastructure
  and the absence of strategies. That's appropriate; the methodology
  starts as soon as the system runs, not when the system has results.
