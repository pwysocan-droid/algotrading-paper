# RECALIBRATION — Amendment 1 to the Constitution (v2.1 proposal)

Status: **ADOPTED IN CORRECTED FORM, 2026-07-31** (per Art **6.1**, not "8.1" —
see review). Core scope (bound 0.2, add 2.9/2.10) is now in CONSTITUTION.md
v2.1. Corrections and rejections are recorded in `RECALIBRATION_REVIEW.md` and
`decision-log.md`: §2.9 reframed as a timing hypothesis (not a fairness test),
citations fixed (Art 8→6, 0.3→0.2), **Charter S / the Service rejected**,
Charters E/C deferred behind the B′+T opening pair.
Proposed: 2026-07-31. Author: operator + Claude session (chat, not code).
This file lives at the registry root next to `CONSTITUTION.md`. On adoption,
`CONSTITUTION.md` is amended per §2 below and `decision-log.md` gains an entry
pointing here.

---

## 1. The finding this amendment stands on

1.1. The ~43 falsifications established a *bounded* negative: no edge in
**price-derived signals** (OHLCV and its transforms), in **two liquid
markets**, at **tested horizons**, at retail cost structure. That is a
measured ceiling on **one input space**.

1.2. Constitution Art 0.3 generalized this to a global prohibition:
*"any proposal that requires the program to out-predict an efficient market
is out of scope by constitution."* That generalization exceeds the evidence.
The registry contains zero tests of non-price inputs (text, filings,
governance events, positioning/crowd data, event contracts). A verdict about
candles is not a verdict about everything.

1.3. Separately, the Book's richness gate (credit ≥ 20% of width, vs a
market that prints 12–13%) demands that the market *overpay* relative to
fair — which is mispricing-hunting reintroduced as prudence, and which
guarantees n = 0 and therefore permanent undecidability of the Book's own
pre-registered live gate. By our own standards this is a decidability
failure, not safety.

1.4. Nothing in this amendment touches the epistemics. Pre-registration,
kill criteria decidable in advance, forward-only evaluation, drift nulls,
premise checks, cost floors, n < 30 makes no claim, small-sample quarantine,
the integrity regime — all carried over in full force, unamended. **The
engine is the asset; this amendment changes its fuel, not its brakes.**

## 2. Amendments to CONSTITUTION.md

2.1. **Art 0.3 is rewritten** from a global prohibition to a bounded one:

> 0.3 (v2.1). This program does not hunt mispricing **in price-derived
> signals on liquid instruments** — that space was measured empty (~43
> falsifications, plus the ML ceiling study). Hypotheses drawing on input
> spaces the registry has never tested (text, events, positioning, contract
> structure) are in scope, provided they enter through the full gauntlet
> discipline of Art 2.5/3.3 analogues: pre-registered, forward-only,
> premise-checked, with a decidable kill criterion.

2.2. **Art 2 gains 2.9 (Book gate re-derivation):** the flat 20%-of-width
gate is retired as arbitrary. The replacement gate is derived from the
market's own distribution: the Book writes when the day's credit/width sits
at or above the **[SET: __th] percentile of the trailing [SET: __d]
distribution** for that underlying and strike-distance, delta-adjusted (per
the busy-parameter lesson in field-notes). The bounded-loss partition
(2.2), solvency sizing (2.4), and Book-level kill (2.6) remain the safety
mechanism — safety lives in the *structure*, not in demanding overpayment.
Purpose: the executed record must be able to reach n ≥ 30 within the
12-month live-gate deadline, or the gate itself was mis-specified.

2.3. **Art 2 gains 2.10 (event contracts admissible):** binary/defined-
outcome contracts (regulated event markets, defined-risk options
structures around named events) have contractually computable worst cases
and are therefore admissible under the *existing, unamended* partition of
2.2. No structural change; this clause merely records the reading.

## 3. New charters (the successor generators — forward-only fuel)

Each charter below is a *permission*, not a plan. Each activates only via
its own pre-registration file under `book/` or `foundry/`, with the full
battery. Sequenced; do not start all at once (see §4).

3.1. **Charter T — text-native signals (r005 lineage).** The LLM reads
what no retail participant systematically reads: earnings-call language
deltas, 8-K/filing events, crypto governance proposals, tokenomics/unlock
calendars. Hypotheses must name the mechanism (who is forced to act on
this information, and why slower than us), the horizon, and the cost model.
New data source ⇒ fresh statistical budget, but **forward-only from day
one** — no adaptive mining of a fixed text archive without pre-registered
splits.

3.2. **Charter B′ — the Book, actually writing.** Under the re-derived
gate of 2.9. First target: resume the VRP harvester with the percentile
gate; the shadow arm continues unchanged as the control.

3.3. **Charter E — event underwriting.** Defined-risk structures around
scheduled, decidable events (earnings, macro prints, protocol upgrades,
listed event contracts). Admissible per 2.10. The question inherits the
Book's framing: *am I paid fairly to bear this bounded outcome risk?* —
now extended with: *does a text-reading machine set that price better than
the crowd on thin venues?*

3.4. **Charter C — crowd/positioning data (crypto).** Funding extremes,
open interest, liquidation maps, narrative velocity: data about
*participants*, which OHLCV never contained. Note the standing literature
prior (funding = crash-risk premium, not free alpha) — any funding
hypothesis must be framed as underwriting, not prediction, or explicitly
argue why not.

3.5. **Charter S — the first autopsy ships.** The Service publishes its
first pre-registered autopsy within [SET: __ days] of this amendment's
adoption or writes up why not. Drafting integrity clauses is not the
radical act; publishing is.

## 4. Sequencing & budget

4.1. **Two active charters maximum** at any time. Proposed opening pair:
**B′** (unblocks the existing machine; smallest lift) + **T** (the
original thesis, finally tested). E and C queue behind whichever finishes
or dies first. S runs on calendar time, not capital, and doesn't count
against the two.

4.2. Every charter pre-registers its own program-level kill in the spirit
of Art 8.3 before its first live/paper action.

4.3. The operator's time is the scarcest capital. Each charter's pre-reg
states its expected hours/week and its decidability date.

## 5. What this amendment refuses

- No loosening of 2.2 (partition), 2.4 (solvency), 4 (integrity) — the
  entrenched articles are untouched.
- No return to in-window mining of the spent OHLCV archive.
- No "just this once" verbal waivers — Art 8 governs this document too.
- No conflating this recalibration with impatience: the predecessor's
  willingness to stop is why this document exists; the successor's virtue
  is willingness to **start where the evidence hasn't spoken**, under the
  same discipline that made stopping trustworthy.

## The one-liners (append to the constitution's list on adoption)

- The verdict was about candles, not about everything. (1.1–1.2)
- Safety lives in the structure of the contract, not in demanding the
  market overpay. (2.9)
- The engine is the asset; change the fuel, never the brakes. (1.4)
- Two charters at a time; everything pre-registers its own death. (4)
