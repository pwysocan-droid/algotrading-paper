# New Directions — beyond continuous directional prediction

Written 2026-07-23, after both markets' price-prediction structure was
measured null. This is the strategic map for what to test next and how.
It is a living plan; each experiment updates it.

---

## The one-paragraph thesis

We have exhaustively searched **one structure** — *continuous directional
prediction on price/OHLCV* — across two markets, every horizon, single
factors and combinations, with measured ceilings at every turn. It is
null after costs. That is a real, instrument-backed result, not a
failure. But every ceiling we measured was a ceiling **on that structure
and that input space**, never on the market itself. The edge, if it
exists at retail scale, lives in a structure or a data space we have not
entered. This document names the untested ones, ranks them by
evidence, and gives each a falsifiable test that runs through the same
gauntlet + drift-null + multiple-testing + holdout discipline as
everything before it.

Non-negotiable inheritances (every direction below obeys these):
- Beat the **drift/benchmark null**, never zero.
- **Regime-condition** every claim (REGIME IS THE VARIABLE).
- **n<30 = no claim**; positive small samples are quarantined.
- **Multiple-testing haircut** on any best-of-N selection.
- **Costs are volatility-conditional** — worst exactly when events fire.
- **Trust direction over magnitude**; magnitude is usually inflated.
- Pre-register a **kill criterion** before each test.

---

## The four directions, ranked by evidence

### D1 — Event-driven / tail (HIGHEST evidence: a measured lead)
**Structure:** don't predict continuously; act only around specific
catalysts, contrarian to the crowd's forced flow.
**Why now:** we already *measured* the signal and shelved it. The
**shock-fade**: after a 3%/3x-volume shock bar, crypto reverts −3 to
−4% over multiple days (n=53) — the largest gross effect in the project,
recorded as a lesson, never built into a spec.
**Known failure mode:** costs spike exactly when shocks fire
(volatility-conditional slippage) — the fade must clear a *widened* cost
floor, and entries should be limit/maker where possible (price comes to
you on a reversion).
**Test (first build):** an event-triggered contrarian spec — enter
against a qualifying shock, multi-day hold, maker-friendly entry; score
net of a volatility-widened cost model vs a "random large-bar" placebo
(the control arm the fragility audit demanded); regime-split; holdout.
**Kill:** net expectancy < 0 after volatility-conditional costs, OR
indistinguishable from the random-large-bar placebo.

### D2 — Carry / risk-premium harvesting (HIGH evidence: external + our tape)
**Structure:** get *paid to bear a risk* rather than predict direction.
**Why now:** funding-rate carry is a documented, persistent crypto
premium, and our Layer-2 tape has been recording funding + OI for days
(unused by any spec). Literature prior is banked: funding carry is a
**crash-risk premium, not free money** (BIS) — it pays steadily then
gives back violently in liquidations.
**Test:** a funding-carry spec — position on the paid side of funding
when the rate is extreme, sized small, with an explicit
liquidation/crash tail model; measure the *premium net of the tail*, not
the gross carry; regime-split across the 2024-26 funding history we hold.
**Kill:** tail-adjusted carry ≤ 0, OR the drawdown in a liquidation
event exceeds the accumulated premium (the BIS clawback).

### D3 — Regime-switching meta-structure (MEDIUM evidence: our own lesson)
**Structure:** the regime *is* the alpha — hold momentum in trends,
reversion in chop, cash when neither. One detector, two known behaviors.
**Why now:** REGIME IS THE VARIABLE showed directional momentum was real
for four years then inverted at our archive's doorstep; the gate family
was a failed first attempt (it gated on the system's own outcomes, which
proved to be noise). A cleaner version detects the *market's* regime
(e.g., a slow trend/vol filter) and switches the base behavior.
**Test:** a two-state spec — a pre-registered regime detector (trend-on
vs chop) selecting between a momentum leg and a reversion leg; the
canary already tells us the current state (reversion). Score vs a
"always-momentum" and "always-reversion" baseline — the switch must beat
BOTH, or the regime signal adds nothing.
**Kill:** switched expectancy does not beat the better of the two
single-behavior baselines (the exact clause the gate family failed).

### D4 — New data space (HIGH ceiling, but a spend decision, not research)
**Structure:** same prediction, richer inputs the market mines less.
**Options:** crypto Layer-2 (funding/OI/book — tape collecting, feeds D2
too); equity **fundamentals** (value/quality — where durable long-only
equity edge actually lives, absent from our archive); equity
**small-cap** (anomalies concentrate there, at real liquidity cost).
**Why gated:** fundamentals/small-cap-clean data is an acquisition
decision (cost, new pipeline), not a free experiment. Layer-2 is free
and already flowing → it rides with D1/D2.
**Test:** only after D1–D3; if those are null, a bounded fundamentals
probe (a single value or quality factor on purchased point-in-time data)
is the last "change the space" move before the program-level null.

---

## Sequencing & stop rule

1. **D1 shock-fade** — build first. Free, measured lead, decisive.
2. **D2 funding-carry** — second. Free (tape exists), different structure,
   external support.
3. **D3 regime-switch** — third, if D1/D2 warrant continued search.
4. **D4** — only a *bounded* data-acquisition probe, and only if D1–D3
   are null and the operator chooses to spend.

**Program-level stop (pre-committed, mirrors crypto v2):** if D1, D2, and
D3 each return null against their pre-registered kills, the conclusion is
declared: *retail-accessible edge in these markets and data spaces, across
the directional, event, carry, and regime structures, is absent after
costs* — and the project's product is the **instrument and the measured
negative**, which is a genuine and unusual result. D4 (new data) is the
only reopening, and it is a deliberate spend, not a reflex.

**The posture, stated plainly:** change the structure a small number of
times, decisively, following measured evidence — not infinite iterations
of a structure already proven empty. Be willing to let the null win. The
discipline that makes this project good is its willingness to stop.

---

## Status of each direction

| dir | structure | evidence | data | cost to test | status |
| --- | --- | --- | --- | --- | --- |
| D1 | event/tail | **measured lead** (shock-fade) | have | free | **next build** |
| D2 | carry | external + tape | have | free | queued |
| D3 | regime-switch | our own lesson | have | free | queued |
| D4 | new data | high ceiling | must buy (some) | $ + pipeline | gated on D1–D3 |
