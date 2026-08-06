# PROPOSAL — B′ gate seed interrogation (drift flag fired 2026-08-06)

Status: **PROPOSAL — logged, awaiting operator sign-off. NO gate change
enacted.** Per the standing rule, the trailing-252d p90 gate (CONSTITUTION 2.9 /
book/pre-reg-book-gate-v2.md) is interrogated only through a logged proposal;
this is that proposal. The running gate, the p90 percentile, and the 252-day
window are untouched until this is signed off as a versioned amendment.

## 1. Observation — the drift flag fired

The daily digest surfaced it, as designed: **realized gate fire 0% vs 21%
predicted, n = 21** (`⚠ >10pp off prediction — investigate`). Trajectory: n =
11 → 16 → 21 over 08-03/04/05, realized 0% throughout. The B′ gate has written
**zero** spreads across 21 ETF-day decisions against a backfill-predicted ~21%.

## 2. Diagnosis — a seed cost-model inconsistency

The trailing-p90 threshold is seeded from the committed backfill richness series
(`reports/vrp-richness-backfill-1sd.json`), whose `rich_hc` used a **fixed
$0.06 haircut** (2 × $0.03/leg). Live richness is `short_bid − long_ask` — the
**real bid/ask crossing on both legs**, which for index-option spreads is
typically $0.10–0.40, i.e. materially wider than $0.06. So on a $5-wide spread
live richness runs ~1–7 pp **below** the backfill seed. Observed live richness
from the daily runs (SPY 11–13%, QQQ 2%, IWM 8–9%, DIA 2–5%, GLD 3–5%) sits
**below the seeded p90 thresholds** (13.8–17.4%) → 0% fire. This is the *same
biased-proxy gap* recorded in July (backfill implied ~45% clear 20%; real quotes
were 12–13%), now inherited by the p90 **seed**.

## 3. Why it matters — undecidability risk

The p90 relative gate was introduced to fix the flat-20% gate's "never fires →
undecidable" problem. If the seed bias makes the p90 gate *also* fire ~0%, the
candidate accumulates **no executed record**, cannot reach n ≥ 30 executed, and
**fails its 12-month live gate (2027-07-31) by undecidability** — the exact
failure mode resurfacing one layer up. The flag is doing its job by catching this
now rather than at the deadline.

## 4. Proposed first step — MEASURE, do not adjust (zero gate change)

Instrument the harvester to log, per scan, **both** the *mid* credit
(`(short_bid+short_ask)/2 − (long_bid+long_ask)/2`) **and** the *executable*
credit (`short_bid − long_ask`) it already logs. This is a measurement-only
addition to the shadow record — it changes no gate, places no order. Accumulate
~2 weeks across the 5 ETFs, then quantify the **actual live crossing cost**
(mid − executable) and compare it to the backfill's $0.06 assumption. This
converts "the seed looks too rich" from inference to a measured number.

## 5. Pre-registered decision rule (decided by the data, NOT by a wish for trades)

After the measurement, exactly one of two paths — chosen by the number, committed
here in advance so the choice can't be argued toward trades:

- **(A) Seed correction.** If the measured crossing cost materially exceeds
  $0.06 and explains the 0%-fire gap, **recompute the backfill seed's richness
  with the live-consistent crossing cost** and reseed the trailing reference.
  The p90 percentile and 252d window are **unchanged**; only the seed's cost
  model is corrected to match live. The gate then resumes its intended ~10%
  *relative* firing, and the always-write shadow control + forward P&L judge
  whether those writes are +EV (2.5). This is a principled correction of a
  demonstrable inconsistency, not a loosening.
- **(B) Recorded negative.** If, even after correcting the seed's cost model,
  the top-decile *live* richness is still below the fair-pay bar (i.e. real
  crossing costs eat the premium), then the honest reading is that **the VRP at
  1-SD is not tradeable net of real costs** — recorded as a negative
  (`shelved_premise`/dead per the evidence), the same cost-floor verdict Charter
  E reached. **We do NOT reseed to force trades against a premium that isn't
  fairly paid.**

## 6. Guardrails (anti-goalpost-shopping, explicit)

- The **p90 percentile and 252-day window are not on the table** — only the
  seed's cost model, and only if (A)'s measured condition holds.
- The **always-write shadow arm remains the arbiter**: any resumed writes are
  tested against always-write and the drift null (2.5), so a seed correction that
  merely manufactures −EV trades is caught and kills the candidate.
- Any enacted change is a **versioned commit with rationale** amending
  book/pre-reg-book-gate-v2.md; nothing changes in the moment.
- If the measurement is ambiguous, the default is **(B) / do nothing to the
  gate**, not (A) — the burden is on the data to justify a seed change.

## 7. Not proposed

No in-the-moment gate change. No percentile/window tuning. No reseeding before
the crossing-cost measurement exists. The gate keeps firing 0% (correctly, given
its current seed) until this proposal is signed off and its measurement resolves.
