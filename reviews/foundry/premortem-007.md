# Premortem — Round 007

Blind review: no context beyond `round-007.json` and `dead-ideas.json`. Adversarial stance — trying to kill each idea on paper before any gauntlet slot is spent.

Calibration prior applied throughout (given, 2026-07-19 regression, 18 gradient records): predicted fire rates carry ~zero information. Specs whose own final predicted rate is **>=0.3 fires/sym/day are historically over-predicted ~17x**; specs **<0.3/sym/day are under-predicted ~2x**; scatter ±8x either way. I bucket each idea's own stated final placed-rate (not intermediate/raw numbers) and re-derive an expected `n` over 930d×5sym (4,650 symbol-days).

Decidability bar: n >= 100 placed trades. Ceiling: sub-12h OHLCV is measured empty; admissible band is 24h+ (maker-friendly) or multi-week holds.

---

## 1. `liquidity_window_shock_fade_maker` — **REDESIGN**

**The one change:** align `shock_pct`/`vol_mult` in `params` with the thresholds actually used to derive the fire-rate estimate, and run the extension-to-fill premise check against real data *before* committing a slot.

- The mechanism itself is well-targeted: it's the one lesson-sanctioned admissible fade (SHOCKS MEAN-REVERT AT MULTI-DAY HORIZON explicitly opens a shock-fade spec as admissible), horizon is 96h (comfortably in the 24h+ maker band), and it correctly avoids the r003 retest adverse-selection shape by arguing extension deepens the mispricing rather than selecting failures.
- **But there's an internal arithmetic contradiction.** `expected_fire_rate` computes its ~1,160 raw triggers by explicitly *loosening* the trigger to `shock_pct=0.02, vol_mult=2.5` ("So loosen shock_pct to 0.02 and vol_mult to 2.5"). The `params` block, however, still specifies `shock_pct: 0.03, vol_mult: 3.0` — the *strict* threshold tied to the measured control-arm population of n=53 shocks over the full 930d×5sym history. If implemented as coded, the raw trigger population is ~53, not ~1,160 — a >20x gap that is paper-detectable right now, no gauntlet required.
- Recomputing on the spec's *own* final placed-trade estimate (209, i.e. 0.045/sym/day, <0.3 bucket → ~2x over-prediction expected) still nominally clears n≈100 — but that number is built on the mismatched params, so it isn't trustworthy either way.
- Using the actual coded params (n=53 base population) × the stated 18% fill-conversion gives ~9-10 placed trades — squarely in the "inconclusive_starved" graveyard (`slot_scarcity_conviction_gate` n=7, `weekly_pullback_limit_into_uptrend` n=3).
- Independent of the params bug, the extension-to-fill condition (price must extend a further 0.6% within 6 bars) is structurally a **touch-condition nested inside an already-rare event** — the exact shape RARE-TOUCH CONJUNCTIONS MISS WORST OF ALL flags as missing base-rate estimates by 166x-186x, worse than any non-touch conjunction. That lesson demands the actual joint frequency be histogrammed against data before spending a slot, which this spec's `kill_criterion` does not do (it only checks adverse selection *after* firing).

## 2. `cross_sectional_dispersion_gate_trend_engine` — **IMPLEMENT**

- Gate family status check: the self-referential-gate family is CLOSED (2026-07-19, amended r005) *unless* a spec names a genuinely external information source. This spec conditions on cross-sectional basket dispersion — not the engine's own trade outcomes — which is the same reopening argument r006's `constraint_rejection_pressure_release_engine` used and which premortem accepted as legitimate on mechanism grounds (it just died on absolute performance, and explicitly left "the cross-sectional-synchronization MECHANISM itself... formally untested against its intended control" as an open question).
- This spec closes that exact gap: its `kill_criterion` requires the gated engine to beat the *same* engine run ungated at n>=100 — the direct control comparison r006 never ran. That's a methodological improvement over its nearest ancestor, not a repeat of it.
- Gate structure is a single continuous scalar threshold (dispersion percentile), not a multi-condition conjunction — structurally closer to r005's `placebo_losing_streak_single_gate_trend` (which reached n=3,006, no starvation) than to the multi-condition `system_state` gates that starved every time (r001 n=460 best-case down to r004 n=39). Starvation risk is lower than the gate family's historical norm.
- Recalibrating on the spec's own final estimate (~279 placed, 0.06/sym/day, <0.3 bucket → ~2x over-prediction expected) still lands near n≈140 — above the decidability floor even after the calibration haircut.
- Explicitly framed as this round's mandated continuation canary (per CANARY MANDATE). Flagging the known blind spot: PREMORTEM CANNOT SEE REGIME RISK — a clean paper verdict here does not mean it will survive; REGIME IS THE VARIABLE means a with-trend continuation bet is odds-on to fail in this epoch. That's not a paper-detectable flaw, it's exactly why the canary must be run rather than skipped.
- No fatal flaw found on paper. Implement to get the canary's answer.

## 3. `kolmogorov_directional_asymmetry_break` — **REDESIGN**

**The one change:** drop the `AND current close > close[lookback]` with-trend confirmation from the entry rule; take direction purely from the sign of the asymmetry statistic `A` and test *that* on its own.

- The core measurement (LZ-complexity/entropy asymmetry between up- and down-magnitude sub-streams) is genuinely the one untested corner of the information lens — correctly distinguished from saturated sign-entropy (r002, dead both directions) and direction-blind magnitude-surprise (r004, dead).
- As specified, though, direction is *not actually taken from the novel statistic* — it's taken from trend sign, with the asymmetry statistic acting only as a gating filter. That is precisely the shape of `multiday_magnitude_persistence_directional_hold` (r005): an information-theoretic regime-quality gate, paired with "direction from trend sign," which premortem called "the most self-aware spec of the round" and which died anyway because "a genuine vol-clustering regime does not, in this basket and epoch, mean the co-occurring trend is more likely to continue." Swapping the specific info-theoretic filter (compressibility-persistence → directional-asymmetry) does not change that underlying, already-falsified direction mechanism.
- The 48h hold is squarely inside the horizon band REVERSION AT EVERY MEASURED HORIZON found continuation dead in (9/9 cells, multi-day through monthly), and REGIME IS THE VARIABLE confirms directional momentum has flipped negative across this entire archive — a real conflict the spec's lineage_check doesn't engage with at all (it only discusses r002/r004, never the regime lessons).
- Fire-rate arithmetic is not the problem: spec's own final estimate (~372 placed, 0.08/sym/day, <0.3 bucket → ~2x over-prediction expected) still lands near n≈186, comfortably decidable.
- If the redesign is taken (direction purely from `sign(A)`, no trend filter), the idea actually tests something new — whether accumulation/distribution organization predicts direction independent of trend, which the regime lessons haven't already closed.

## 4. `epidemic_susceptible_depletion_terminal_burst` — **REDESIGN**

**The one change:** widen `run_pct`/`run_bars` (or otherwise raise the raw run-population rate) before spending the slot — the calibration-adjusted placed-trade estimate sits right in this project's historical near-miss band, and a closely analogous idea just landed there and produced no usable claim.

- Correctly fade-shaped and horizon-appropriate (48h, contrarian, matches the sanctioned reversion signature), and it does distinguish itself from the point-process import family (Omori/R0/Hawkes, 3-for-3 dead) by trading termination rather than continuation — a real, not cosmetic, distinction.
- It is, however, the **second volume-exhaustion cross-domain idea in two rounds**: `predator_prey_volume_depletion_rebound` (r006) tested "volume declining over a directional run → contrarian entry" and landed at n=62/58 — just under the n>=100 decidability floor — with a near-null edge (-0.13%/+0.11%, "no claim, positive or negative"). This spec's own distinction (volume-per-displacement *efficiency ratio* vs r006's raw volume count) is real but untested for whether it meaningfully changes the fire-rate/edge outcome rather than reproducing the same near-miss.
- Recalibrating on the spec's own final estimate (~167 placed, 0.036/sym/day, <0.3 bucket → ~2x over-prediction expected) gives n≈84 — *below* the n>=100 bar, and with the stated ±8x scatter this could easily land in single digits, repeating `predator_prey`'s inconclusive-starved outcome rather than answering anything.
- The mandated premise check (non-empty conjunction) is good practice but doesn't by itself fix the margin problem — it confirms the conjunction exists, not that it clears n>=100 with room for the calibration haircut.

## 5. `trapped_breakout_volume_void_reversal` — **SKIP**

**Lesson violated:** MICROSTRUCTURE-FROM-OHLCV LENS EXHAUSTED. This lens is now confirmed dead on its 5th attempt (wick rejection r001, absorption r002 empty-set, gap-fill r003 starved, one-sided-range-expansion r004 well-powered and still negative, range-compression-then-expansion-gap r006 — whose own epitaph states "A fifth confirmation that OHLCV candle geometry alone is exhausted... no repackaging of the same four inputs (wick, body, volume, sequencing) has escaped that ceiling in five tries. The lens needs order-book/footprint data to proceed").

- This spec is built from exactly those same four inputs — breakout-bar volume vs. level-building volume (volume + wick/body geometry) plus a re-entry close (sequencing) — still pure OHLCV, still no order-book/footprint data. The "two-phase flow-order" framing is a genuinely more elaborate shape than the prior five, but the lesson's closure is about the *data source*, not the specific geometric relationship tested — five different relationships (fade, absorption, gap, one-sided thrust, compression/expansion) have already failed on that same input space, and this is a sixth.
- The lineage_check argues distinction from r004/r001/r006 on the specific geometric claim, but never engages with the lens-level closure statement itself, which is the actual barrier here — a new geometric permutation on the same closed data source is not the "fundamentally different mechanism" the lesson requires to reopen it.
- Fire-rate is also weak on its own terms: spec's own final estimate (~124 placed, 0.027/sym/day, <0.3 bucket → ~2x over-prediction expected) gives n≈62 — below the decidability floor, an independent reason this would likely land as another inconclusive_starved entry even if the lens weren't already closed.
- The idea's own mandated premise check (is low-volume-breakout anti-correlated with breaking out, "exactly like absorption") is the right question to ask — and its very framing, invoking the empty-set absorption death as the risk to check against, is itself evidence this spec knows it's re-treading the same exhausted ground.

---

## Summary

| Idea | Verdict | One-line reason |
|---|---|---|
| liquidity_window_shock_fade_maker | REDESIGN | `params` (3%/3x) contradict the fire-rate math's assumed loosened trigger (2%/2.5x); as coded, base population is ~53 events → ~9-10 placed trades, plus the extension-to-fill condition is a rare-touch-in-a-rare-event conjunction |
| cross_sectional_dispersion_gate_trend_engine | IMPLEMENT | Legitimate external-information gate reopening, closes r006's untested-control gap, single-scalar gate (lower starvation risk), calibrated n≈140; serves as the mandated continuation canary |
| kolmogorov_directional_asymmetry_break | REDESIGN | Direction is taken from trend sign, not from the novel asymmetry statistic — reproduces r005's already-falsified "info-theoretic regime gate + trend-sign direction" shape in a horizon band measured to revert; drop the trend-confirmation clause |
| epidemic_susceptible_depletion_terminal_burst | REDESIGN | Second volume-exhaustion cross-domain idea in two rounds; calibrated n≈84 sits below the decidability floor, in the same near-miss band as r006's closely analogous predator_prey idea (n=62/58, no claim) |
| trapped_breakout_volume_void_reversal | SKIP | MICROSTRUCTURE-FROM-OHLCV LENS EXHAUSTED (5-for-5 dead) — still pure candle+volume geometry on the same closed data source, and independently under-sampled (calibrated n≈62) |
