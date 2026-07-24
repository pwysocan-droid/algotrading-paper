# Pre-registration — Funding-Carry (Delta-Neutral Basis)

Book candidate #1 · CONSTITUTION Article 2.8 · pre-registered before any
position. Forward-only; no backtest verdict is admissible (1.3, 2.5).

## Structure (2.2 partition)

Delta-neutral basis carry: **long spot X + short perpetual X** of equal
notional. Funding accrues on the short leg when funding is positive; the
spot long hedges price. Directional P&L ≈ 0 by construction; the return is
the funding stream minus the cost of maintaining the hedge.

Naked funding collection (short perp only) is **inadmissible** — unbounded
price loss, fails 2.2. Only the hedged basis form is admitted.

## Structural worst case (2.3 — mechanism, never history)

The dominant tail is **not** price (hedged) or funding (small, capped per
interval). It is **venue failure**: exchange insolvency, withdrawal halt,
or ADL during a cascade traps or seizes the on-venue capital while the
position cannot be unwound. Mechanism-defined magnitude:

> **structural worst case = 100% of capital on that venue**
> (time-to-flat = ∞ on insolvency — you cannot exit a frozen venue)

Secondary, dominated tails (priced but smaller): basis gap during forced
deleveraging (bounded by arbitrage + exchange liquidation mechanics);
adverse funding flip (bounded by the exchange's per-interval funding cap ×
hold). On-chain perp venues add a **smart-contract-failure** total-loss
mode — another 100%-of-venue tail, priced identically.

Estimating how *often* a venue fails is forbidden (2.3). We price only the
magnitude (100% of venue capital) and the *implied breakeven frequency*.

## Solvency sizing (2.4)

Worst case = 100% of on-venue capital ⇒ the per-position cap binds directly:

- **≤ 5% of Book capital on any single venue.**
- **≤ 25% of Book capital across all venues combined**, worst cases summed
  with no correlation credit (venue failures are correlated in a systemic
  event — the FTX-contagion shape — so 25% is the true maximum at-risk).

This is the FTX lesson as arithmetic: the honest tail forces small
per-venue allocation, mechanically, before any position is opened.

## Fair-compensation test (implied breakeven frequency)

Never estimate the failure frequency. **Compute** the frequency the premium
already pays for and judge it structurally:

> implied breakeven frequency = annualized net carry ÷ 100% (structural loss)

Example: 8%/yr net delta-neutral carry ⇒ breakeven at **one total-venue-loss
per 12.5 years**. The premium is "fairly paid" only if that breakeven is
structurally survivable for the *specific venue*. Ecosystem base rates
(Mt Gox, QuadrigaCX, FTX, Celsius) run far hotter than 1/12.5yr on weak
venues — so this test **admits carry only on the most robust venues**
(regulated, audited, US-domiciled) and rejects the high-funding sketchy
venues where the carry is larger but the breakeven is not survivable. That
asymmetry is the constitution working: it steers toward paid-less-but-survive
and away from paid-more-but-ruin.

## Kill criterion (2.5, 8.3)

Forward-only, decidable within a stated forward window per venue:
- **Kill** if realized net carry (after fees, adverse funding, basis
  slippage, and hedge maintenance) fails to clear BOTH the drift null AND
  the implied breakeven frequency margin at the forward horizon.
- **Book-level halt** (2.6) if any realized loss exceeds its computed
  structural bound — the bound was mis-specified, invalidating all bounds.

## Execution feasibility — SURFACED PRE-POSITION (honesty, 3.3 spirit)

Delta-neutral carry needs a **perpetuals venue**; our funded live account
(Alpaca) is **spot-only** — no retail perps. US retail perp access is
constrained: Binance blocks US perps; on-chain venues (dYdX, GMX, Hyperliquid)
are accessible but add the smart-contract 100%-tail above. So candidate #1
is **pre-registered but BLOCKED on venue**. Resolutions, in order of
constitutional cleanliness:
1. A US-accessible, robust perp venue whose failure breakeven is survivable
   (to be identified; most fail the fair-compensation test).
2. An on-chain perp venue, with the smart-contract tail explicitly priced
   into the 100%-of-venue worst case (raises the required carry).
3. **Fall back to a spot-only bounded premium as the actual first Book
   position** — e.g., a defined-risk covered structure on the Alpaca spot
   account — which is executable today and admissible under 2.2. This is the
   likely true #1; funding-carry stays registered for when a venue clears.

## Status

Pre-registered, VENUE-BLOCKED. No position opened. This document is the
standing record that the constitution was applied to the first candidate
and produced (a) admission only as delta-neutral, (b) a mechanism-priced
100%-of-venue tail, (c) solvency-forced ≤5%/venue sizing, (d) a
fair-compensation test that rejects most venues, and (e) an honest
execution gap surfaced before any capital moved.
