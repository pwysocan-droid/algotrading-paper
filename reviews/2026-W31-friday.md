The picture is identical to last week, one week later. Writing the review.

---

# Friday Adversarial Review — Week 31 (2026-07-24 → 2026-07-31)

You asked for the bear case. The headline is unchanged from last week, which is itself the story: **the placebo is still the only strategy that has ever placed a live trade, it lost more money this week than last, and every real candidate is still shadow-disabled.** Week 30's TOMORROW line said "enable one candidate arm." Seven days later, zero candidate arms trade. The single recommended action was ignored.

## 1. The trade history bear case

**Only `null_baseline` traded: 36 closed trades, 16 wins (44%), −$38.91 net.** This is the deterministic null arm — the one built to lose — and it is losing on schedule. There is no candidate edge to attack because no candidate is in the ring. The loss profile is textbook mechanical: three stop-losses land at exactly −$7.118, fixed-size losers with no risk logic behind them, and the biggest single loss (−$7.12 AVAX, 1,185-minute hold) is a stop that took nearly a full day to trigger. 24-hour time-exits dominate (avg hold 1,385 min), meaning this arm isn't trading a signal — it's holding a coin flip for a day and booking the drift. **36 trades is below the 30-trade reliability floor for any candidate claim, and the null arm has no edge to claim anyway.** The only thing these trades prove is that the harness executes orders. Meanwhile `bollinger_verytight` emitted 5,251 signals into `/dev/null` this week, `bollinger_tight` 2,834, `macross_veryfast` 1,443 — every one auto-rejected as "shadow arm — variant disabled." The strategies you built fired ~18,000 times and touched reality zero times.

## 2. The promotion bear case

**Zero promotions. Zero new recommendations in the window.** Per the template: the absence of promotions is itself a signal, and the signal is not caution — it is a stalled pipeline. There is no candidate on the operator's desk to approve or reject because nothing is eligible to trade and nothing new is being recommended. The `recommendations` table produced no promoted rows this week and no new candidates. The "idea foundry" narrative — exotic strategies, self-excitation, epidemic-ignition arms — shows 31 distinct variants emitting signals, but the pipeline from "emits research signals" to "eligible for live trade" is not wired. Last week I said the no-promotion state had crossed from discipline into stall. It has now been stalled for two consecutive review windows. Human-in-the-loop caution requires a candidate to be cautious *about*; there is none.

## 3. The runs / decisions bear case

**2,057 runs, 100% ok, 0 failed — no data hole. But `signals_emitted` and `trades_placed` are NULL on all 2,057 rows — identical to last week and the week before.** This telemetry blindness has now been flagged in three consecutive reviews and touched zero times. The review apparatus still reconstructs signal counts by hand from the `signals` table because `runs` records nothing about what each run did. **Rejected:placed is 18,117:36.** Strip the 17,194 shadow-disable flags and the real constraints are **912 "5 concurrent positions already open" rejections** and 4 cooldown rejections. The position cap is doing all the constraining, and it is constraining the *one arm allowed to trade* against itself: null_baseline saturates the 5-slot cap, holds ~24h, and rejects everything until a slot frees. That is a self-deadlock, not a risk control — and it is the same 900-plus cap-full count as last week. The constraint that only ever fires on the placebo isn't protecting a portfolio; it's throttling a coin flip.

## 4. The drift check

**This week's bear case is not weaker than last week's — it is the same case verbatim, which is worse.** Every W30 concern recurs unaddressed: (1) only null_baseline trades — still true, and its loss deepened per-trade (−$1.08 avg vs. the harness's only purpose being "it executes"); (2) NULL run telemetry — still 100% NULL, untouched; (3) self-deadlocking position cap — still 912 cap-full rejections; (4) foundry produces zero recommendations into live — still zero. By this methodology's own rule, a bear case that recurs unaddressed is not "ongoing risk" — it is **dismissed signal**. The W30 TOMORROW line named the exact fix (enable macross_veryslow beside the null arm); it was not done. Nothing flagged "should not promote" got promoted, because the promotion path to live execution still does not exist. The documented failure mode of this project is now fully arrived: "31 variants, 18,000 signals, rich idea pipeline" is standing in for the fact that **no strategy you built has ever placed a single live trade across twelve-plus weeks.**

---

> If the project enables at least one non-null candidate arm to place live trades this week, the bear case will weaken. If next Friday's trades table again shows only null_baseline while candidates emit thousands of shadow-rejected signals and runs telemetry remains NULL, the bear case will strengthen decisively — a fourth identical review means the review itself is being read and ignored.

TOMORROW: Enable one candidate arm (macross_veryslow, lowest signal volume at ~145) to place live trades beside null_baseline — the same instruction as last week, unexecuted, and nothing else in this project matters until it is.

---

machine-generated (investigator, 6 turns) · model claude-opus-4-8 · called_from friday_bear_case_investigated · logged to llm_calls
