# REVIEW-RESPONSE-R1 — Answer to the adversarial review of SPEC v1

Status: DRAFT — externally drafted (chat, 2026-08-03), same session as
SPEC v2. Files: review R1 (Claude Code), this response, SPEC v2.
Convention per the Art 6.2 pattern: attack in writing, answered in
writing, disagreement resolved before commit.

**Material fact for re-review:** R1 was issued without
`addendum-w3-and-queue-stubs.md` in context. The rebuttal below (§2)
depends on it. Re-review must load both documents.

> **Committed 2026-08-03** as the governance record of the R1→R2→PATCH
> cycle. Preserved with the spec per the Art 6.2 pattern (attack in
> writing, answered in writing). The reviewer's R1 and R2 live at
> `reviews/spec-event-market-tape-review*.md`.

---

## 1. Conceded — adopted in v2 without argument

1.1. **Disk budget (R1 "fatal omission").** Conceded as the worst miss
in v1: a spec that names the silent-pagination-cap lesson while
pre-scheduling a disk-exhaustion incident learned the letter, not the
spirit. v2 §2.4: pre-commit estimate, measured first-week rate sets
retention, hard cap with loud pause-not-drop, resolved-market
compression.

1.2. **Curated universe.** Adopted, and R1 undersold its own fix: the
curation is epistemically better, not just operationally — snapshotting
only text-universe-intersecting markets sharpens the §5.1 mechanism
instead of diluting it across sports strikes. v2 §2.2, versioned rules.

1.3. **P1 aimed at the dead question.** Conceded. The kill was
"bias < cost," never "no bias." v2 P1 predicts the cost-net tradeable
miscalibration, with the honest Kalshi prior ≈ 0 and the gross bias
pre-registered as expected-and-non-actionable. This concession also
strengthens the firewall (v2 §0.3): a confirmed gross bias can no longer
masquerade as staged E² evidence.

1.4. **P2 funnel-costing.** Conceded — this is the registry's own
CONJUNCTIONS MULTIPLY TO ZERO lesson pointed back at its author. v2
§2.6: capturable-only statistic, staged funnel reported, gross count
demoted to color.

1.5. **Power (n<30 too lax).** Conceded. Quarantine is a floor, not
power; a 2pp tail claim needs ~750 resolved/bucket per the Charter E
power calc (recomputed and pinned at commit). v2 §3.2, and §6.1 scores
accumulation against the power number, not 30.

1.6. **All four §4 fixes.** Closed [0,1] with settled exclusion;
calendar-aware row bands (the EDGAR Saturday lesson); completeness
asserted per-denominator (catalog = full population, snapshots =
versioned curated list — dissolving C-3's contradiction); fee-drift
demoted to an honestly-labeled manual checklist item. All in v2 §4.

1.7. **Citation disambiguation.** Adopted spec-wide: Art N.n vs
REC §N.n; no bare 4.1 anywhere.

## 2. Rebutted — W2 deferral (the review's verdict)

2.1. **R1's load-bearing attack, restated fairly:** W2 is dead Charter
E's §1.3 zero-risk arm verbatim, renamed; §0.3 demands the E² argument
come first, yet W2 collects the experiment's evidence before the
experiment is re-authorized; "silent, no action attached" doesn't cure
inverted sequencing, because at 90 days everything is staged and only
the trade is missing.

2.2. **The rebuttal is a dependency fact, not a preference.** The
already-approved addendum makes W3 (the LLM forecast duel) priority 1
and pre-registers it as the gate in front of any E′ (§A.6). Scoring the
duel — engine Brier vs venue Brier, per-bucket tail calibration, same
markets, same timestamps (§A.4) — is mathematically impossible without
venue mids, resolutions, and bucket outcomes. That dataset IS W2. The
venue's calibration curve falls out of the duel's scoring as a
byproduct. "Defer W2" therefore entails "defer W3," which R1 did not
argue and, without the addendum in context, could not have.

2.3. **Deferral has an unstated cost R1 does not weigh: the data is
forward-only.** Resolutions not logged today are unrecoverable. "Defer
until an E² argument exists" means any future E² instrument starts its
accumulation clock at authorization — at ~750/bucket power (R1's own
number), that is a multi-year delay silently attached to a document that
claims only to sequence. Deferral is a kill wearing sequencing's
clothes; if the program wants to kill E² permanently it should say so
and log it, not achieve it by data abstinence.

2.4. **The staging concern is real and is answered structurally, not
dismissed.** v2 makes three changes R1 should audit:
- the ledger is defined as W3's scoring apparatus (§0.2) — it has a
  live, pre-registered consumer that is not E²;
- the E² firewall (§0.3) admits only the duel's scored verdict as
  re-entry evidence — the raw calibration curve is pre-registered as
  expected-and-non-actionable via the cost-net P1;
- both pre-named duel readings (§A.6) are committed before the first
  row exists: engine-wins IS the E² premise; engine-loses kills
  prediction-shaped E² on arrival. The 90-day "everything looks good
  and only the trade is missing" scenario R1 fears cannot occur, because
  what "good" means was written down first — the program's standard
  answer to evidence-staging momentum has never been abstinence; it is
  pre-registration.

2.5. **Authorship disclosure.** The same drafter wrote v1, the addendum,
and this rebuttal; the defense has stake. The rebuttal is constructed to
be checkable rather than persuasive: (a) verify §A.4 scoring is
undefined without resolution/mid data; (b) verify §A.6 pre-names both
readings; (c) verify v2 P1 pre-registers the gross bias as
non-actionable. If any check fails, the rebuttal fails.

## 3. Requested re-review scope

- Load: SPEC v2, this response, `addendum-w3-and-queue-stubs.md`,
  CONSTITUTION HEAD, RECALIBRATION, dead-ideas (Charter E entry).
- Attack surface, in priority order: (1) does the W3 dependency
  actually hold, or can the duel be scored on a narrower dataset than
  W2 collects? (2) does the §0.3 firewall leak — any path where the
  calibration curve alone re-argues E²? (3) are the v2 §2.4 disk
  numbers arithmetic that survives the 38 GB reality? (4) is the
  curated-universe screen's conjunction (text-relevant × liquid ×
  no-conflict) itself anti-correlated in a way that starves the duel's
  n (the registry's own trap)?
- Standard: reject if any check in 2.5 fails or any firewall leak is
  found; otherwise greenlight W1+W2-as-scoreboard jointly with W3.

---

## Resolution (reviewer, R2 + PATCH)

- **Deferral withdrawn** — v2 curated the collection; there is no broad
  census left to defer. The dependency (2.2) resolved not by the
  entailment holding but by v2 scoping W2 to the duel's needs.
- **Firewall (Q2) closed** by the cost-net A.6 (PATCH-3): only a NET win
  argues E²; gross skill that can't out-earn the takeout is the Charter E
  kill re-confirmed.
- **Ghost citation (Art 4.2)** re-grounded as spec-local CX-1 (PATCH-1);
  lesson logged: grep applies to corpses.
- **Q4 (intersection)** made a blocking pre-build premise check (§1.5).
- **§2.5(a)** closed on receipt of the addendum: A.4 → A.6 coherent.

## One-liners

- Every concession made the spec harder to game; the rebuttal rests on
  one dependency fact. (1, 2.2)
- Forward-only data makes deferral a verdict; verdicts get logged, not
  smuggled. (2.3)
- The defense is checkable or it is nothing. (2.5)
