# Pre-registration — Book Gate v2 (re-derived) · Charter B′

CONSTITUTION Art. 2.9 (v2.1, Amendment 1). Pinned before the first write under
this gate. Retires the flat 20%-of-width gate. Reviewed against the
self-referential trap in `RECALIBRATION_REVIEW.md` §1 — this document is written
to satisfy the five corrections required there.

## What this gate is — and is NOT

- **NOT a fairness test.** Ruin-avoidance lives entirely in the bounded
  partition (2.2: max loss = width − credit) and solvency sizing (2.4: ≤5%/
  position, ≤25% portfolio). Thin premium is at worst −EV, never insolvency.
  This gate does not decide whether a write is *fair*; the structure guarantees
  it cannot ruin us at any premium.
- **IS a pre-registered deployment-*timing* hypothesis:** "write the bounded bet
  when insurance is comparatively expensive." Whether that timing adds value is
  tested forward against the always-write control — it is not assumed.
- **NOT tuned to trade count or backtest P&L.** The threshold and window are
  fixed a priori by stated convention (below). The real distribution was
  computed only to *report* the cadence each principled choice implies (1.3: the
  historical window's budget is spent for selection).

## The gate (pinned)

Write the 1-SD put-credit spread on an underlying iff **both** hold:

1. **Relative (timing):** the day's `credit/width` (haircut) is ≥ the **90th
   percentile of the trailing 252-trading-day richness** for that underlying at
   the 1-SD strike distance.
   - *Window D = 252* — the standard IV-rank one-year lookback (a-priori
     convention, not fitted).
   - *Percentile N = p90* — top decile, "insurance meaningfully expensive,"
     the selectivity the thesis names. Chosen for faithfulness to the thesis,
     not because it hits a trade count (every candidate config reaches n≥30
     well inside the 12-month deadline — see cadence below — so decidability
     does not select the threshold).
2. **Absolute floor:** `credit/width` ≥ **0.08** (≈ the pooled median). A
   fairness backstop so a *locally* rich day in a dead-vol week is not written
   when it is *absolutely* thin. Comfortably above the ~2–3%-of-width round-trip
   cost floor.

**Delta-adjustment (review §1 obj. 3):** strike distance is held fixed at 1-SD,
so the short-put delta is ~constant (~16%) across days; comparing richness at a
fixed strike is already like-for-like. No separate, self-referential N(−sd)
adjustment is applied. (When/if a second strike distance is ever executed live,
it carries its *own* trailing distribution — never cross-compared.)

**Reference distribution:** seeded from the committed backfill richness series
(`reports/vrp-richness-backfill-1sd.json`, real Alpaca closes, Feb 2024→) so the
trailing window is populated from day one, then rolls forward on live/shadow
observations. Seeding calibrates "what counts as top-decile richness" — it is a
reference distribution, not a fitted parameter; the threshold (p90) and window
(252) are a-priori.

## Computed distribution & cadence (reported, not the selection criterion)

Pooled richness (haircut, 1-SD, 5 ETFs, n=2354): p50 6.8% · p75 10.3% ·
p80 11.3% · **p90 13.8%** · p95 16.6%.

| window / pctl | fire-rate | writes/mo (5 ETFs, pre-cap) | n≥30 in |
|---|---|---|---|
| D=63 / p75 | 33% | ~35 | ~0.9 mo |
| D=63 / p90 | 16% | ~17 | ~1.7 mo |
| D=252 / p75 | 40% | ~43 | ~0.7 mo |
| **D=252 / p90 (pinned)** | **21%** | **~22** | **~1.4 mo** |

Post the 2.4 solvency cap (concurrent-position limit) and the 8% floor, realized
executed cadence is lower — expected n≥30 in ~2–4 months, still well inside the
12-month live-gate deadline.

## The mandatory control (review §1 obj. 1)

The **shadow always-write arm** (`book/shadow.jsonl`, Art 3.2) continues
unchanged: it logs and resolves *every* day's spread regardless of this gate. It
is the control. The pre-registered live gate (`book/pre-reg-live-gate.md`) judges
whether this timing gate's executed record beats (a) always-write and (b) the
drift null. **If the timing adds nothing, the gate dies** — the always-write
resolved set also lets us read the full threshold-response curve forward, so no
single threshold is over-committed.

## Decidability & kill (review §1 obj. 2)

- n ≥ 30 within 12 months is a **decidability target, not a success metric**
  (always-write would maximize n; that is not the goal).
- If this *principled* gate still cannot reach n ≥ 30 by **2027-07-31**, the
  honest reading is the **finding** "no fair premium at tradeable frequency,"
  recorded as a negative — never a mis-specification to relax the gate around.
- All other kills unchanged: Book halts on any realized loss exceeding the
  defined width (2.6); the live-gate 5-point threshold governs paper→live.

## Activation

This pre-registration authorizes replacing the flat `RICHNESS_MIN` gate in
`scripts/vrp_harvester.py` with the rule above **only once this file is
committed** (mirroring the Charter-T data-collection rule). The shadow arm and
solvency sizing are untouched. Test suite must stay green.

## Status

Pinned 2026-07-31, pre-commit. Gate values fixed a priori; cadence reported from
real data. Not yet wired into the harvester (activation on commit).
