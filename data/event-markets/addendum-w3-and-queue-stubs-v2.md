# ADDENDUM v2 + QUEUE STUBS — W3 forecast arm & queue entries

Status: **DRAFT v2 — externally drafted (chat, 2026-08-03). PATCH-R2
applied (PATCH-1: CX-1 re-grounding; PATCH-3: cost-net A.6). Sent for
formal closure of review item §2.5(a). Step zero before commit: diff
against repo HEAD; grep-verify citations.** On commit: §A amends
`data/event-markets/SPEC.md` (v2.1); §B/§C enter the hypothesis queue
as stubs (freeze on commit; revisions logged, never edited in place).
Queue count after commit: [verify ≤ 12].

> **Committed 2026-08-03 with SPEC v2.1.** §2.5(a) closed by re-review R2:
> A.4's per-bucket tail-calibration error is exactly the per-bucket margin
> A.6's cost-net firewall compares to measured cost, under the §3.2 power
> bar. Follow-up: register §B/§C in build_queue.md and verify the ≤ 12 cap.

---

## §A — W3: LLM forecast arm (amends event-market tape spec)

**Priority 1. Zero capital, zero slot; runs on W1/W2 infrastructure.**

A.1. **Question.** Does the program's LLM engine, given only public
information before market close, produce probability forecasts better
calibrated than the venue's money-weighted crowd — especially in the tail
buckets where the documented bias lives?

A.2. **Mechanism claim (Art 0.2(a) analogue).** The counterparty on thin
event venues is recreational flow; the engine reads systematically what
that flow reads casually. If the engine cannot beat the crowd here, at
zero fees, no E′ trading premise survives — this arm is the *gate in
front of* any future E′ pre-reg.

A.3. **Protocol.** For every market in the W1 catalog meeting screen
[SET: category inclusions/exclusions — plus **rule CX-1, defined in
SPEC §2.2** (operator-conflict exclusion; spec-local, no constitutional
hook claimed)]:
- at fixed offsets before close ([SET: e.g. 72h and 24h]), the engine
  commits a probability to `event-shadow.jsonl` alongside the venue mid
  at the same timestamp;
- prompt template, model version, and retrieval scope are **pinned and
  versioned**; a model/prompt change opens a new ledger column, never
  overwrites — forecasts are forward-only, no backfilling ever;
- forecasts are committed before resolution and hash-logged with the
  nightly git commit (tamper-evidence for free).

A.4. **Scoring (pre-named).** Brier score and tail-bucket calibration
error, engine vs venue mid, on the same markets, same timestamps —
scored against realized resolutions from the W2 ledger (SPEC §2.5/§2.6).
Small-sample quarantine: n < 30 resolutions per bucket makes no claim;
tail-calibration claims additionally carry the SPEC §3.2 power bar.
Decidability target: first scored report at [SET: __] resolutions or
90d, whichever later.

> **Two-column scoring (PATCH 2026-08-03).** The duel ledger carries
> **separate columns per class (OUTCOME, MENTION)**, scored identically,
> regardless of which class governs §5. Pre-named cross-reading: engine
> wins MENTION but loses OUTCOME → the engine's measured edge is
> Keynesian (text→text), not fundamental (text→world) — recorded as a
> finding; a MENTION-only win licenses at most a MENTION-scoped E²
> premise, which additionally carries the mention-market dispute tail
> (worst-in-category; priced per Art 2.10(b) before any such pre-reg).

A.5. **Blind prediction P4 (commit before first forecast).** Operator's
predicted outcome: engine Brier vs venue Brier [SET: direction and
margin], and whether the engine's tail calibration beats the venue's
[SET: yes/no, magnitude]. The registry's law is that predictions miss.

A.6. **Pre-named readings (cost-net; R2 fix).** The duel is scored at
zero fees, so a gross win proves forecast SKILL only — and Charter E
died on COST, not skill. Three readings, pre-named:
- **Engine loses gross** → the engine's limit is measured;
  E′-via-prediction is dead on arrival; only underwriting-shaped E′
  premises remain admissible.
- **Engine wins gross but not net** — tail-bucket margin over the
  venue ≤ that venue's measured all-in round-trip cost in those
  buckets (Stage-0 numbers for Kalshi; fresh measurement required per
  venue before this comparison is made) → the GATE is passed but no
  E² premise exists: skill that cannot out-earn the takeout is the
  Charter E kill, re-confirmed at the forecast layer. Recorded as a
  finding; not re-arguable without a venue whose measured cost is
  lower.
- **Engine wins net** — margin exceeds the venue's measured all-in
  tail-bucket cost with the SPEC §3.2 power bar met → that finding,
  and only that finding, is citable as the E² premise (SPEC §0.3
  firewall, cost-net reading).
The cost side of the comparison uses MEASURED venue numbers, never the
fee schedule as documented — the Stage-0 discipline (verified against
executed mechanics) carries over.

> **Reviewer refinements (R2, recorded 2026-08-03; for the build):** (1)
> within the tape, §0.4 forbids orders and the Stage-0 cost was a LOWER
> BOUND (quoted spread + fee, no executed verification), so: engine loses
> vs lower-bound cost = definitive kill; engine wins = PROVISIONAL, the
> final executed-cost check belongs to the E² stage that places orders.
> (2) model-version pinning inherits the fee-schedule-drift caveat — a
> hosted model can change behind a stable name; pin a dated snapshot and
> treat silent backend drift like the §4 fee check.

## §B — Queue stub: corporate_action_oddlot_arithmetic

**Priority 2. Premise check ≈ one weekend; no build before it reports.**

- **Lineage:** Graham special-situations; prediction-free contractual
  arithmetic. Descends from no dead lineage (first non-crypto-venue,
  non-OHLCV equity structure proposed).
- **Mechanism:** odd-lot tender/exchange-offer preference clauses
  contractually exclude size; the acquirer is forced to pay the stated
  price. Retail scale is the admission ticket, not the handicap.
- **Shape:** bounded (max loss = position, admissible Art 2.2); the
  "tail" is deal-break before settlement — priced from mechanism (offer
  withdrawal terms × stressed time-to-flat), never from deal-break
  frequency history (Art 2.3).
- **Premise check (blocking, pre-build):** count qualifying US events
  over trailing [SET: __ months] from public filings; distribution of
  gross spread per event; broker eligibility/fees on our account
  (verify by executed mechanics, not documentation). Kill at premise:
  events/year × net spread × deployable capital per event < [SET: $__/yr
  floor] → dead at Stage 0, recorded with the numbers.
- **Conjunction discipline:** state why screen conditions (odd-lot
  clause present × spread > costs × account-eligible) are not
  anti-correlated before predicting cadence.
- **Blind prediction:** [SET: qualifying events/yr, median net spread].
- **Reviewer note (R2):** likely killer is capacity (a few odd-lots per
  deal → tiny $/yr); the kill floor catches it. Sound framing.

## §C — Queue stub: dex_lp_as_underwriting_book

**Priority 3. New input space: contract structure itself (Art 0.2).**

- **Lineage:** options-underwriting (Charter B′ kin), NOT the dead
  crypto-OHLCV foundry — the input is the pool contract's fee/LVR
  structure, no price-derived signal anywhere in the entry rule.
- **Mechanism:** a concentrated LP position sells optionality to
  arbitrageurs for fees; the Book question verbatim (Art 2.1): is the
  fee yield fair pay for bearing LVR, tail included?
- **Shape:** bounded by construction (max loss = stake; admissible
  Art 2.2). Venue tail = contract/bridge/custody failure = 100% of
  on-venue capital → the Art 2.7 venue test and ≤5%/venue sizing
  (Art 2.4) apply before any deposit.
- **Premise check (blocking, zero-risk):** shadow always-LP arm (B′
  pattern) on [SET: pool(s)] — log fee accrual vs computed LVR daily,
  no deposit. Literature null stated up front: LVR ≥ fees on major
  pairs is the published default; the burden is on the data to refute
  it. Kill at premise: after [SET: __ d] shadow, net (fees − LVR) ≤ 0
  at [SET: p __] → dead, recorded.
- **Blind prediction:** [SET: net fee−LVR sign and bps/day].
- **Note:** queued LAST deliberately — operationally heaviest (keys,
  gas, contract risk) and blocked behind its own venue-robustness test.
- **Reviewer note (R2):** the LVR computation is the load-bearing
  measurement — validate against the closed-form / a simulation, and
  model concentrated-range fee mechanics correctly (fees only in-range),
  before trusting the premise check. Otherwise strong (states the null,
  burden on the data).

---

## One-liners

- The duel gates E′: beat the crowd at zero fees before proposing to
  beat it net of fees — and only a NET win argues E². (A.6)
- Skill that cannot out-earn the takeout is the same death at a new
  layer. (A.6)
- Forecasts are commits, never memories. (A.3)
- Odd-lot clauses make small the ticket in, not the tax. (B)
- An LP position is an insurance book with the premium set by strangers —
  measure before underwriting. (C)
