# Pre-registration — Variance-Risk-Premium Harvester (Candidate #1)

Book candidate #1, executable form · CONSTITUTION Art. 2, 0.3, 0.4 ·
pre-registered before any position. The machine: an *underwriter with a
brain* — sell the insurance the market overpays for, cap every loss in
advance, and use LLM information-synthesis to decide **when the premium is
rich and when to refuse to write the policy.**

## The thesis (why this and not price prediction)

Options are systematically overpriced: implied volatility exceeds
subsequently-realized volatility on average (the variance risk premium — the
most persistent, most-documented, retail-accessible edge there is).
Sellers are paid for bearing the risk buyers overpay to shed. This is
compensation for risk transfer (Art. 2.1), not a prediction of price — the
one return shape our own evidence endorsed (low-vol delivered its risk
thesis; 1.2).

## Structure (Art. 2.2 — bounded by construction)

**Defined-risk credit spreads** on liquid, tightly-quoted, optionable
underlyings — sell a nearer option, buy a farther one of the same type and
expiry. Forms: put-credit spread (harvest downside VRP), or iron condor
(both sides) when the surface is symmetric.

> **max loss = (strike width − net credit received), CONTRACTUAL and known
> at entry.** Fully bounded → admissible. Naked short options (unbounded)
> are inadmissible, always.

## Tail pricing (Art. 2.3 — mechanism, not history)

The structural worst case is the spread's defined max loss, realized if the
underlying blows through both strikes and stays there to expiry:
`worst_case = width − credit`, per contract, independent of how far the
underlying moves. No frequency estimate, no sample estimate. Assignment/
early-exercise and pin risk are operational, not additional loss beyond the
width. Broker/venue failure (Alpaca) is the residual 100%-of-collateral
tail, sized under 2.4 like any venue.

## The LLM stand-aside rule (the differentiator — Art. 0.3)

Dumb premium-selling blows up by writing insurance into a known hurricane.
Before every position the LLM reads the information surface and REFUSES to
write if any of these is true within the tenor:
- a scheduled catalyst on the underlying (earnings, FDA, major product/legal
  date) inside the expiry;
- a scheduled macro shock in-window (FOMC, CPI, major elections) for
  index/beta-heavy underlyings;
- an active, credible tail-risk narrative in the news/sentiment surface
  (liquidity event, contagion, sector blowup) that the static IV rank does
  not yet reflect.
Selection (where the premium is rich): high IV-rank names/regimes, liquid
tight spreads, no stand-aside trigger. This context judgment — not the
spread mechanics — is where the LLM earns its keep and is the decaying
arbitrage speed must capture (0.4).

## Sizing (Art. 2.4) & the capital reality

Per position max loss ≤ **5%** of Book capital; sum of open max losses ≤
**25%**, no correlation credit. **Honest constraint:** at $200 Book capital,
5% = $10 max-loss per position — too small for a real equity-option spread.
Consequences, in order:
1. **Paper-first (fast loop, zero risk, starts now).** Run the full
   machine — LLM selection + stand-aside + defined-risk spreads — on the
   Alpaca PAPER options endpoint, forward, immediately. This validates the
   loop and the stand-aside judgment live-but-riskless while capital and
   options-approval resolve (0.4: buy information now, cheaply).
2. **Scale to live** only when (a) Book capital is set at a level where a
   properly-5%-sized spread is expressible, AND (b) Alpaca options approval
   is granted, AND (c) the paper forward has cleared its kill.

## Fair compensation & kill (Art. 2.5, 6.3)

- **Fair compensation:** the credit collected must exceed the loss implied
  by the strikes' own assignment odds by a margin — write only when IV-rank
  makes the premium rich enough that the implied breakeven is survivable.
  Judged by the position's implied breakeven, never an estimated crash rate.
- **Forward kill:** paper-forward then live; kill the candidate if realized
  net (credits − losses − costs) fails to beat a passive short-premium
  benchmark AND the drift null over the forward window; **Book halts** (2.6)
  if any realized loss exceeds the defined width (bound breached).

## Status

Pre-registered. Next build (mine): the paper execution loop — Alpaca paper
options wiring, the LLM selection+stand-aside step, defined-risk spread
placement, and the forward ledger. Live is gated on capital sizing +
options approval + a survived paper kill (all surfaced now, pre-position).
Speed target: paper loop running in days, not a backtest in months (0.4).
