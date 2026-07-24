# CONSTITUTION — The Book

Founding charter of the trading machine that succeeds the search program.
Pre-registered before the first position. Lives at the registry root; every
amendment is a versioned commit with written rationale. Nothing here may be
waived verbally, from memory, or in the moment.

> **v2.0 (2026-07-23).** Corrects v1.0's confusion: the objective is a
> **trading machine**, not a public falsification service. The "Service"
> (publishing autopsies) is removed in full, along with the
> auditor-conflict integrity layer that only existed to serve it. What
> remains is the Book — a machine that earns by underwriting bounded risk —
> plus disciplined search of the structures the evidence still licenses.
> E-1.0 real-money cost experiment: shelved by operator (2026-07-23).

---

## Article 0 — Objective

0.1. The objective is a trading machine whose edge survives costs. At this
capital scale the dollars are small; the deliverable is a *working machine
and the proof it works* — an edge that clears the honesty gauntlet, or the
credible finding that a given structure cannot.

0.2. The evidence forbids one whole approach and points at another. ~40
falsifications established that **hunting mispricing** — out-predicting an
efficient market at retail scale in liquid markets — does not pay net of
costs. Any proposal requiring prediction of mispricing is out of scope by
constitution. The two positive findings were **risk-premium-shaped**:
compensation for bearing something, not reward for predicting something.
The machine is built on that.

## Article 1 — Inherited findings (the evidence this stands on)

1.1. No mispricing edge survived the conjunction of costs, power, and
multiple-testing correction, in either market, at any horizon tested.

1.2. The most positive findings were risk-premium-shaped (low-vol delivered
its risk-reduction thesis; the shock-fade is contrarian liquidity provision).

1.3. The historical window's statistical budget is spent (~40 adaptive
tests). No new *in-window* backtest verdict can be trusted. New evaluation
is forward-only, or on genuinely new data/structure.

1.4. The instrument's confidence about a premium is anti-correlated with
tail safety: premia flagged as best-compensated are selected for tails that
haven't fired in the window. A selection effect, not evidence of safety —
the founding hazard this charter contains.

## Article 2 — The Book (the machine)

2.1. **The question.** Of every candidate: *am I paid fairly for this risk
transfer, tail included?* Never: *is this mispriced?*

2.2. **Admission (the partition).** The Book holds only structures whose
maximum loss is computable from contract terms alone — contractual caps,
defined-risk, finite exposure. Unbounded structures (naked short convexity,
uncapped adverse carry, unlimited liability) are inadmissible at any level
of compensation, permanently — no Sharpe, no calm history, no amendment
short of rewriting this article admits one.

2.3. **Tail pricing — mechanism, never history.**
> structural worst case = contractual adverse extreme × guaranteed stressed
> time-to-flat
where time-to-flat is a measured property of our own infrastructure, not
the market. Estimating tail *frequency* is forbidden; estimating tail
*magnitude* from the sample is forbidden. Both factors of the bound must be
measurable without either estimate.

2.4. **Solvency sizing** (against the structural worst case, not volatility):
per position ≤ **5%** of Book capital; sum of simultaneous worst cases
across all open positions ≤ **25%**, no correlation credit (all fire
together).

2.5. **Evaluation.** Forward-only. Drift/market null mandatory. Small-sample
quarantine below **n = 30** (neither pass nor fail). Every position enters
with a pre-registered kill decidable in a stated forward window, and
**fair compensation is judged by implied breakeven frequency**
(accumulated premium ÷ structural magnitude — a computed number), never by
an estimated tail frequency.

2.6. **Book-level kill.** If a realized loss exceeds its computed bound, the
Book halts immediately — the bound was mis-specified, which invalidates
every other bound. Resume only after the methodology is re-derived and the
error written up.

2.7. **Candidate #1 (pre-registered).** Funding-carry, delta-neutral basis
only (book/pre-reg-funding-carry-basis.md): dominant tail = venue failure
(100% of on-venue capital) → ≤5%/venue by 2.4; admits only robust venues by
the fair-compensation test; VENUE-BLOCKED on Alpaca (spot-only). The likely
true first position is a **spot-only defined-risk premium** executable on
the account we hold — to be specified next, subject to every rule above.

## Article 3 — Continued structural search (the other half of the machine)

3.1. The Book is one structure. The evidence also leaves specific untested
structures whose leads are *measured*, not hoped-for. These are searched
under full discipline (drift null, control arm, matched yardstick, regime
conditioning, small-sample quarantine, pre-registered kill), forward-only
where the historical budget is spent.

3.2. **Live leads:**
- **Event-driven shock-fade** — a measured post-shock reversion that
  survives at a matched exit but only at n=18 (below quarantine) and
  regime-dependently. Pursued via **shadow-arm forward accumulation** (zero
  risk) and a cross-market power test, never promoted on the in-window n.
- **Alt-data (Layer-2)** — the funding/OI/order-book tape, already
  collecting, feeds candidate risk-premium structures (2.7) and is the one
  input class not yet mined.

3.3. A structure graduates from "search" to "Book position" only when it
both (a) presents a bounded, mechanism-priced tail admissible under 2.2 and
(b) clears its forward kill. Search that never finds an admissible bounded
structure ends in a recorded negative, not an unbounded bet.

## Article 4 — Integrity & operational law

4.1. **Data integrity over cleverness.** Correctness checks outrank liveness
checks; golden-output regression tests and data contracts (row counts,
ranges, gaps) fail loudly. Silent corruption is the enemy; downtime is an
inconvenience.

4.2. **Autonomy is a state machine over durable artifacts.** Unattended runs
derive actions from committed state; nothing load-bearing lives in context
or memory. Accumulated knowledge lives in the versioned registry.

4.3. Alarms judge only the most recent run. The dead-man's switch uses an
active external watchdog (absence of a signal is not a signal). Single-writer
data ownership; pinned dependencies; a locked-architecture list; a decision
log that records *why*.

4.4. The registry is timestamped and self-honest: positions, pre-registrations,
results, this charter, and its amendments. The honesty is for us — the
machine that lies to its operator is worse than one that loses money.

## Article 5 — Structural edges (banked, not targeted)

5.1. Tax-loss harvesting, fee-tier/rebate optimization, and cash yield on
idle collateral are the only *guaranteed* edges at this scale. Maintained as
a background checklist, reviewed quarterly (year-end tax pass), executed as
arithmetic. The instrument is never pointed at them — they need a checklist,
not a machine.

## Article 6 — Amendment and the willingness to stop

6.1. Amended only by versioned commit with written rationale. No amendment
takes effect the same day it is proposed while any affected position is open.

6.2. Article 2.2 (the partition) is entrenched: amending it requires a
written adversarial review from a fresh blind context arguing *against* the
amendment, answered in writing.

6.3. Program-level kills, pre-registered:
- The Book dies under 2.6 (a bound proven mis-specified) if re-derivation
  fails, or if 3 consecutive admitted premia fail fair-compensation at their
  forward horizon.
- The search (Art. 3) ends in a recorded negative if no live lead yields a
  bounded, admissible structure that clears its forward kill.

6.4. The discipline that makes this trustworthy is its willingness to stop.
The predecessor stopped when its kill fired; that is why this charter is
worth writing. Nothing here mistakes "we can keep going" for "we should."

---

## The one-line articles

- The goal is a trading machine that survives costs; we do not hunt
  mispricing. (0)
- We underwrite bounded risk and search measured leads — nothing unbounded,
  ever. (2.2, 3)
- Tails are priced from mechanism × our own stressed exit time, never from
  history; confidence about a premium is not evidence about its tail. (2.3, 1.4)
- Fair pay is judged by the breakeven frequency it buys, not an estimated
  one. (2.5)
- Forward-only where the budget is spent; small samples make no claim. (1.3, 2.5)
- Data integrity over cleverness; the machine must not lie to its operator. (4)
- Free money is a checklist, not a target. (5)
- Everything is willing to stop, and says so in advance. (6)
