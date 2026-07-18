# Literature priors — external evidence channel (compiled 2026-07-18)

Source: claude.ai research-mode survey (Run E of the elicitation
program), 2020-present academic + practitioner evidence. Full text in
the operator's session; this file keeps the actionable priors.

## Convergent with our internal measurements (independent confirmation)
- "Real statistical predictability, essentially no documented NET edge
  from a US retail spot seat at hours-to-days horizons" = our ceiling
  study (gross +0.02-0.63%, net <=0) from a disjoint method.
- Alpaca realized round-trip ~0.55-0.7% = our assumption + measured
  venue spreads. Kraken-tier maker fees named as the only fee path
  under ~0.6%.
- Largest coins show mild daily MOMENTUM (small-coin daily reversal is
  an illiquidity artifact, per its own authors).

## New priors we did not have
1. SLIPPAGE IS VOLATILITY-CONDITIONAL: costs are worst exactly when
   signals fire. Our constant 0.05% slippage assumption understates
   realized costs for event-triggered entries; the factorial cost
   experiment must include calm-vs-volatile windows as a factor.
2. THE SLOW BAND IS OPEN: published persistence at 1-8 WEEK holds
   (slow beats fast in BTC; a 2026 study rules AGAINST 24h as the
   sweet spot). Multi-week holds amortize the fee floor to near
   irrelevance (~0.6% per RT over weeks) and fit our 5-slot/$1k book.
   Our archive cannot measure this band (n runs dry past 3d) — the
   literature is the only instrument that reaches it, and it points
   there.
3. FUNDING SIGNALS ARE RISK PREMIA, NOT FREE ALPHA (BIS WP 1087):
   funding carry is crash-risk compensation clawed back in
   liquidation events; directional funding-extreme signals are
   practitioner folklore with zero peer-reviewed OOS support. Layer-2
   designs on the funding tape must engage this prior explicitly.
4. McLean-Pontiff decay (~50% post-publication in equities) likely
   bites harder in crypto; NO crypto intraday effect has published
   post-publication confirmation. Treat every published effect as
   half-sized and dying.

## Program implications
- The admissible-territory map gains a second region: alongside
  "24h + maker" (internally measured), "1-8 week holds" (literature-
  supported, internally unmeasurable). A literature-prior candidate
  (slow BTC/ETH momentum, weekly rebalance, maker entries) is queued.
- Cost experiment: add volatility-regime factor.
