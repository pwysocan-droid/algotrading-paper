# Adversarial Review — SPEC: Event-Market Tape & Calibration Shadow Archive

Reviewer: Claude session, 2026-08-03. Instructed to attack before any build,
focus on §3 (blind pre-regs) and §4 (assertions). Step-zero HEAD-reconciliation
done first (the spec demands it): all article citations grep-verify against HEAD;
the spec was correctly drafted against **v2.1** (it cites 0.2(a), which only
exists post-Amendment-1). One citation ambiguity — see X-0.

**Verdict:** the spec is well-built and self-aware, but it **conflates two things
that must be split**:
- **W1 (tape as a Charter T crowd-benchmark)** — LEGITIMATE, and the strongest
  idea here (§5.1) — *provided* collection is curated to Charter T's text-linked
  event universe, which also dissolves the disk problem.
- **W2 (calibration ledger + P1 + the E3 sum-violation counter)** — this is
  **mechanically the dead Charter E's Stage-1 calibration arm**, re-instantiated
  under an "infrastructure" name. It measures the question the kill already
  answered, and inverts the spec's own sequencing (0.3). **Defer W2 until an E²
  pre-reg is committed.**

Plus one fatal omission (no disk estimate) and several assertion bugs that would
cry wolf. Details below.

---

## X-0. Citation check (step zero) — pass, one ambiguity

All grep-verified against HEAD: 0.2(a) mechanism (CONSTITUTION:50), 4.1
correctness>liveness (CONSTITUTION:201), 3.2 Layer-2 tape (CONSTITUTION:190),
Charter E kill (2 dead-ideas entries), pre-reg-E §0.1 Polymarket (line 33).
**Ambiguity:** the spec uses "**§4.1**" for the charter-slot cap (which is
**RECALIBRATION §4.1**, line 112) and "**Art 4.1**" for correctness>liveness
(**CONSTITUTION 4.1**) — two different 4.1s, same document. Disambiguate by file
or a reader conflates them. This is the collision the grep-rule exists to catch.

## §0 — the load-bearing "collection ≠ experiment" claim. Attack.

**O-1 (fatal to W2 as drafted): W2 *is* the dead charter's Stage-1 arm.** The
Charter E pre-reg §1.3 was literally *"calibration measurement first (zero-risk
arm): log every qualifying contract's price and resolution... the premise
checkable at zero risk."* W2 (§2.4 calibration ledger + §3 P1) is that arm,
verbatim, renamed "tape." The kill was supposed to foreclose that arm — or (per
this spec's own §0.3) gate it behind an E² pre-reg that *argues the different
premise in writing first.* W2 builds and RUNS the arm NOW, before any such
argument. **The sequencing is inverted: it collects the experiment's evidence
before the experiment is re-authorized.** "Silent, no action attached" does not
change that you are computing the E-signal and scoring a frozen prediction against
it; when P1/P2 look good at 90 days, the infrastructure + predictions + scores are
all sitting there and the only missing step is the trade — which is not
"collecting the instrument," it is running the experiment with the trigger taped
over. **Split it:** W1 (below) is defensible; W2 waits for an E² pre-reg.

**O-2 (the "no slot, free" framing understates cost).** "Consumes no §4.1 slot"
is true only for the *trading*-slot technicality. The two-charter cap exists to
bound the **scarcest capital — operator attention** (RECALIBRATION §4.3). A
standing two-venue tape with nightly derived jobs, dispute tracking, correctness
assertions, and a 90-day review IS a real attention draw — §6.2's own stop
condition concedes it. Call it low-cost infrastructure, not free.

## §1 — venues. Attack.

**V-1: restarting Kalshi 3 days after sunsetting it, heavier.** The 2026-07-31
sunset named the reactivation trigger as *"a changed fee schedule → fresh Stage
0."* This spec reactivates Kalshi for a *different* reason (tape/calibration) and
*heavier* (full price curve, hourly). That may be legitimate — but it must
**cross-reference and explicitly supersede** the sunset entry's trigger, or it
reads as reactivation-by-accretion three days later.

**V-2: Polymarket "US-relevant fee schedule now exists (QCEX path)" is an
unsourced factual claim** baked into the spec, about a moving regulatory target.
Source + date it, and note the ToS-collection risk (§6.2 already contemplates a
venue forbidding collection). Observational-only is right; the fee claim is not
yet a fact.

## §2 — schema. Attack (the fatal omission lives here).

**S-1 (FATAL as drafted — no disk estimate):** §2.2 logs the **full price curve,
all buckets, all markets, two venues, 60-min cadence (5-min in the final 24h)**.
Kalshi has ~800k open markets (the number that caused the truncation finding). A
back-of-envelope: even 100k snapshotted hourly ≈ 2.4M rows/day/venue ≈ ~360
MB/day/venue ≈ **~250 GB/year** on a **38 GB box that hit 95% twice this month.**
This is the exact heavy-collection pattern behind today's gc-cadence fix. The
spec MUST carry a hard MB/day estimate, a gitignored-raw plan, AND a population
cap — and §5.1 hands you the cap for free (collect only the event markets that
intersect Charter T's text universe, not everything). Without this, the spec is
the next disk incident, pre-scheduled.

**S-2:** verbatim question text (§2.1) is Charter T fuel but is ~static — store
once in a catalog table, never re-snapshot it daily. Matters at Kalshi scale.

## §3 — blind pre-registrations. Attack (requested focus).

**P-general (the deep one): the predictions are aimed at the dead charter's
question, not the live one.** §3.1's instinct — commit predictions while the
archive is empty — is exactly right and endorsed. But P1–P3 re-litigate *does the
calibration bias exist*, which Charter E already rendered **irrelevant**: the kill
was not "no bias" — it was "bias 1–2¢ < cost 2–8¢." A signal can exist and be
untradeable; that is precisely what was found. So:

**P-1 (calibration): measures the wrong quantity.** Predicting "longshot
overpriced / near-certainty underpriced by low single-digit cents" predicts a
number whose existence changes nothing — it can be *confirmed* and the charter
stays dead. Fix: P1 must predict the **tradeable miscalibration NET OF the
measured cost floor** — which, given Stage 0, should be pre-registered at
**≈ zero**. Predicting ≈0 and confirming it is the honest blind pre-reg;
predicting the gross bias manufactures the illusion of progress.

**P-2 (sum-violations / E3): overcounts a mirage unless funnel-costed.** A
cross-venue Yes+No violation is only real if *captured* — two spreads crossed,
two fees paid, two settlement tails borne, simultaneously. A "frequency count of
violations exceeding [SET]¢ after each venue's fee" that ignores the two-legged
execution cost and the simultaneity/liquidity conjunction counts gross, not
capturable. The spec flags conjunction discipline itself (good) — so **P-2 must
predict the FUNNEL** (violation AND both legs liquid AND simultaneous AND
net-of-two-legged-cost), which per CONJUNCTIONS-MULTIPLY-TO-ZERO likely
pre-registers at ≈0. Predict the funnel, not the gross.

**P-3 (dispute rate): honest but slow and low-value.** It prices a real
settlement tail (good), but a rare-event base rate needs many resolutions to
estimate (per the Charter E n-computation, tail rates are slow to pin), and it
prices a tail for **Polymarket, which is observational-only (untradeable).** Keep
it as a data-quality metric; do not dignify it as decision-relevant yet.

**P-missing: the actual Charter T prediction isn't here.** The live question this
tape serves (§5.1) is *does a text signal beat the event-market price?* The
strongest blind pre-reg would be about the **text→price** relationship, not the
calibration curve. The spec pre-registers the dead charter's questions and omits
the live one.

**P-decidability: n<30 is far too lax for the tail claims.** §6.1's "n<30
resolutions per bucket makes no claim" is the generic quarantine, but P1 is a
**tail-bucket** claim, and the Charter E power computation showed a 2pp tail
effect needs **~750 resolved contracts per bucket**, ~3,400 for 1pp. Carry that
figure, or P1 will "resolve" on 30 and mislead.

## §4 — correctness assertions. Attack (requested focus).

**C-1: "every price in (0,1)" false-alarms on legitimate extremes.** Settled and
near-certain markets trade at exactly 0/1 (or 0.01/0.99); a strict-open assertion
cries wolf on real data → the operator learns to ignore it (our own
alarms-must-forgive lesson). Use [0,1] closed, and exclude settled markets from
the bound check.

**C-2: "row-count deltas within expected band" needs a calendar-aware band.**
A static band false-alarms every weekend (exactly what Charter T's EDGAR ingest
showed: 0-new Sat/Sun is *correct*). Make the band day-of-week/holiday aware or
it is noise.

**C-3 (the real one — internal contradiction): the pagination-completeness
assertion collides with the disk cap.** §4's "fetched count == venue's reported
total" is the *right* lesson (the max_pages bug, named) — but it asserts
**full-population completeness**, while S-1's disk reality forces a **subset**.
You cannot both "assert we fetched all 800k" and "only store a curated subset."
Resolve by defining completeness against the **intended universe** (the curated
event-text-linked set), not the venue's raw total — else the assertion
perpetually fails the moment you filter for disk. As written, §2 and §4
contradict.

**C-4: fee-schedule drift detection is a manual dependency, not an automatic
assertion.** Kalshi's fee is a *formula*, not an API-versioned field; "fee-schedule
version in force" (§2.1) must be human-tracked. So the "version drift raises a
flag" (§4) is only as reliable as a manual process that can lapse silently — the
opposite of a loud correctness check. Name it as a manual control with its own
review, or it gives false assurance.

## §5 — Charter T interface. (Endorse — this is the spec's real value.)

**§5.1 is the strongest idea in the document and the actual justification for
W1:** a liquid, real-money event-market price is a clean crowd-probability
benchmark a text signal must *beat* to be worth anything. That is genuinely
useful for Charter T. It also **scopes the collection**: you only need the tape
for markets with a text counterpart in Charter T's universe — a small curated
subset, which resolves S-1's disk problem and sharpens the mechanism (§0.2(a)).
Build W1 to serve §5.1's need, not §2.2's "all markets, all buckets."

## Disposition

**Build (corrected): W1 only** — the event-market tape as a Charter T
crowd-benchmark, scoped to the text-linked event universe (curated, not full
population), with: a hard disk estimate + cap; the C-1..C-4 assertion fixes;
completeness defined against the intended universe (C-3); the Kalshi-restart
reconciled with the sunset entry (V-1); Polymarket fee-claim sourced (V-2);
§4.1↔Art 4.1 disambiguated (X-0).

**Defer: W2** (calibration ledger, P1, E3 counter) — it is the dead Charter E's
Stage-1 arm, and 0.3 already says the E² argument must be written *first*. If the
operator wants the blind pre-reg now, pre-register the **live** question (text
beats price, §5.1) and the **cost-net** versions of P1/P2 (≈0), not the gross
biases the kill already made irrelevant.
