# Adversarial Review — Amendment 1 (RECALIBRATION.md, v2.1 proposal)

Reviewer: Claude session, instructed to attack before implementing. Not a
"fresh blind context" per Art 6.2 — that stricter bar is only *required* for
amendments to the entrenched partition (2.2), which this amendment does not
touch. A fresh-context review is still recommended before any future 2.2 edit.

**Verdict up front:** the amendment's *direction* is largely defensible and in
two places actively correct, but it cannot be adopted as drafted. Three defects
block it: (a) §2.9's percentile gate, as written, re-introduces the exact
self-referential trap this project just spent a session learning to avoid;
(b) the article citations are wrong throughout (Art 8 does not exist; the
prohibition is 0.2, not 0.3); (c) Charter S resurrects the "Service" that
CONSTITUTION.md v2.0 removed in full and that the operator explicitly killed.
The first two are answerable with reframing/correction; the third is rejected.
Implementation therefore proceeds on the corrected, scoped core (bound 0.2, a
reframed 2.9, 2.10 with a venue caveat, plus the two pre-registrations), and
NOT on Charters S/E/C.

---

## 1. §2.9 (Book gate re-derivation) — the requested focus. Attack.

**Claim under review:** retire the flat 20%-of-width gate; write when the day's
credit/width sits at/above the *Nth percentile of the trailing D-day
distribution* for that underlying/strike, delta-adjusted; correctness judged by
"the executed record must reach n ≥ 30 within the 12-month deadline, or the gate
was mis-specified."

**Objection 1 (fatal as written): a percentile gate is the self-referential
trap, re-introduced.** Two days ago we committed the lesson (decision-log
2026-07-31; `feedback_self_referential_validation` memory) that you must not
judge "fairly paid" against a bar derived from the same machinery that generates
the position. A trailing-percentile gate is precisely that: it says "write when
today's richness is high *relative to its own recent history*." It contains **no
reference to whether the premium covers the risk.** If the entire trailing
distribution is thin (median richness ~8% against a breakeven that must clear
the physical loss rate), the 80th percentile might be 14% — still thin — and the
gate fires anyway. **By construction a percentile gate fires ~(100−N)% of days
regardless of whether a single one of them is fairly paid.** It manufactures
volume by *decoupling the write decision from fair compensation*. That is not a
re-derivation of a fair gate; it is the abandonment of fairness dressed as
prudence — the same move §1.3 accuses the flat gate of, in the opposite
direction.

**Objection 2 (fatal as written): decidability-by-lowering-the-bar is circular.**
§2.9 defines the gate's correctness by whether it yields n ≥ 30. By that metric
"always write" is the optimal gate (maximal n). The amendment treats n = 0 as a
"decidability failure," but n = 0 *because the market never offers a fair price*
is a **true finding about an efficient market**, not a defect to engineer away.
Forcing n ≥ 30 by relaxing the gate converts a real negative into a manufactured
dataset of marginal bets — and then the pre-registered live gate (beat
always-write + drift) would be evaluated on trades the machine should not have
made. Decidability is a legitimate concern; buying it with trade count is not.

**Objection 3: "delta-adjusted" hand-waves the load-bearing step.** The clause
says "delta-adjusted (per the busy-parameter lesson)" without saying *which*
delta. If from the placement model (N(−sd)), it is self-referential (the very
error we fixed). If from market IV/skew, then by no-arbitrage richness already
tracks that delta, so "delta-adjusted percentile" collapses toward "how richly
is the market pricing this relative to itself" — Objection 1 again. Under-
specified exactly where it must be exact.

**Objection 4: choosing N and D on the backfill burns statistical budget.** The
task instruction — "compute the trailing distribution from shadow/backfill data
before choosing the threshold" — is a live risk. If N,D are picked to *hit a
trade count* or *maximize backtest P&L*, that is adaptive fitting on the spent
2-year window (violates 1.3). N,D must be fixed by a stated principle, and the
backfill used only to *report* the frequency each principled choice implies, not
to *select* the profitable one.

**Objection 5: fragmentation and cold-start.** "for that underlying and
strike-distance" splits an already-thin sample five ways; for the first D days
there is no trailing distribution at all. Undefined at boundary.

**Is §2.9 answerable? Yes — but only by reframing what the percentile IS.** The
amendment's own best sentence points the way: *"safety lives in the structure of
the contract, not in demanding the market overpay."* That is correct and
important: because max loss is contractually bounded (width − credit) and sized
≤ 5% (2.4), thin premium is **not a solvency violation** — it is at worst a −EV
bet, and whether it is −EV is exactly what the forward record measures against
the always-write shadow control. So the defensible construction is:

- The percentile gate is **not the fairness test.** Fairness/ruin-avoidance
  rests on the bounded partition (2.2) + solvency (2.4), unchanged.
- The percentile gate is a **pre-registered deployment-timing hypothesis** —
  "insurance is comparatively expensive now" — *tested forward against
  always-write.* If it adds nothing, the live gate kills it. It must be labeled
  a hypothesis, never "the re-derived fair gate."
- N and D are **fixed a priori by a stated rationale** (e.g. top-quartile as a
  standard IV-rank convention), not tuned to trade count or P&L. The backfill
  distribution is computed to *report* implied cadence and decidability, not to
  choose the winner.
- An **absolute floor** accompanies the relative gate (never write below a
  fixed richness, however rich the recent week), preserving a fairness anchor.
- The **shadow always-write arm is the mandatory control** (the amendment
  already states this in 3.2 — good).
- "Must reach n ≥ 30 or mis-specified" is **softened**: n ≥ 30 is a decidability
  *target*, but the threshold is chosen by principle; if a principled gate still
  cannot reach n ≥ 30 in 12 months, the honest reading is "no fair premium
  exists at tradeable frequency," a *finding*, not a mis-specification.

With those five corrections the clause is adoptable. Without them it is the trap.

## 2. Bounding the prohibition (§1.1–1.2, §2.1) — mostly correct; wrong address.

The substantive claim — "~43 falsifications measured a ceiling on *price-derived*
signals, not on all inputs; generalizing to a global mispricing ban exceeds the
evidence" — is **fair and largely correct.** Text, filings, event structure, and
positioning were never tested; a verdict about candles is not a verdict about
everything. The discipline that makes the expansion safe (mechanism-naming,
pre-registration, forward-only, kill criteria, cost floors) is retained
unamended (§1.4). Endorsed.

**But the amendment amends the wrong clause.** In CONSTITUTION.md the mispricing
prohibition is **Art 0.2** ("Any proposal requiring prediction of mispricing is
out of scope by constitution"); **Art 0.3 is the generative mandate.** The
"Art 0.3 rewrite" in §2.1 must therefore be applied to **0.2**, leaving 0.3
(the generative mandate) intact — indeed the bounding *serves* 0.3. Blindly
overwriting 0.3 would delete the generative mandate. Corrected in implementation.

**Residual caution (answerable):** text/event signals still face efficient-
market pressure (many funds read filings). The bounding is only safe *because*
each hypothesis must name "who is forced to act slower than us." That mechanism
requirement must be explicit in the amended clause, not just in Charter T prose.

## 3. §2.10 (event contracts admissible) — a correct reading, missing one caveat.

Binary/defined-outcome contracts do have contractually computable worst cases
(max loss = stake / defined width) and are admissible under the *existing* 2.2.
Fine. **Missing:** 2.3's worst case = contractual extreme × *guaranteed stressed
time-to-flat*, and event venues (Kalshi/Polymarket-type) carry a real venue tail
(thin, discontinuous settlement, withdrawal risk) — exactly the 100%-of-venue
tail that blocked funding-carry in 2.7. 2.10 must carry the venue-robustness /
fair-compensation-per-venue test, sized under 2.4. With that note, adoptable.

## 4. Charter S (the Service) — REJECTED.

§3.5 has "the Service publishes its first pre-registered autopsy." CONSTITUTION
v2.0's own header removed the Service "in full, along with the auditor-conflict
integrity layer that only existed to serve it," and the operator's standing
direction is explicit: *"we are not publishing public papers … this is all in
the service of finding a trading machine — not publishing."* Charter S
contradicts both the current charter and the operator's stated intent. It is not
answerable by reframing; it is out of scope. Not implemented. (The task scope —
0.2/0.3 + 2.9/2.10 + two pre-regs — already excludes it; this records *why* it
stays excluded.)

## 5. Sequencing (§4), Charters E/C — defer, do not adopt now.

"Two active charters max" (§4.1) and "each charter pre-registers its own kill"
(§4.2) are sound governance and consistent with 6.3. But E (event underwriting)
and C (crowd/positioning) are *permissions*, not this task's deliverables. They
activate only via their own pre-regs. Nothing here implements them. The opening
pair per §4.1 is B′ (the re-derived Book gate) + T (text signals) — which is
exactly the two pre-registrations this task drafts. Consistent.

## 6. Structural/citation defects (must fix before any commit).

- "Art 8.1 / 8.3 / Art 8 governs this document" → the amendment article is
  **Art 6**. Corrected to 6.1/6.3.
- "Art 0.3 rewrite" (prohibition) → the prohibition is **0.2**; 0.3 is the
  generative mandate. Applied to 0.2.
- "Art 2.5/3.3 analogues" (§2.1) → 2.5 (evaluation) and 3.3 (graduation) exist
  and are the right references; kept.
- Same-day adoption: 6.1 forbids an amendment taking effect the same day it is
  proposed *while any affected position is open.* The Book currently has **no
  open positions** (n = 0, positions.jsonl empty), so the bar does not bind and
  v2.1 may take effect on commit. Recorded.

## 7. Disposition

**Answerable → implement, corrected:** bound 0.2 (not 0.3) with the mechanism
requirement; add 2.9 reframed per §1's five corrections; add 2.10 with the
venue-robustness caveat; bump to v2.1; fix citations; append corrected
one-liners. Draft the two pre-registrations (re-derived Book gate with a
*principled* percentile + absolute floor, cadence *reported* from real data; and
the Charter T scaffold — no data collection until its pre-reg is committed).

**Rejected / deferred:** Charter S (contradicts v2.0 + operator intent);
Charters E/C (defer behind B′/T per the two-charter cap).
