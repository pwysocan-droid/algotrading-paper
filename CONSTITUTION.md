# CONSTITUTION — The Book & The Service

Founding document of the successor program. Pre-registered before the first
premium is written and before the first autopsy is scheduled. This file lives
at the root of the registry; every amendment is a versioned commit with a
written rationale. Nothing in this document may be waived verbally, from
memory, or in the moment.

Working name: **The Book & The Service**. (Rename freely; the structure is
the name.)

> **Ratification note (v1.0, 2026-07-23).** [SET] values resolved below:
> 2.4 per-position ≤ 5% / portfolio ≤ 25% of Book capital (operator
> risk-appetite call, amendable per Article 8); 2.5 n = 30 (inherited
> quarantine); 6.1 quarterly with a year-end tax pass; 8.3 N = 3. Two
> refinements are routed to the funding-carry spec (2.8), not the articles,
> because they operationalize principles the articles already state:
> (a) "fair compensation" is decided by the position's IMPLIED BREAKEVEN
> FREQUENCY (accumulated_premium / structural_magnitude — a computed number)
> judged structurally survivable, never by an estimated tail frequency
> (2.3-compliant, actuarial loss-ratio form); (b) funding carry is
> admissible ONLY as the delta-neutral basis trade (long spot + short perp),
> since naked funding collection has unbounded price loss and fails 2.2.

---

## Article 0 — Objective

0.1. The objective of this program is the instrument, the registry, and what
we know. It is not returns. Returns at this capital scale are a test
statistic, not a goal.

0.2. The product of the predecessor program was a credible negative plus the
instrument that produced it. The product of this program is that instrument
pointed at the two things the evidence says it is fit for: underwriting risk
transfer, and auditing others' claims.

0.3. This program does not hunt mispricing. Forty-odd falsifications across
two markets established that fighting for mispricing at retail scale in
liquid markets does not pay net of costs. Any proposal that requires the
program to out-predict an efficient market is out of scope by constitution,
not by judgment call.

## Article 1 — Inherited findings (the evidence this constitution stands on)

1.1. No mispricing edge survived the conjunction of costs, power, and
multiple-testing correction, in either market, at any horizon tested.

1.2. The two most positive findings were both risk-premium-shaped, not
alpha-shaped: compensation for bearing something, never reward for
predicting something.

1.3. The historical dataset's statistical budget is spent. ~40 adaptive
tests against the same window mean no new in-window discovery can be
trusted. All evaluation in this program is forward-only.

1.4. The instrument's confidence about a premium is anti-correlated with
tail safety: the premia it will flag as best-compensated are selected for
tails that have not fired in the window. This is a selection effect, not
evidence of safety, and it is the founding hazard this constitution is
built to contain.

## Article 2 — The Book (underwriting program)

2.1. **The question.** The Book asks one question of every candidate: *am I
being paid fairly for this risk transfer, tail included?* It never asks
whether anything is mispriced.

2.2. **Admission rule (the partition).** The Book may hold only contracts
whose structure bounds the maximum loss. A candidate is admissible if and
only if its worst case is computable from contract terms alone —
contractual caps, defined-risk structure, finite exposure. Unbounded
structures (naked short convexity, uncapped adverse carry, unlimited
liability of any form) are inadmissible at any level of compensation,
permanently. No measured Sharpe, no calm-window history, and no amendment
short of rewriting this article admits an unbounded structure.

2.3. **Tail pricing.** Tails are priced from mechanism, never from history.
The structural worst case of a position is:

> contractual adverse extreme × guaranteed stressed time-to-flat

where time-to-flat is a measured property of our own infrastructure
(monitoring cadence, order constraints, worst-case reaction lag under
degraded conditions), not of the market. Estimating tail *frequency* is
forbidden. Estimating tail *magnitude* from the sample is forbidden. Both
factors of the bound must be measurable without either estimate.

2.4. **Solvency sizing.** Positions are sized against the structural worst
case, not against measured volatility:

- Per position: structural worst case ≤ **5%** of Book capital.
- Portfolio: the sum of simultaneous structural worst cases across all open
  positions ≤ **25%** of Book capital. Correlation assumptions are not
  permitted in this sum; all worst cases are assumed to fire together.

2.5. **Evaluation.** Forward-only. Drift/market null mandatory for every
verdict. Small-sample quarantine applies (below **n = 30**, a result is
neither pass nor fail). Every premium enters with a pre-registered kill
criterion decidable within a stated forward window.

2.6. **Book-level kill.** Pre-registered now: if a structural worst case
fires and the realized loss *exceeds* the computed bound, the Book halts
immediately — not because of the loss, but because the bound was
mis-specified, which invalidates every other bound in the Book. Trading
resumes only after the bound methodology is re-derived and the error is
written up in the registry.

2.7. **The Book's second function.** The Book is the laboratory of the
Service. Every audit technique the Service uses must first have been
developed and exercised on the Book's own live cases. The Book is
foundational, not subordinate: it is where the standards are written that
the Service later certifies against.

2.8. **First admitted candidate.** Funding-rate carry (D2 lineage),
DELTA-NEUTRAL basis form only (long spot + short perp): the funding accrues
on the short leg and the worst case is bounded by basis convergence + fees,
therefore admissible under 2.2 — the naked directional form is inadmissible
(unbounded price loss). Fair compensation is decided by its implied
breakeven frequency (accumulated funding / structural basis-blowout
magnitude), judged structurally survivable, never by an estimated funding-
inversion frequency. Its bound, sizing, and kill criterion are registered
in its own spec, subject to every rule above.

## Article 3 — The Service (falsification of public claims)

3.1. **The format.** Every autopsy is pre-registered before it is run: the
target claim, the data, the method, the cost model, and the kill criterion,
committed to the public timestamped registry *before* any result exists.
The result publishes regardless of outcome. A famous strategy that
survives the autopsy is published with the same prominence as one that
dies. Publishing only kills is the failure mode of the genre; the
pre-registration is the moat.

3.2. **Scope.** The Service autopsies claims, never people. Titles, framing,
and text address the strategy and the evidence. No autopsy publishes a
verdict about a person's honesty, competence, or motives.

3.3. **Standard battery.** Every autopsy inherits, at minimum: empirical
cost floor; drift null (never zero); survivorship correction;
multiple-testing haircut; instrument power check against a planted signal;
yardstick matched to the claim's mechanism; regime conditioning. Omitting
any element must be justified in the pre-registration, in writing.

3.4. **Method provenance.** Per 2.7, no method is pointed outward before it
has been sharpened on the Book.

3.5. **Blind adversary.** The standing blind-adversary stage is retained:
before publication, the autopsy's state is handed to fresh, unanchored
contexts instructed to attack it. Their objections are answered in writing
or the publication waits.

3.6. **Target selection.** Early targets are chosen for decidability, not
heat: famous claim, public data, clean kill criterion. The Broad Street
pump, not a border skirmish.

## Article 4 — Integrity regime (two layers, neither self-policed)

4.1. **Founding premise.** The corruption of an auditor is invisible to the
auditor. Berenson did not feel the drift. Therefore no safeguard in this
article may depend on the author's judgment, memory, or sense of their own
cleanliness.

4.2. **Layer one — mechanical (positions).** A tooling-generated conflict
declaration is produced automatically from the registry's position history
and attached to every autopsy before it can publish. The check is a
blocking gate in the publication pipeline, not a checklist item. If the
Service's author holds, has held, or has a registered pending interest in
any instrument the audited claim touches, the declaration states it,
verbatim, machine-written. A bypassed or failed gate is a constitutional
breach: the autopsy is retracted and the breach itself is published.

4.3. **Layer two — constitutional (revenue).** The mechanical gate can only
see conflicts the registry contains; off-book incentives are invisible to
it by construction. Therefore, by standing rule: the Service accepts no
money, sponsorship, affiliate arrangement, privileged access, product, or
consideration of any kind from any party whose claims it could ever audit.
Data and products under review are acquired at retail. This rule predates
every temptation on purpose; it is cheap now and cannot be retrofitted
after the first accusation.

4.4. **Publicity of the registry.** The registry — positions,
pre-registrations, results, this constitution, and its amendment history —
is public and timestamped. Credibility is compounded there or nowhere.

## Article 5 — Sequencing

5.1. **Phase one — authority (the Cochrane model).** Reputation is built
solely from public rigor: pre-registered autopsies, published survivals,
visible integrity gates. This phase is available immediately and requires
no one's permission.

5.2. **Phase two — institution (the UL model).** Certification — the mark
others seek — is an aspiration, not a plan. It requires a market that wants
rigor, and the retail-strategy ecosystem currently profits from its
absence. Phase two may be *considered* only if unsolicited demand for
certification appears; it is never assumed reachable because phase one
works, and no phase-one decision may be justified by phase-two ambitions.

## Article 6 — Structural edges (banked, not targeted)

6.1. Tax-loss harvesting, fee-tier and rebate optimization, and cash yield
on idle collateral are the only guaranteed edges at this scale. They are
maintained as a background checklist, reviewed **quarterly (with a year-end
tax pass)**, and executed as arithmetic.

6.2. The instrument is never pointed at them. They need a checklist, not a
machine, and they justify no infrastructure.

## Article 7 — Inherited operational law

Carried over from the predecessor program in full force:

7.1. Autonomy is a state machine over durable artifacts. Every unattended
run derives its actions from committed state; nothing load-bearing lives in
any context or memory.

7.2. Correctness checks outrank liveness checks. Golden-output regression
tests and data contracts (row counts, ranges, gap detection) fail loudly.
Silent corruption is the enemy; downtime is an inconvenience.

7.3. Alarms judge only the most recent run. An alarm that keeps ringing
after recovery trains its operator to ignore all alarms.

7.4. The dead-man's switch uses an active external watchdog. Absence of
email is not a signal.

7.5. Single-writer data ownership, pinned dependencies, a locked
architecture list, and a decision log that records *why*.

## Article 8 — Amendment and the willingness to stop

8.1. This constitution is amended only by versioned commit with written
rationale. No amendment takes effect on the same day it is proposed while
any affected position is open or any affected autopsy is unpublished.

8.2. Article 2.2 (the partition) and Article 4 (integrity) are entrenched:
amending them requires, in addition to 8.1, a written adversarial review
from a fresh blind context arguing *against* the amendment, answered in
writing.

8.3. Program-level kills, pre-registered now:
- The Book dies under 2.6 (a bound proven mis-specified) if re-derivation
  fails, or if **3** consecutive admitted premia fail the fair-compensation
  test at their forward horizon.
- The Service dies on a second integrity breach under 4.2, or the first
  under 4.3. One mechanical failure is an incident; a revenue violation is
  the end, because 4.3 has no innocent failure mode.

8.4. The discipline that makes this program trustworthy is its willingness
to stop. The predecessor stopped when its kill fired; that is the whole
reason this document is worth writing. Nothing here mistakes "we can keep
going" for "we should."

---

## The one-line articles

- We do not hunt mispricing; we underwrite bounded risk and audit public
  claims. (0, 2, 3)
- Only structures that bound the loss enter the Book; tails are priced from
  mechanism × our own stressed exit time, never from history. (2.2, 2.3)
- Confidence about a premium is not evidence about its tail. (1.4)
- The Book writes the standards; the Service certifies against them. (2.7)
- Pre-register before the result exists; publish survivals. (3.1)
- The auditor is never trusted to feel their own corruption: machines check
  positions, the constitution forbids revenue. (4)
- Authority first; the institution only if the world asks for it. (5)
- Free money is a checklist, not a target. (6)
- Everything is willing to stop, and says so in advance. (8)
