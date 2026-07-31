# Pre-registration — Live-Trading Performance Gate (Candidate #1, VRP)

Pinned before any live position. CONSTITUTION Art. 2.5, 6.3. This is the
number that decides paper → live. It may not be weakened while the paper
record is open (6.1). Operator owns funding + options approval; this document
owns the performance bar.

## The gate — all five must hold, judged on the CLOSED paper record

1. **Volume — n ≥ 30 closed spreads.** Below 30 the record is quarantined:
   neither pass nor fail (2.5). Executed paper trades and shadow-resolved
   trades (Art 3.2) both count toward evaluating the decision rule; only
   *executed* closed spreads count toward the n≥30 P&L gate.

2. **Net-positive after modeled costs.** Cumulative realized net (credits −
   buyback debits − commissions − modeled bid/ask crossing) > 0.

3. **Beats the dumb benchmark.** Net must beat a **passive always-write arm**
   (same spreads, gate only, no LLM stand-aside) over the same window. This is
   the sole test that the stand-aside *judgment* earns its keep; if it can't
   beat always-write, the LLM layer is decoration and is cut, not shipped.

4. **Beats the drift null.** Net must beat being long the underlying basket
   over the same window (2.5 mandatory drift null). Selling puts makes money
   in up-markets for free; the edge must survive that subtraction.

5. **Bound integrity + fair compensation.**
   - **Zero bound breaches:** not one realized loss exceeded `width − credit`.
     A single breach halts the Book (2.6) — the risk math was wrong, which is
     disqualifying regardless of P&L.
   - **Loss-rate under breakeven:** realized loss frequency ≤ the premium-
     implied breakeven frequency (`credit ÷ width`, a computed number — never
     an estimated crash rate), with margin.

**Green light = (1)…(5) all true.** Only then may live be armed, and only
after: options approval granted, Book capital funded to a level where a
5%-sized spread is expressible (~$10k floor; $50–100k to size properly), and a
single 1-contract live smoke test confirms the order/close plumbing.

## Kill (the symmetric commitment)

- **Candidate retired** (recorded negative, not a bug) if, by the forward
  deadline **2027-07-31** (12 months) OR after 3 consecutive fair-compensation
  failures at the position level, the gate is not cleared.
- **Book halts** immediately on any bound breach (2.6), independent of the above.

## Why these and not a Sharpe target

A Sharpe/return target over a benign window is the tail-flattering number this
whole program was built to distrust (1.4, 2.3). The gate instead demands the
edge beat *two nulls* and that the *mechanism* (the bound) never fail — a
survivable, honest bar, not an impressive one. The expected reward if cleared
is modest by design: ~5–8%/yr on Book capital, roughly half of it T-bill yield
on idle collateral (see decision-log). Double-digit book returns would signal a
breached solvency cap or an under-priced tail, not success.

## Status

Pinned 2026-07-31. Paper record open; executed n = 0 (premium thin — see
reports/vrp-richness-backfill.json: the 20% gate clears only ~2–3% of days at
1-SD-OTM). The shadow arm (book/shadow.jsonl) is now accumulating the decision
rule on ~250 days/yr to reach a statistically meaningful read in months.
Gate-richness recalibration (fair-pay vs arbitrary 20%) is the open design
question feeding this pre-registration.
