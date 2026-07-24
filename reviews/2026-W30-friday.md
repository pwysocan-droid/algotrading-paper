The picture is complete. Only null_baseline has closed trades; every candidate arm is shadow-disabled; runs telemetry is still 100% NULL.

---

# Friday Adversarial Review — Week 30 (2026-07-17 → 2026-07-24)

You asked for the bear case. The headline: **the placebo is the only strategy that has ever placed a live trade, it lost money this week, and every real candidate is disabled.** The project has been running ten-plus weeks and its entire live P&L history is 38 closed trades from the deterministic null arm — down −$62.37.

## 1. The trade history bear case

**Only one variant traded: `null_baseline`. 38 closed trades, 16 wins (42% win rate), −$62.37 net.** This is the placebo — the arm that exists to lose, and it is losing on schedule. There is no edge to attack because there is no candidate in the ring. The bear signal is not in the numbers, it is in the roster: `bollinger_verytight` alone emitted 3,683 signals this week, `bollinger_tight` 2,031, `macross_veryfast` 1,029 — and **every one was rejected as "shadow arm — variant disabled, research signal only" (12,658 rejections).** The strategies you spent weeks building fired thousands of times into `/dev/null`. Meanwhile the loss profile of the one live arm is textbook broken: stop-losses cluster at exactly −$7.08 (fixed-size losers), and the single take-profit (+$8.93) barely offsets three −$7.08 stops on the same AVAX symbol on 2026-07-23. With 38 trades this is below the 30-trade reliability floor for any *candidate* claim anyway — but the null arm isn't supposed to have an edge, so the only claim it supports is "the harness executes trades," and even that took ten weeks.

## 2. The promotion bear case

**Zero promotions ever — the recommendations table has zero promoted rows and zero new recommendations since before 2026-07-10.** Last week I wrote that no-promotion was discipline working. One week later I am revising that: the absence is no longer caution, it is a **stalled pipeline**. Every candidate is in shadow mode emitting research-only signals that get auto-rejected. Nothing can be promoted because nothing is eligible to trade, and nothing is being newly recommended. The tuner/foundry that the W29 log advertised as generating "5 exotic ideas per round, ~1 round per 1–2 days" has produced **zero recommendations in this window**. Either the foundry stopped, or its output never reaches the recommendations table. The constraint isn't human-in-the-loop caution — there is no candidate on the operator's desk to say yes or no to.

## 3. The runs / decisions bear case

**2,057 runs, 100% ok, 0 failed — no data hole. But `signals_emitted` and `trades_placed` are NULL on all 2,057 rows, unchanged from last week.** I flagged this exact NULL-telemetry blindness in the W29 review. It was not fixed. The review apparatus is still reading emitted-signal counts off the `signals` table by hand because the `runs` table records nothing about what each run did. **Rejected:placed ratio is 13,581:38 — a 35,700% rejection rate, catastrophically above the 50% threshold.** But 12,658 of those rejections are the shadow-disable flag, not a real constraint. Strip those out and the real execution constraints are: 916 "5 concurrent positions already open" and 5 cooldown rejections. So the actual live loop is: null_baseline saturates the 5-position cap, holds for 24h, and rejects everything until a slot frees. The cap is still self-deadlocking on the one arm allowed to trade — exactly the failure I said to watch for last week, still present.

## 4. The drift check

**This is the second review; last week's four baseline concerns were all restated, none resolved.** (1) Closed-trade count: went from 0 to 38 — real progress, but all placebo. (2) NULL telemetry: **still NULL, not touched.** (3) Self-deadlocking cap: **still deadlocking** — 916 cap-full rejections confirm it. (4) Foundry-vs-reality: the "faster factory upstream of a pipe that never passes a unit" concern is now worse — the factory produced zero recommendations while the pipe passed only placebo trades. Three of four flagged items are unaddressed, which by this methodology's own rule makes them **dismissed signals, not ongoing risk**. Nothing last week said "should not be promoted" got promoted, because nothing got promoted at all — the pipeline has no promotion path wired to live execution. The narrative-substitution failure mode I warned about is arriving: "rich idea pipeline / thousands of signals emitted" is standing in for "zero candidate strategies have ever placed a live trade."

---

> If the project enables at least one candidate arm to place live trades AND fixes runs telemetry to record per-run signals/trades, the bear case will weaken. If next Friday still shows only null_baseline in the trades table with shadow-disabled candidates emitting thousands of auto-rejected signals, the bear case will strengthen — you will have run twelve weeks of infrastructure that has never once let a real strategy trade.

TOMORROW: Enable one candidate arm (start with the lowest-signal-volume one, e.g. macross_veryslow at 98) to place live trades beside null_baseline — the shadow-only roster means no strategy you built has ever been measured against reality.

---

machine-generated (investigator, 6 turns) · model claude-opus-4-8 · called_from friday_bear_case_investigated · logged to llm_calls
