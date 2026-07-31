# Pre-registration — Charter T (text-native signals) · SCAFFOLD

CONSTITUTION Art. 0.2 (v2.1, Amendment 1 — untested input spaces in scope) +
RECALIBRATION.md §3.1. This is a **scaffold**: it fixes the discipline and, on
commit, authorizes **data collection only**. No live or paper trade occurs on
any text signal until that signal has its **own** committed sub-pre-registration
under `book/`. One of the two active charters (with B′) per the two-charter cap
(§4.1).

## The thesis (bounded, per 0.2 v2.1)

The ~43 falsifications measured a ceiling on **price-derived** signals, not on
**text**. The registry has zero tests of language/filings/governance inputs. An
LLM can systematically read what no retail participant reads at scale —
earnings-call language deltas, 8-K/filing events, crypto governance proposals,
tokenomics/unlock calendars. Whether that yields a tradeable, cost-surviving
edge is **unknown and untested** — this charter tests it, it does not assume it.

## The non-negotiable discipline (carried from 0.2 (a)–(c), unamended brakes)

Every sub-hypothesis under this charter, before any live/paper action, must in
its own pre-reg state:

1. **Mechanism (who is forced to act, and why slower than us).** Name the
   participant who must react to this text and the friction that makes them
   slower than a machine that read it first (mandate, process latency,
   attention limits). "The market hasn't priced it" is not a mechanism.
2. **Horizon and cost model.** The hold, and the *measured* (not assumed) cost
   — spreads on the actual instruments, borrow, event-gap slippage.
3. **Forward-only split, pre-registered.** New data source ⇒ fresh statistical
   budget, but spent forward: **no adaptive mining of a fixed text archive
   without a pre-registered train/holdout split.** The holdout answers one
   question per hypothesis, ever, and is never reused.
4. **Decidable kill + drift null + n<30 quarantine + premise check** (2.5/3.3
   analogues), and a program-level kill in the spirit of 6.3.
5. **Framing.** If the signal predicts a *price move*, it must argue why it is
   not the mispricing-hunting that 0.2 still forbids in price-derived space; a
   text→event→bounded-outcome framing (underwriting, Charter E / 2.10) is
   preferred where it fits.

## Data sources to be wired (collection authorized on commit of THIS file)

- **Equity:** earnings-call transcripts (language/tone deltas vs prior calls),
  8-K / material-event filings, guidance-change text.
- **Crypto:** governance proposals + vote timelines, tokenomics **unlock
  calendars** (scheduled, decidable supply events), protocol-upgrade notices.

Collection is **forward-only from day one**: timestamp every document at
ingestion; store raw + parsed; **never** backfill a signal and mine it. A signal
computed today may only be evaluated on documents that arrive after its
sub-pre-reg is committed. (A separately pre-registered, split-disciplined
historical panel may be added later, but is not authorized by this scaffold.)

## What commit of this file DOES and does NOT authorize

- **DOES:** begin building the ingestion pipeline and collecting/timestamping
  documents forward, under the forward-only rule above.
- **Does NOT:** trade, paper or live, on any text signal; nor mine any archive.
  Each tradeable hypothesis needs its own committed sub-pre-reg first.

## Operator budget & decidability (§4.3)

- Expected operator time: ≤ ~1–2 hrs/week (pipeline review; sub-pre-reg sign-off).
- First decidability checkpoint: **2026-10-31** — either ≥1 sub-hypothesis is
  pre-registered and forward-collecting, or this charter writes up why not and
  yields its active-charter slot.
- Runs alongside Charter B′ (Book gate v2); E and C stay queued behind whichever
  of B′/T finishes or dies first.

## Status

Pinned 2026-07-31, pre-commit. **Data collection MUST NOT begin until this file
is committed.** No sub-hypothesis is yet pre-registered; no trading is
authorized.
