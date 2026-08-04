# SPEC v2.1 — Event-Market Tape & Duel Scoreboard

> **Status: SHELVED (2026-08-04) — not killed.** The §1.5 premise check
> fired the dormant reading: OUTCOME flow ~1–2/quarter vs the 8/quarter bar
> (P5a predicted 0–3/month and scored correct). §6.1 re-earn test FAILED —
> with E² not live, the duel's gate function has no consumer, and the weekly
> hour loses to §B (odd-lot) on expected value. **No fetch infrastructure was
> wired.** Reopen conditions, pre-named:
> - **(a)** a live E² intent forms — firewall path unchanged (a cost-net duel
>   verdict would still be required per §0.3/§A.6; the frozen pre-reg below is
>   the instrument-in-waiting); OR
> - **(b)** a venue lists *fast-resolving* markets intersecting the text
>   universe (e.g. earnings-beat contracts) — reopening then requires only
>   re-running §1.5 against the new catalog, no new spec.
>
> The frozen pre-regs (this spec, the addendum, P1–P5, the derived-comparisons
> patch) remain committed untouched — the paid-for asset. History below.

Status: **DRAFT v2.1 — externally drafted (chat, 2026-08-03). PATCH-R2
applied (PATCH-1: CX-1; PATCH-2: §1.5 intersection check). All three R2
conditions addressed; sent with addendum v2 for formal closure of
§2.5(a). Step zero before commit: diff against repo HEAD; grep-verify
every citation.** Supersedes SPEC v2 (draft, never committed).
Companions: `REVIEW-RESPONSE-R1.md`, `addendum-w3-and-queue-stubs-v2.md`.

> **Committed 2026-08-03 as a DRAFT.** Open `[SET]` items at commit
> (documented, not hidden): hard cap resolves to **5 GB** (df measured
> 30 G free; min(5, ½·30)); power sidedness is the operator's call
> (reviewer rec: **1,050 two-sided**); §2.2 needs the ≤2,000 enforcement
> rule (tighten the liquidity floor, versioned/logged — never truncate
> the market list by fetch order). Passed the R1→R2→PATCH adversarial
> cycle (reviews/spec-event-market-tape-review*.md).

Proposed location: `data/event-markets/SPEC.md`, adapter code under
`venues/{kalshi,polymarket}/`.

Admissibility basis: infrastructure under the CONSTITUTION Art 3.2
pattern (a collecting tape, like the Layer-2 funding/OI feed), NOT a
charter activation. Consumes no charter slot (REC §4.1), no statistical
budget, no capital.

Citation convention: constitution articles cited **Art N.n**;
RECALIBRATION sections cited **REC §N.n**. No bare 4.1 anywhere.

---

## 0. Structure of this spec

0.1. **W1 — the event-market tape (curated).** Price/depth/resolution
data as (a) the crowd benchmark Charter T text signals must beat
**(conditional on §1.5)** and (b) Charter C positioning input.

0.2. **W2 — the duel scoreboard (subordinated to W3).** The calibration
ledger exists *only as the scoring apparatus of W3*, the LLM forecast
duel (addendum §A) — engine Brier vs venue Brier is mathematically
unscoreable without venue mids, resolutions, and per-bucket outcomes.
The venue's own calibration curve is a byproduct of scoring the duel,
not a separable deliverable.

0.3. **The E² firewall.** Any future E² pre-reg must cite (a) the
Charter E kill, (b) a materially different premise argued in writing,
and (c) **the scored outcome of the W3 duel (addendum §A.6) under its
cost-net reading — never the raw calibration curve.** A confirmed gross
bias is pre-registered here as expected and non-actionable (see P1);
only the duel's net verdict is admissible E² evidence. Deferral of
collection was rejected because the data is forward-only: resolutions
not logged are gone permanently — the program's answer to
evidence-staging risk is pre-registration, not data abstinence.

0.4. Nothing in this spec places, papers, or shadows an order on any
venue. The Charter E Stage-0 kill stands as recorded in dead-ideas.

## 1. Venues & the intersection premise check

1.1. **Kalshi** — regulated, US-accessible, Stage-0 familiarity. The
kill was about trading costs; measurement is cost-free.

1.2. **Polymarket** — observational. Log fee-schedule version in force
alongside every snapshot (QCEX-era vs prior), so later cost analysis
knows which regime each row lived under.

1.3. **ForecastEx** — phase 2, pending IBKR-gateway API assessment.
Adapter directory stubbed; nothing blocks on it.

1.4. Per-venue everything: own adapter, own DB file, own fetch cron,
single-writer preserved. No trader.db writes. Cross-venue joins are
read-only at analysis time.

1.5. **Text-intersection premise check (PATCH-2; blocking for the
Charter T interface, NOT for the duel).** Before any W1 adapter code is
built: sample the trailing [SET: __ months, suggest 6] of the Charter T
8-K archive (or, if the archive is younger, the full EDGAR 8-K flow for
the trailing window); classify filings by event type; match against
current Kalshi and Polymarket catalogs for a LIQUID counterpart market
(liquidity floor per §2.2). Report the intersection as events/month
with a tradeable crowd benchmark.

**Pre-named readings (against the GOVERNING column only, per below):**
- governing-column intersection ≥ bar → §5 (Charter T interface) is
  live as specced;
- < bar → §5 goes DORMANT (not deleted): the curated universe collapses
  to the duel screen (addendum §A.3) alone, and the Charter T benchmark
  rationale re-activates only when a text source with measured
  intersection exists (macro-print text, governance proposals — each
  requiring its own intersection check). The tape survives on its
  primary consumer, W3.

**Class split (pre-named; PATCH 2026-08-03).** The intersection is
counted and reported in two columns, never blended:
- **OUTCOME** — company-specific, event-resolving markets (the thing
  happens or doesn't) passing the liquidity floor;
- **MENTION** — earnings-call mention markets (the phrase is said or
  isn't) passing the liquidity floor.

**Governing class: OUTCOME** (pinned by the operator 2026-08-03, as the
class Charter T's first-generation hypotheses will consume: text→world,
not text→language). The §5 live-vs-dormant reading is taken against the
OUTCOME column ONLY. The pin was committed before the count ran so the
verdict cannot be argued from whichever column favors it afterward.

- **P5a (OUTCOME) — committed prediction: 0–3 /month** (near-zero
  off-season). This is the governing column.
- **P5b (MENTION) — committed prediction: tens /earnings-quarter**
  (near-zero between). Conjunction caveat, stated: listed × LIQUID ×
  8-K-relevant — the liquidity floor is the unmeasured conjunct; the
  catalog may be broad while tradeable depth is narrow.

**Bar (committed): 8 qualifying OUTCOME events per earnings quarter**
(≈ 2.5/month sustained) — the minimum flow letting a Charter T
hypothesis reach n ≥ 30 scored events within 12 months of activation
(8/qtr × 4 = 32/yr ≥ 30). §5 live iff measured OUTCOME flow ≥ this bar.
Note P5a (0–3/month ≈ 0–9/qtr) straddles the bar, leaning dormant — the
prediction itself expects §5 near the dormancy line.

## 2. What is collected (curated universe + disk budget)

2.1. **Market catalog** (daily, FULL population, metadata only): venue,
market_id, category, question text verbatim (Charter T fuel),
listed/close/settle timestamps, resolution source, fee-schedule version.
Metadata rows are small; the catalog stays population-complete so the
curation filter (2.2) is auditable against the whole universe.
**Storage mode is UPSERT + delta log, never daily append** — appended
daily, the full-population catalog alone is ~88 GB/yr (800k × 300 B ×
365) and kills the box in weeks; as an upsert table it is ~0.24 GB
flat. This line is load-bearing (arithmetic logged 2026-08-03).

2.2. **Curated snapshot universe.** Price snapshots are collected ONLY
for markets passing the curation screen:
- intersects the Charter T text universe [SET: category list — subject
  to the §1.5 reading], OR is in the W3 duel screen (addendum §A.3);
- meets liquidity floor [SET: e.g. volume > $__ or listed > __ h];
- passes **rule CX-1** (below — shared with addendum §A.3).
Curation rules are versioned; a rule change opens a new universe
version, never silently reshapes the old one.
**Target-size enforcement (reviewer catch, 2026-08-03):** if the curated
set exceeds the §2.4 target (≤ 2,000), tighten the liquidity floor —
versioned and logged — until |curated| ≤ target; NEVER truncate the
market list by fetch order (that is the silent-pagination-cap bug in a
budget's clothes). The liquidity floor is the honest knob.

> **CX-1 (spec-local operator-conflict exclusion; no constitutional
> basis claimed — candidate for promotion at the next amendment
> window):** excluded from the curated universe and the duel screen is
> any market where the operator holds a position, a personal stake, or
> a previously stated view. Rationale: the duel's validity requires
> engine forecasts uncontaminated by operator views leaking through
> prompt construction or market selection; and no registry position may
> create an incentive to shade collection or scoring.

2.3. **Price snapshots** (curated universe only): best bid/ask, mid,
last, top-of-book depth both sides, cumulative volume. Cadence: [SET:
suggest 60 min baseline, 5 min inside final 24h]. Full price curve
across all buckets within the curated set — tails are a focus, not a
filter.

2.4. **Disk budget (values computed 2026-08-03).** Snapshot row ≈
**300 B** (JSON-lines, conservative; SQLite ≈ half) × curated markets
**≤ 2,000** open at a time × cadence (60-min baseline, 5-min final
24h, ~30 d avg lifetime assumption) ⇒ ~65,600 rows/day ⇒ **~7.2 GB/yr
raw accumulation; ~0.5 GB steady-state with the compression rule below
— the retention policy is load-bearing, not optional** — against the
38 GB box currently running ≥ 90% twice this month. Hard rules:
- measured first-week disk rate is reported and sets the retention
  policy before week 2; the ~30 d lifetime assumption is re-measured
  from the first month's catalog;
- hard cap **5 GB** (df measured 30 G free 2026-08-03; rule = min(5 GB,
  half of measured free) — the cap derives from FREE space, not box
  size; re-derive if the box baseline shifts); breach = collection
  pauses and flags, never silently drops rows;
- snapshots older than **30 d** for RESOLVED markets compress to
  closing-window-only summaries (~2 KB each; the calibration ledger
  needs the closing window; the full intraday curve is Charter T/C
  material and ages out per retention policy).

2.5. **Resolutions**: outcome, settle timestamp, dispute flag
(Polymarket UMA disputes logged explicitly — settlement-venue tail
data). Resolutions are never aged out; they are the scoreboard.

2.6. **Derived nightly** (read-only jobs):
- duel scoreboard rows (W3): engine forecast vs venue mid vs outcome,
  per addendum §A.4;
- calibration ledger: closing-window price bucket (5¢ bands) vs
  realized outcome — computed as W3 scoring input per 0.2;
- **sum-violation counter, funnel-costed:** a violation counts ONLY if
  capturable — gross gap minus BOTH venues' spread at logged depth,
  BOTH fee schedules, flagged for settlement-tail asymmetry. Gross
  (uncapturable) violations are logged separately as color, never as
  the P2 statistic.

## 3. Blind pre-registrations

3.1. Committed before the first fetch runs; frozen on commit; revisions
logged, never edited in place.

- **P1 (cost-net tradeable miscalibration).** The Charter E kill was
  "bias < cost," not "no bias." P1 predicts the NET number: tail
  miscalibration minus each venue's measured all-in round-trip cost in
  that bucket. Operator's committed prediction: [SET — given Stage-0,
  the honest prior is ≈ 0 net on Kalshi; Polymarket-US and ForecastEx
  are genuinely open]. A confirmed GROSS bias of literature magnitude
  (1–5¢) is pre-registered as expected and, alone, actionable-nowhere
  (0.3 firewall).
- **P2 (capturable sum-violations, funnel-costed):** predicted
  frequency of NET-capturable violations per 2.6: [SET: __ per week —
  conjunction discipline: two spreads × two fees × two settlement
  tails, simultaneously; the registry's own lesson says predict ≈ 0
  and let the data argue]. The funnel (gross → spread-surviving →
  fee-surviving → capturable) is reported at each stage.
- **P3 (dispute rate):** predicted UMA-disputed share of Polymarket
  resolutions: [SET: __%] — prices the settlement-venue tail later.
- **P4 (the duel):** lives in addendum §A.5, committed the same day as
  this spec.
- **P5 (intersection):** lives in §1.5, committed the same day.

3.2. **Power statement (values computed 2026-08-03).** n < 30
resolutions per bucket makes no claim (small-sample quarantine), AND no
tail-calibration claim is decidable before the power bar: for a 2pp
effect at a 5% tail base rate, 80% power, **n ≈ 1,050/bucket two-sided
or n ≈ 850/bucket one-sided** [SET: pick one and state the principle —
one-sided is defensible because P1 pre-registers the direction
(literature prior: longshot overpriced); two-sided is bulletproof;
reviewer rec = two-sided 1,050]. A 3pp effect needs ~380. The 90-day
review (§6) reports accumulated n against the pinned number, not against
30. Accumulation estimate: at 2,000 curated and 15–20% of resolutions
landing in a tail bucket, n = 850 arrives in ~2–4 months; **if §1.5
sends §5 dormant and the universe collapses to a duel-only screen, this
timeline stretches proportionally** — reported at review as a finding,
not engineered around.

## 4. Correctness assertions

Nightly, failing loudly (Art 4.1: correctness outranks liveness):

- every price in **closed [0, 1]**, settled markets excluded from the
  open-market assertion (settled prints at exactly 0/1 are legitimate);
- every Yes+No within venue-documented bounds, per fee-schedule version
  in force at snapshot time;
- every resolved market has exactly one outcome; none resolves before
  its close timestamp;
- row-count deltas within a **calendar-aware** band (weekday/weekend/
  holiday profiles per venue — the EDGAR Saturday lesson);
- **completeness, per-denominator:** (a) CATALOG completeness: fetched
  market count vs the venue's own reported total (full population; the
  silent-pagination-cap lesson, named); (b) SNAPSHOT completeness:
  snapshot coverage vs the versioned curated-universe list;
- schema drift raises a flag, never auto-adapts;
- **fee-schedule drift is a MANUAL check, labeled as such:** Kalshi's
  fee is a formula, not an API field — the nightly job asserts only
  "fee-schedule version string unchanged"; verifying the actual
  schedule is a [SET: monthly] operator checklist item.

## 5. Charter T interface (conditional on §1.5)

5.1. W1 exports a read-only event calendar view (upcoming settlements,
current implied probability) consumable by Charter T hypotheses. Any
consuming spec names its mechanism per Art 0.2(a): who is forced to act
on the text, and why slower than us — with the venue price as the crowd
benchmark the text signal must beat.

5.2. No Charter T hypothesis may trade an event venue under this spec;
the venue price is a feature/benchmark only.

## 6. Review & stop condition

6.1. Review at 90 days from first fetch: data quality report; disk rate
vs 2.4 estimate; P1–P3/P5 accumulation vs the §3.2 power number
(explicitly NOT scored if underpowered); W3 duel accumulation per
addendum §A.4; operator time vs estimate [SET: __ h/week, suggest ≤ 1].
If §5 is dormant per §1.5, the review explicitly re-asks whether a tape
whose sole consumer is the duel still earns its maintenance.

6.2. Stop condition (pre-named): maintenance > [SET: __ h/week] for two
consecutive months, OR disk cap breached twice, OR a venue's API terms
forbid collection → the affected feed stops, reason logged. A tape that
costs more attention than it earns is a liability.

---

## One-liners (v2.1)

- The ledger is the duel's scoreboard, not the dead charter's arm. (0.2)
- Only the duel's NET verdict — never the raw curve — can argue E². (0.3)
- Measure the conjunction you assumed: text × liquid market was never
  counted. (1.5)
- Curate the universe; the mechanism sharpens and the disk survives. (2.2)
- Grep applies to corpses. (CX-1 provenance)
- Predict the NET number; the gross bias is expected and buys nothing. (P1)
- A violation isn't real until it survives its own funnel. (2.6, P2)
- Assert each completeness against its own denominator. (4)
- Quarantine is a floor; power is the bar. (3.2)
