# PROPOSAL — B′ gate seed interrogation (drift flag fired 2026-08-06)

Status: **Step 1 (measurement) APPROVED 2026-08-06; four amendments folded in.
Step 2 (the fork) awaits the measured number. NO gate change enacted.** Per the
standing rule, the trailing-252d p90 gate (CONSTITUTION 2.9 /
book/pre-reg-book-gate-v2.md) is interrogated only through a logged proposal;
this is that proposal. The running gate, the p90 percentile, and the 252-day
window remain untouched. Only the measurement instrumentation (§4, shadow-only,
zero gate change) is enacted now.

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

**Archive check (amendment 1): backdating is not possible — the quotes weren't
kept.** Grep 2026-08-06: `book/shadow.jsonl` and `reports/vrp-*.json` store only
the *executable* credit and richness — never the per-leg bid/ask — and no raw
chain snapshots exist. So mid-vs-executable cannot be reconstructed for the 21
gate-days; prospective is correct *by fact*, not by preference. (Retention gap,
closed going forward by this instrumentation.)

Instrument the harvester to log, per scan, **both** the *mid* credit
(`(short_bid+short_ask)/2 − (long_bid+long_ask)/2`) **and** the *executable*
credit (`short_bid − long_ask`) it already logs. Measurement-only addition to
the shadow record — changes no gate, places no order. **Immediate down-payment:**
a one-shot snapshot of today's mid-vs-executable across the 5 ETFs is taken now
for a directional estimate; the ~2-week accumulation is for robustness. Then
quantify the **actual live crossing cost** (mid − executable) and compare it to
the backfill's $0.06 assumption — turning "the seed looks too rich" into a
measured number.

## 5. Pre-registered decision rule (thresholds PINNED now — amendment 2)

Both conditions of (A) carry committed numbers, fixed here before the measurement
lands so the fork cannot be argued at decision time:

- **(A) Seed correction — activates ONLY if BOTH hold:**
  1. *"Materially exceeds $0.06":* measured live crossing cost **≥ $0.12/spread**
     (≥ 2× the seed's assumed haircut), median across the 5 ETFs; AND
  2. *"Explains the gap":* recomputing the backfill seed's richness with that
     measured crossing cost yields a **counterfactual fire rate ≥ 10% (≥ 2 of
     the 21 observed gate-days)** — i.e. the correction demonstrably restores
     firing on the actual live richness we saw.
  If both hold: recompute the seed's richness with the live-consistent cost and
  reseed. **p90 percentile and 252-day window unchanged** — only the seed's cost
  model. This is a principled correction of a demonstrable inconsistency.
  **What (A) changes (amendment 4):** post-reseed, fire rate is **selection, not
  signal** — resuming ~10% firing is *not* vindication; the always-write shadow
  arm's **delivered EV becomes the entire test** (2.5). A future ~10% fire rate
  may never be read as the candidate working.
- **(B) Recorded negative — the default.** If either (A) condition fails
  (crossing cost < $0.12 → the seed was not materially the cause; or the
  correction does not restore firing), the drift is not a seed artifact: **the
  VRP at 1-SD is not tradeable net of real costs**, recorded as a negative — the
  same cost-floor verdict Charter E reached. **On any ambiguity the default is
  (B); we do not reseed to force trades.** (B) is also the terminal outcome if,
  after resuming under (A), the shadow arm's forward EV fails to beat always-write
  and the drift null.

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

## 8. Bookkeeping (amendment 3) — the record is honest regardless of fork

- **Gate v2 is CLOSED with its scored entry regardless of outcome.** Whichever
  path we take, the current p90-gate-v2 instrument gets a recorded score:
  *"0/21 fire vs 21% predicted; diagnosed seed cost-model bias (backfill $0.06
  haircut vs live crossing)."* v2 does not get quietly overwritten by a fix — it
  is retired with its number, so the drift is a permanent part of the record.
- **Path (A) activates only after a FRESH BLIND fire-rate prediction is
  committed first.** Before any reseed enacts, a new blind prediction of the
  corrected gate's fire rate is logged — v3 predicts its own behavior before it
  runs, exactly as v2 did.
- **The n ≥ 30 executed clock RESTARTS under (A).** A reseeded gate is **v3, a
  new instrument, not a resumed one** — the executed-record count begins at zero
  under v3; nothing from v2 carries. The 12-month live-gate deadline for v3 runs
  from its own activation.
