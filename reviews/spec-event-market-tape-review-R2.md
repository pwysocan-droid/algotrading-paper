# Re-Review R2 — SPEC v2 + REVIEW-RESPONSE-R1 (event-market-tape)

Reviewer: Claude session, 2026-08-03. Now with **SPEC v2 in context**; the W3
addendum (`addendum-w3-and-queue-stubs.md`) is **still not provided** — the two
checks that depend on it are marked ⟨needs addendum⟩ and cannot be closed.

**Verdict:** v2 is a strong revision. It adopts all six R1 concessions and, more
importantly, **resolves the W2-deferral dispute the right way — by curation, not
by winning the dependency argument.** Three items remain: one citation error that
survived into v2 (ironic, given its grep-verify claim), one unresolved premise
gate (Q4), and one firewall question that needs the addendum. I greenlight the
**curated W1+W3** path conditional on those; I cannot clear the full bundle blind.

---

## 1. The deferral dispute — RESOLVED, but not by the rebuttal's logic

R1 said: defer the *broad* calibration census (Charter E §1.3's arm). The
R1-response rebutted: the duel needs W2, so defer-W2 ⟹ defer-W3 (which R1 never
argued). **My R2-blind answer was that the entailment is false** — by "same
markets, same timestamps," the duel needs a narrow forecast-linked slice, not the
broad tape.

**v2 makes the argument moot by doing the right thing anyway:** §2.2 collects
price snapshots **only for the curated universe** (text-intersecting OR W3-duel
markets, liquidity-floored), and §0.2 subordinates the calibration ledger to the
duel's scoring. **There is no longer a broad full-venue census to defer.** So:
- the rebuttal's specific claim ("the duel needs W2's broad data") remains false;
- but v2 no longer relies on it — it scoped collection to what W1+W3 actually
  use. Good adversarial convergence. **R1's deferral verdict is withdrawn** for
  the *curated* W2-as-scoreboard; it only ever applied to the broad census, which
  v2 removed.
- **§2.3's forward-only option value** (which I partially conceded) is now
  correctly captured: the curated set is collected *now*, forward-only, without
  the dead-charter census. Both concerns satisfied.

## 2. NEW — a v1.0 citation error survived into v2 (fix before commit)

v2 cites **"Art 4.2 conflict gate"** (§2.2, and the §A.3 shared screen). Grep vs
HEAD:
- **HEAD Art 4.2** = *"Autonomy is a state machine over durable artifacts"* — not
  a conflict gate.
- The conflict / auditor-conflict layer was **removed in v2.0** (CONSTITUTION
  header line 11; decision-log 2026-07-23 + the v2.0 rewrite: `conflict_check.py`
  and "old Article 4" cut). In v1.0, the conflict mechanism *was* Art 4.2 — so
  this is a **stale-snapshot citation**, the exact class this whole thread exists
  to kill, surviving into a spec that claims "grep-verify every citation."

**Consequence:** the operator-conflict exclusion v2 leans on (exclude markets
where the operator holds a view/position) has **no current constitutional hook.**
The hygiene is sensible, but it must be **proposed as a new rule with its own
rationale**, not cited to a removed article. Fix: drop the "Art 4.2" citation and
either (a) write the conflict-exclusion as a fresh spec rule, or (b) if it should
be constitutional, amend — don't cite a ghost.

## 3. Q4 — the real gate, unresolved and sharpened (premise check required)

R1/R2 flagged that the curation conjunction (text-relevant × liquid × no-conflict)
may starve to ≈∅. v2 §2.2 leaves the category list `[SET]` and suggests
"economics/policy/filings-adjacent." **But Charter T's *committed, collecting*
archive is SEC EDGAR 8-K — company-specific filings.** Liquid event markets
(Kalshi) skew macro / politics / weather. **The intersection of {8-K-covered
company events} ∩ {liquid event markets} is plausibly ≈ empty** — company 8-Ks
rarely have a tradeable event-market counterpart. v2's suggested "economics/
policy" universe is a *different* text universe than the 8-K archive actually
running, so either the benchmark doesn't serve the text source we collect, or the
Charter-T text universe is being quietly redefined.

**Required premise check, before building W1 or W3 (cheap, decisive):** take a
sample of the EDGAR 8-K archive and measure how many of those events have a
liquid, tradeable event-market counterpart on the tracked venues. If ≈0, W1's
benchmark rationale is void for the text source we hold, and the spec should
either change its text source or its claim. This is the CONJUNCTIONS-MULTIPLY-TO-
ZERO lesson pointed at the curation itself — measure the funnel before building on
it.

## 4. Q2 — firewall leak ⟨needs addendum §A.6⟩

§0.3 admits, as E² re-entry evidence, only **the duel's scored verdict** (never
the raw curve) — good, and §0.3+P1 pre-register the gross bias as non-actionable.
**But the duel measures FORECAST SKILL (engine Brier vs venue Brier), and Charter
E died on COST, not on skill.** If §A.6's "engine-wins" reading is raw Brier skill
(cost-blind), the firewall **leaks**: "my engine out-forecasts the crowd" becomes
a backdoor to E² while sidestepping the cost floor that actually killed it. The
firewall is leak-proof **iff** §A.6's engine-wins reading is *cost-net* (skill
that survives the Stage-0 cost floor), tying back to v2 P1. **I need §A.6 to
confirm.** This is the single most important open check.

## 5. Q3 — disk framework sound; numbers `[SET]`; suggested cap is safe

§2.4's framework is right (measured first-week rate sets retention; hard cap with
**pause-not-drop**; resolved-market compression). Numbers are `[SET]`, but the
suggested **≤2,000 open curated markets** at ~hourly cadence ≈ 2,000 × 24 × ~150 B
≈ **~2.6 GB/yr** — safe on the 38 GB box. **Conditionally passes:** fill the `[SET]`
figures and let the measured first-week rate confirm before any scaling.

## 6. §2.5 checks

- **(c) v2 P1 pre-registers the gross bias as non-actionable** — VERIFIED PASS
  (v2 §3.1 P1: "confirmed GROSS bias … actionable-nowhere (0.3 firewall)").
- **(a) §A.4 scoring undefined without resolution/mid data** — logically true
  (Brier needs outcomes + probabilities); ⟨verify with addendum⟩.
- **(b) §A.6 pre-names both readings** — ⟨needs addendum⟩.

## 7. Disposition

- **Withdraw** the broad-W2 deferral — v2's curation removed the census the
  verdict targeted. Good convergence.
- **Greenlight the curated W1 + W3-scoreboard**, conditional on all three:
  1. **fix the Art 4.2 citation** (removed-layer hook) — §2 above;
  2. **pass the Q4 premise check** (|8-K events ∩ liquid event markets| non-
     trivial) *before* building — §3;
  3. **§A.6 confirms the engine-wins reading is cost-net**, so the firewall
     doesn't leak skill into E² past the cost floor — §4.
- **Cannot fully clear** the bundle without `addendum-w3-and-queue-stubs.md`
  (Q2 / §2.5 a,b). Provide it and I close them.
- Everything else (`[SET]` cadence, categories, disk numbers, hours) is
  operator-values, not dispute.

**One-liner:** the census that had to be deferred was deleted instead — the right
fix; now the spec stands on one unmeasured premise (does our text even have a
market?) and one firewall question (is the duel's win cost-net?), and carries one
ghost citation that its own grep-rule condemns.
