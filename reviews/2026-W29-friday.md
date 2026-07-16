The story is now clear. Here is the review.

---

# Friday adversarial review — 2026-W29

algotrading-paper / friday bear-case · 4G methodology
Week under review: **2026-07-09 → 2026-07-16** (ISO week 29)
The bear case only. No hedging. The bull case lives elsewhere.

---

## 1. The trade history bear case

**One variant, `null_baseline`, with four trades — all opened in a single 20-minute window today (2026-07-16, 21:45–22:05 UTC), none closed.** There is no trade history to make a bear case against; there is an ignition event that happened on the last afternoon of the review week. Zero exits means zero realized P&L, zero win rate, zero hold-time data — every performance dimension the template asks me to attack is null.

`null_baseline` is, by name, the control arm — a strategy that exists to lose to. Its four positions (ETH long, AVAX short, BTC short, SOL long) are not an edge and were never meant to be one. **Any performance claim about anything this week is statistically unreliable in the strongest possible sense: n=4, all open, all in one hour, all on a baseline that is definitionally not a strategy.** The correct response is not "wait for more data" — it is "note that data collection began on the final day and the week produced no observable trade behavior at all."

## 2. The promotion bear case

**No promotions this week. The `recommendations` table has zero rows since June 1 — likely zero rows ever.** Per the template, absence of promotions is itself a signal, and here the signal is unambiguous: there is nothing to promote because the tuner has produced nothing, because there is exactly one registered variant and it is the control. This is not the operator being too cautious. **There is no candidate pipeline.** Eleven weeks after review #1 warned that "no strategy is registered," the registry still contains only `null_baseline`. The tuner cannot be investigated for producing bad candidates; it has produced none, which means the entire promotion apparatus — recommendations, backtests, walk-forward gates — is untested vaporware sitting downstream of a roster that was never built.

## 3. The runs / decisions bear case

**Runs are immaculate and meaningless: 2,016 runs this week, 100% `ok`, zero failures. Lifetime: 15,643 runs, all 19 failures confined to May.** No data hole. But 2,016 clean runs produced their first-ever trade on the last day — the pipeline is a metronome logging 81 bars an hour into a table nobody trades on. Your own nightly skeptic already named it: "a metronome with no conductor."

**Decisions this week: 4 placed, 3 rejected — a 43% rejection rate, but n=7, all from today.** All three rejections are identical: 1-hour cooldown not elapsed on SOL/BTC/AVAX. This is not a constraint being stress-tested; it's the cooldown firing correctly the very first time the system fired at all. You cannot conclude the limits are too loose or too tight from seven decisions in one hour. **The infrastructure conclusion stands regardless of the ratio: a decision engine that made its first seven decisions today has been "running" for two and a half months deciding nothing.**

## 4. The drift check

**This week's bear case is the same bear case as review #1 (W21), eleven weeks later, and that is the entire finding.** W21's number-one punch-list item: "Register a strategy or admit the curriculum is paused." W21's central attack: "zero signals, zero trades, zero decisions... the experiment has not started." Eleven weeks on, the only variant is still the null baseline and the first four trades opened *hours before this review*. **This is not "ongoing risk." A bear case that recurs unaddressed for eleven weeks is a dismissed signal, not a tracked one.**

The drift is worse than softening — it's the calendar. `pending.md` records that the W21 review was review #2's baseline and that **the Fridays of 07-03 and 07-10 were both missed.** The methodology designed to catch exactly this eleven-week stall did not run for the eleven weeks the stall occurred. W21 explicitly warned: "If [the next review] slips, the methodology is dead." It slipped, twice, this month alone. Meanwhile "Phase 1 review" is marked **OVERDUE** (review date 2026-07-12 already passed), and the future-self letters have been "open" since 2026-04-26 — the project's entire life, flagged in W21, still open. Nothing W21 flagged as recurring got closed. **The one genuine change — four trades today — is real, but it arrived so late in the week and so long after it was due that it reads as a response to the imminent review, not a shift in the project.** W21's harsh floor was correct, and this review degrades from it: same concerns, plus a now-demonstrated pattern of skipped reviews.

---

> **If the project registers at least one real (non-baseline) strategy variant and accumulates closed trades on it before next Friday's review — which must actually be written — the bear case weakens.** **If next Friday arrives with `null_baseline` still the only variant, the four trades still the entire history, and the Phase 1 review still OVERDUE, the bear case strengthens to its terminal form: the infrastructure was the project, and eleven weeks of clean cron runs were an elaborate way of never asking the research question.**

TOMORROW: Register one real strategy variant or write the Phase 1 review that decides extend-or-archive — it is four days overdue and it is the only decision that unblocks everything else.

---

machine-generated (investigator, 7 turns) · model claude-opus-4-8 · called_from friday_bear_case_investigated · logged to llm_calls
