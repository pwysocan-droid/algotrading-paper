# Pre-mortem: Round 005

Blind review of `reviews/foundry/round-005.json` against `reviews/foundry/dead-ideas.json` (28 prior deaths, 15 failure lessons). Goal: kill on paper what can be killed on paper, before any gauntlet spend.

---

## 1. `placebo_losing_streak_single_gate_trend` — **SKIP**

**Lesson violated:** *THE GATE SURVIVED, THE ENGINE DIED* (r001).

The lineage_check only compares this idea against the r004 conjunctive-gate death and concludes the single-scalar gate fixes the family's problem. But it never checks against the closer analog: `drawdown_regime_contrarian_gate` (r001) *already* paired the self-referential gate with a weak intraday breakout engine, reached an ample armed sample (**n=460**, not gate-starved), and still died — 43.3% win rate, gross Sharpe 0.98, net **-0.65%/trade**, because "the base breakout signal underneath is too weak." That death proved the gate wasn't the binding constraint *for that engine shape* — the engine was. Idea 1's engine ("current bar closes above prior bar's high/low" continuation, confirmed by a 12-bar trend-sign filter) is the same species of intraday trend-continuation-on-confirmation engine, just re-skinned. Loosening the gate to a single scalar doesn't address why r001's version of this engine lost money at good sample size.

Two compounding problems:
- **Gross-positive trap shape:** its own fee_survival math nets out to "hoping for 44% win rate to clear +0.4% gross" — the same razor-thin shape that killed `round_number_breach_continuation` (42.3% win, positive Sharpe, still -0.37%/trade net).
- **Maker-fee assumption doesn't match the entry mechanism:** fee_survival claims "~+0.25% net maker," but the entry rule fires when price *closes beyond* the prior bar's high/low — a taker-style chase, not a resting limit an order can rest at. This violates *COST IS A DESIGN INPUT* ("prefer entries where price comes to the level"); you cannot get a maker fill on a breakout-confirmation entry. Strip the maker assumption and the edge argument (+0.2% gross at 40% win) collapses toward the fee floor.

Idea 4 in this same round tests the identical gate with a multi-day engine instead — the strictly stronger version of this same hypothesis. Running idea 1 spends a gauntlet slot re-testing an engine shape r001 already falsified at n=460.

---

## 2. `trailing_return_rank_persistence_hold` — **IMPLEMENT**

No fatal flaw found.

- **Base rate:** ~1.0-1.5 placed fires/day across the basket → 930-1,395 over 930d; even at half the estimated qualification rate, n≥465. Comfortable margin against the historical 3x-8x (and occasionally worse) miscalibration pattern.
- **Ceiling:** tp15/sl6/168h — cost ratio ~0.04 of target, squarely in the admissible multi-day/maker-friendly band, not the empty sub-12h zone.
- **Lineage:** correctly distinguished from `post_shock_multiday_drift` (r003 dead) — that entered ON a shock impulse and found no persistence; this enters on a slow-built rank state, a different premise. Not a descendant of `macross_family` either (that was 5-min crossover chop, this is weekly rank).
- **Conjunction check:** the entry condition ("top-ranked of 5" AND "return > 10%") is not treated as two independent multiplied probabilities — it's stated as one joint condition on the leader's own return distribution, so it doesn't fall into the *CONJUNCTIONS MULTIPLY TO ZERO* trap.
- Minor gap: no explicit pre-gauntlet premise check validating the 55-65% qualification assumption against actual data (as idea 5 does for its autocorrelation claim). Given the wide sample margin, this isn't fatal, but a 1-hour histogram check of "days the leader's 7d return exceeds 10%" before the full 930d run is cheap insurance.

---

## 3. `weekly_pullback_limit_into_uptrend` — **IMPLEMENT**

No fatal flaw found, but flagging the residual risk this idea is already built to test.

- **Base rate:** ~0.6 fills/day for the basket → ~558 over 930d; halved still clears n≥279.
- **Ceiling:** tp12/sl5/120h, maker limit entry — cost ratio ~0.03-0.05, admissible multi-day band, and unlike idea 1 the entry mechanism (a resting limit at the pullback level) actually matches its maker-fee claim.
- **Lineage:** distinguishes correctly from `pullback_to_breakout_level_limit` (r003, worst Sharpe ever, adverse selection — retests select failing breakouts). The residual concern: is "3% below the 24h high, inside an 8%+/week uptrend" still an adverse-selection trap, i.e., does requiring a *touchable* pullback systematically select the weaker trends within the uptrend bucket (strong trends grind up without ever offering the discount)? This is a real echo of the r003 mechanism at a different horizon. However, the idea's own kill_criterion explicitly names this exact failure mode ("if pullbacks-in-weekly-uptrends select failures the way intraday retests did") and is falsifiable at n≥279 — this is the hypothesis under test, not an unexamined blind spot. Worth implementing to get a decisive answer rather than skipping pre-emptively.

---

## 4. `placebo_streak_gated_weekly_trend_engine` — **REDESIGN**

**One change that fixes it:** validate the gate's actual historical open-frequency against real `null_baseline` trade logs (not the assumed "~27% open, single smooth statistic" estimate) *before* committing to the full 930-day gauntlet, and widen `placebo_floor` if needed until the armed sample carries at least a 5-10x cushion above n=100 — not the current 2.5x.

This is the fifth consecutive test of the self-referential gate family, and the calibration record for this specific family is uniquely bad: every prior gate idea over/under-fired its prediction, and **none has ever reached n≥100 armed** (r001 n=460 *raw*-armed but that's the outlier; r002 n=109/35; r003 n=7; r004 n=39). Historical miss factors for gate ideas specifically: r001 gate-open rate missed 3x, r002 rejection gate missed ~6.7x, r003 slot-scarcity gate missed **166x**, r004 missed **28x**. Idea 4's own arithmetic states "even at 40% of estimate, n≥100" — a 2.5x safety cushion. That is thinner than the *smallest* miss ever recorded for this family (3x), let alone the 28x-166x misses seen twice. On the historical base rate of this specific family's calibration failures, this idea is odds-on to become gate-idea #5 that fails to reach a decidable sample, independent of whether the underlying win-rate-lift hypothesis is true.

The fix is cheap relative to the full gauntlet: this idea already sits at the top of the funnel (single-scalar gate × a metered engine that itself only fires ~1/day) so there's no headroom to absorb another characteristic gate-family miss. A real gate-open-rate measurement against the live `null_baseline` history, or a looser threshold, removes the single biggest risk without changing the core hypothesis (single-condition gate + multi-day engine, which is a genuinely novel and worthwhile combination per the r001-r004 lessons).

---

## 5. `multiday_magnitude_persistence_directional_hold` — **IMPLEMENT**

No fatal flaw found; the most self-aware spec of the round.

- **Base rate:** conjunction of mag_persistence≥0.25 (~50% of days) and |168h return|>0.06 (~55% of days) is explicitly argued as positively correlated rather than multiplied as independent (~35% combined, not 27.5%) — this is exactly the discipline *CONJUNCTIONS MULTIPLY TO ZERO* demands, done correctly instead of assumed. Even at 30% of the resulting estimate, n≥334.
- **Ceiling:** tp14/sl5/144h, cost ratio ~0.04 — admissible multi-day band.
- **Lineage:** correctly separates from both info-theory deaths. `conditional_entropy_regime_expansion` (r002) and `return_magnitude_compressibility_break` (r004) both died because they asked an information-theoretic signal for *direction*, which the r004 epitaph named explicitly as the flaw ("compressibility break identifies volatility-regime birth; it does not identify which direction"). This idea takes the r004 prescription literally: info-theory is used *only* as a regime-quality gate, direction comes from the trend sign — never asking entropy/magnitude for a sign.
- **Best practice already built in:** the kill_criterion requires the pre-implementation premise check (lag-1 |return| autocorrelation actually reaching 0.25+ on 40%+ of symbol-days) to be confirmed before the full gauntlet is spent — the exact "check the premise against the data distribution first" discipline the r002 lesson calls for, applied proactively rather than in hindsight.

---

## Summary

| Idea | Verdict |
|---|---|
| placebo_losing_streak_single_gate_trend | **SKIP** — re-runs r001's already-falsified gate+weak-breakout-engine shape; maker-fee claim contradicts a chase-style entry |
| trailing_return_rank_persistence_hold | **IMPLEMENT** |
| weekly_pullback_limit_into_uptrend | **IMPLEMENT** |
| placebo_streak_gated_weekly_trend_engine | **REDESIGN** — validate/loosen gate-open rate against real history before full gauntlet; current 2.5x cushion is thinner than any prior gate-family miss |
| multiday_magnitude_persistence_directional_hold | **IMPLEMENT** |
