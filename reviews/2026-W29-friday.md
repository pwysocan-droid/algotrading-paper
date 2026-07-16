# Friday adversarial review — 2026-W29

algotrading-paper / friday bear-case · 4G methodology
Week under review: **2026-07-09 → 2026-07-16**

---

## The bear case, in one paragraph

Eleven weeks past the first review, the numbers are identical to Week 1: zero trades, zero decisions, zero live execution. The prior review set a floor and named the exact terminal condition — "if next Friday arrives with `trades` still at 0, the bear case strengthens to: the experiment was never going to start, and the infrastructure was the project." Eight Fridays later, `trades` is still 0. That prediction has come due, and it resolved against the project.

---

## 1. The trade history bear case

Zero rows. No variant has a single trade.

No rebuttable claim this week — there is no data to attack because there is no data.

The sharper point: the entire apparatus of Section 1 — win-rate traps, symbol concentration, recency bias — is a *luxury* the project has not earned. Those are the failure modes of a system that is trading. This project has not reached the point where its results could even be wrong. There is nothing here to steelman as overfit, because nothing has been fit.

## 2. The promotion bear case

No promotions — "no promotion machinery has run yet."

Per the template: the absence of promotions is a signal. But the standard framing (tuner too quiet vs. operator too cautious) does not apply, because there is no tuner output *and no live baseline to promote from*. This is worse than either documented failure mode. The promotion machinery has never run because there is nothing upstream to feed it: no registered variant trading, no 30-day window, no predecessor.

This is not human-in-the-loop discipline. It is a control system with no plant attached. The "caution" is not a choice being exercised — it is the absence of anything to be cautious about.

## 3. The runs / decisions bear case

Runs status: **ok: 2016, failed: 0**. Zero failed runs. No data hole. The substrate is, again, excellent.

Decisions: **the execution layer has never run live.** The rejected:placed ratio is undefined because both numerator and denominator are zero.

The template's dichotomy — constraint below 5% is vestigial, above 50% is starvation — cannot be evaluated. But undefined is the most damning value of all. A vestigial constraint is at least attached to a system that fires. A starving constraint at least implies signals exist. Here the position-limit checks, the cooldown logic, the concurrent-position cap — all of it — is untested code guarding a door no one has walked through. 2016 clean runs producing zero decisions means the runs are executing a pipeline that terminates before it reaches the only stage that matters.

**2016 successful runs, 0 decisions. The infrastructure is running perfectly at doing nothing.**

## 4. The drift check

This is **not** the first review — there is a prior baseline, and the comparison is the whole point this week.

**Are this week's claims weaker than last week's?** No — and that is the finding. The claims are *identical*. Week 1's core attack vector ("the week bought no movement on the only question that matters — signals=0, trades=0, decisions=0, Day 7 of 56") is verbatim reproducible for Week 29. The bear case did not soften. It calcified.

**Are these the same concerns as last week's?** Yes, all of them. And per the template's own rule: *unaddressed bear cases that recur are not "ongoing risk" but "dismissed signal."* Walk the Week 1 punch list:

1. "Register a strategy or admit the curriculum is paused" — **still zero trades.** Not done, or done and not trading.
2. "Run the adversarial review weekly, on time" — reviews W21→W29 exist, so the discipline held. This is the *one* thing that worked. It is also the least important one, because a perfectly-run weekly review of a project that never trades is the drift-detection apparatus successfully documenting a corpse.
3. "Log the backbone or stop claiming it" — unmeasurable from here; this review is again drafted in Claude Code, again not in `llm_calls`.
4–6. Hygiene items — no evidence of closure surfaced.

**Did anything flagged "should not be promoted" get promoted anyway?** No — nothing can be promoted, so this check is inert. But note the shape: the promotion machinery hasn't run, so the review cannot even catch a bad promotion. The methodology is running clean over an empty substrate.

**The terminal prediction resolved.** Week 1 stated the falsifiable fork explicitly:

> "If next Friday arrives with `trades` still at 0 and no 2026-05-29 review written, the bear case strengthens to: the experiment was never going to start, and the infrastructure was the project."

The reviews *were* written — so the methodology survived. But `trades` is still 0, thirty-two Fridays' worth of them. The half of the prediction that measured the actual experiment came true. The reviews accumulated; the trades did not. The methodology has become the deliverable. **The experiment was the infrastructure, and the review cadence is now infrastructure too — a second respectable process that runs reliably while the trade count stays at zero.**

The most dangerous drift this week is not that the bear case softened — it's that running this review at all has become the substitute for the thing it was supposed to force. Week 1 warned that infrastructure is "the most respectable way to avoid the scary work." The adversarial review is now that infrastructure.

---

> If the project logs a single live paper trade — one row in the trade history with a real fill from paper-api.alpaca.markets — before next Friday, the bear case weakens materially for the first time in 29 weeks. If next Friday's review is again written cleanly over `trades: 0`, the bear case strengthens to its terminal form: the project is now two nested infrastructures (the trading substrate and the review cadence) that both run flawlessly at producing nothing, and the correct action is to stop reviewing and either trade or shut down.

---

machine-generated · model claude-opus-4-8 · called_from friday_bear_case · logged to llm_calls
