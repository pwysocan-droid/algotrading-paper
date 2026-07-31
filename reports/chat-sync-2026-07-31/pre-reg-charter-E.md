# PRE-REG — Charter E: Event Underwriting (venue study + hypothesis family E1)

Status: **DEAD at Stage 0 (2026-07-31).** The venue cost-floor study killed BOTH
sides of E1 on absolute cost (reports/event-venue-floor-2026-07-31.json;
epitaphs in dead-ideas.json; adjudication in decision-log 2026-07-31):
longshot-sell (<10¢) all-in 2–8¢ = 80–107% of price (fee floor dwarfs a 1–2¢
bias); near-certainty-buy (>90¢) all-in 3–5¢ = 1.5–2.5× a 2pp edge. The venue
fee is a takeout that exceeds any plausible bounded bias exactly where the bias
lives — the racing-takeout death on an order-book venue. No Stage 1, no charter
slot consumed. venues/kalshi/ is retained as a reusable instrument; the snapshot
cron's sunset is an open operator decision (recommended: stop). The kept text
below is the pre-death design, left for the record.

_Historical (pre-death) status:_ Stage 0 (measurement) built and corrected per
adversarial review (`RECALIBRATION_REVIEW.md`, Charter E addendum); it spent no
charter slot (operator-confirmed); admissibility Art 2.2 + 2.10 (v2.1) + 3.3.
The draft's "activates on commit" and its v1.0 §-citations were corrected.

Prior library: horse-racing market literature (favorite–longshot bias,
Griffith 1949 onward; late-money informativeness, Shin; crowd-correction
modeling, Benter). Racing is a **prior source, not a venue** — parimutuel
takeout (~15–20%) fails the fee floor by an order of magnitude. Priors
inform mechanism sections only; nothing here mines racing data.

---

## Stage 0 — Venue cost-floor study (the premise check; blocking)

Mirrors the crypto fee-floor measurement. No hypothesis in this charter may
be gauntleted before Stage 0 reports.

0.1. **Venues measured:** Kalshi (regulated, US-accessible) primary;
Polymarket observational-only unless/until access is resolved — its data
still serves calibration measurement.

0.2. **Measurements (read-only snapshots; ≥3×/day for ≥14 days; all markets
clearing a two-sided-quote liquidity screen):**
- effective **quoted spread** by price bucket (5¢ bands), tail-focused
  (<10¢, >90¢) where the bias prior lives;
- top-of-book depth by bucket (raw size units);
- all-in fee per contract from the **published fee schedule** (documented).
- **Struck as incompatible with the no-trading posture** (RECALIBRATION_REVIEW
  S0-2, and confirmed on build): executed-order fee *verification* and
  *time-to-fill* both require placing orders — deferred to a separately
  authorized order-placing stage. Snapshots cannot recover order lifetime at
  any cadence. Reported cost is therefore an **optimistic LOWER BOUND** (quoted
  spread + documented fee, no fill-cost).

0.3. **Kill criterion (corrected — absolute cost, not the racing magnitude):**
Charter E dies at Stage 0 if the tail-bucket **lower-bound** round-trip cost
already dominates any plausible *bounded* bias — i.e. cost so high no admissible
edge could survive. The racing favorite–longshot magnitude is a **prior for the
mechanism section only, never the Kalshi threshold** (S0-1): the on-venue bias
is what Stage 1 measures, so it cannot also be Stage 0's benchmark. Recorded in
dead-ideas with the venue numbers, no gauntlet. Prior expectation, stated openly:
the edge and the cost co-locate in the tails, and cost usually wins — Stage 0
will *likely* kill the charter, a cheap honest negative.

0.3a. **Venue-robustness assessment (added per Art 2.10b).** The Stage 0
deliverable also records the venue-failure tail — regulatory status, fund
segregation, historical void/dispute rate — the 100%-of-venue tail sized
≤5%/venue (2.4). A venue failing this is inadmissible regardless of spread.

0.4. **Deliverable:** `reports/event-venue-floor-{date}.json` (built:
`venues/kalshi/floor_report.py`) + a field-notes entry once the study resolves.
Est. operator time: ≤1 h. Decidability: ≤14 d of snapshots.

## Stage 1 — Hypothesis family E1: tail-calibration underwriting

Runs only if Stage 0 passes.

1.1. **Mechanism (named, per RECALIBRATION 3.1 discipline):** retail-
dominated thin venues reproduce the favorite–longshot bias — longshots
trade above true probability, near-certainties below. The counterparty is
recreational flow expressing opinions; no institutional corrector at this
liquidity. We are paid for bearing the boring side of a documented
distortion, not for predicting outcomes. This is underwriting under the
Book's question (Art 2.1).

1.2. **Rule sketch (exact params set after Stage 0 data):** buy contracts
priced in [SET: __–__¢] (near-certainty side) and/or sell in [SET: __–__¢]
(longshot side) on markets meeting liquidity screen [SET: depth/volume
bar], excluding [SET: named category exclusions — e.g. markets where we
hold a view, per Art 4.2 conflict gate]. Max loss per contract =
contractual (price paid / 100−price). Sizing per Art 2.4 solvency rules,
worst cases summed with no correlation credit.

1.3. **Calibration measurement first (zero-risk arm).** Before any paper order,
log every qualifying contract's reference price and resolution into
`book/event-shadow.jsonl`. Preconditions fixed by the review (must hold before
Stage 1 runs):
- **Per-bucket n, computed — not a blind SET slot** (α=.05, power=.80,
  RECALIBRATION_REVIEW): distinguishing even a *large* 2pp tail bias needs
  **~750 resolved contracts in that single 5¢ bucket** (≈750 at 5¢/3pp@10¢,
  ~1,600 at 10¢/2pp, ~3,400 for a 1pp bias). The premise is decidable only at
  that per-bucket depth; the shadow must pre-register the target **per bucket**
  plus a realistic time-to-accumulate, since tail events are rare (C-1).
- **Reference price defined a priori** (C-2): mid at a fixed lead time before
  resolution — not entry, close, or a time-weighted blend chosen later.
- **Selection/survivorship handled** (C-3): the liquidity screen correlates with
  the estimand (illiquid tails *are* the biased ones); voided/delisted markets
  are survivorship. Both are recorded and their effect bounded, or the curve is
  biased by construction.
- **Predicted effect size, named now and tied to cost** (C-4/C-5): state a
  concrete falsifiable bias magnitude that also **exceeds the Stage-0 cost
  floor** — a miscalibration smaller than cost is not an edge (the VRP lesson).

1.4. **Kill criteria (decidable):**
- Shadow: after n ≥ [SET: __] resolutions, if realized calibration curve
  is not distinguishable from the venue's implied curve at [SET: p __],
  the family dies — the bias doesn't exist here at measurable size.
- Paper: standard battery (Art 3.3 analogue) — net after measured costs vs
  the **always-take-the-tail-side dumb arm** (the drift-null analogue) and
  vs. a random-side control; n < 30 makes no claim; [SET: __]-month
  decidability deadline.

1.5. **Queued behind E1, not active:** E2 flow-shape residual (late
aggressive flow as resolution feature — Charter C overlap, needs public
flow data premise check); E3 correlated-market arithmetic violations
(structural, prediction-free; premise check = frequency count of
sum-violations exceeding costs). Listed so their budgets are ledgered
separately from day one.

## Budget & interaction rules

- Charter E consumes one of the two active slots on activation (§4.1);
  state which of B′/T yields or whether E queues.
- Statistical budgets are **per-venue ledgers**: Kalshi tests spend Kalshi
  budget only. Cross-venue replication is out-of-sample confirmation, never
  budget laundering.
- Venue adapter code lives under `venues/kalshi/`; own fetch cron, own DB
  file, single-writer preserved. No trader.db writes.
- Integrity: Art 4.2 gate extends to event positions automatically (they
  enter the registry's position history like any other); Art 4.3 forbids
  any venue rebate/affiliate arrangement.

## One-liners (on adoption)

- Racing is the library, not the venue. (prior §)
- The cost floor auditions every venue before any hypothesis does. (Stage 0)
- Sell the crowd its documented distortion; predict nothing. (1.1)
- The bias is checkable at zero risk before a dollar moves. (1.3)
