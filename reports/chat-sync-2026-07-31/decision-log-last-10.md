# decision-log — last 10 entries (as of 2026-07-31)

## 2026-07-23 — Candidate #1 spec: variance-risk-premium harvester (paper-first, fast)

The machine's first real position, pre-registered (book/pre-reg-variance-
premium.md): an "underwriter with a brain" — sell defined-risk equity
option credit spreads (bounded max loss = strike width − credit, admissible
under 2.2) to harvest the variance risk premium (options systematically
overpriced — the evidence-aligned, retail-accessible risk-transfer edge),
with the LLM's differentiating job being the STAND-ASIDE rule: read the
information surface and refuse to write insurance into a known catalyst
(earnings, FOMC, live tail narrative) that static IV-rank misses. That
context judgment is the decaying LLM arbitrage; per Art. 0.4 speed captures
it via a fast loop. Honest capital constraint surfaced: $200 is too small
for a 5%-sized spread, so PAPER-FIRST (Alpaca paper options, forward,
riskless, starts now) validates the loop; live gated on capital sizing +
options approval + a survived paper kill. Also added CONSTITUTION 0.4:
speed is an edge because the edge decays; the solvency cap licenses fast
small live/paper bets over slow in-window backtests.

## 2026-07-24 — VRP harvester built + first live paper run (fast loop working)

Candidate #1 machine (scripts/vrp_harvester.py) runs end-to-end on the
Alpaca paper account (level-3, $100k): stock bars → put chain → ~1-SD-OTM
strike selection → richness gate (credit/width) → LLM stand-aside → multi-
leg paper order path. First run: at the real 20% richness bar it SKIPPED all
three indices (premium genuinely thin — SPY/QQQ/IWM credit 4-15% of width),
which is the discipline working (a good underwriter won't sell cheap
insurance). A forced-low-threshold test showed the LLM stand-aside FIRES.

HONEST FINDING (the fast loop earned its keep): the LLM stand-aside is too
blunt to be useful yet — it (a) defaults to generic caution because every
5-week window has a CPI/FOMC, so it would stand aside ~always, and (b) is
guessing future macro dates it can't know from training. #1 next build:
feed a REAL catalyst calendar (FOMC/CPI/jobs published dates + earnings) and
refine the logic to the correct thesis — routine scheduled events are
already priced into IV (don't stand aside), stand aside only for UNDERPRICED
tail risk / extraordinary events. The machine currently errs safe (writes
nothing), the right direction to err, but not yet earning.

Operator to-do: NONE for the paper loop (runs riskless now). LIVE later
needs (a) options approval on the live account (currently level None) and
(b) a Book capital level where 5% is a real spread ($200 too small). E-1.0
stays shelved.

## 2026-07-24 — VRP machine fully validated end-to-end (paper order path confirmed)

v2 (real macro calendar + refined stand-aside) validated: at the real 20%
richness bar it skips (premium thin); at forced-rich it correctly decides
WRITE, reasoning that scheduled CPI/FOMC/NFP are already priced and no
extraordinary tail is present. Paper multi-leg order placement CONFIRMED
(Alpaca paper accepted a SPY 705/700p spread, status 200); test order
cancelled + ledger reset afterward. The brain discriminates and the plumbing
works.

ONE GAP before autonomous running: the machine OPENS positions but does not
yet MANAGE them — no profit-take (~50% of credit), no close-near-expiry, no
breach handling. Opening without managing is a broken loop; a faithful paper
forward test needs the exit half. NEXT BUILD: position management + then a
daily paper schedule (writes when genuinely rich, manages exits). A live
news feed for real-time tail detection is v3 (current stand-aside is
training-knowledge-limited — it won't catch a crisis it doesn't know about).

Capital sweet spot (operator Q): defined-risk VRP is a breadth game, not a
size game. ~$25k functional floor (below it the 5% cap forbids
diversification); $50-100k target sweet spot (real breadth, no liquidity impact on index
options). CORRECTED return expectation (an earlier $5-15k/yr figure was too
rosy): on TOTAL book capital ~5-8%/yr, of which ~half is just T-bill yield on
the ~75% idle cash (solvency cap deploys only ~25%); the VRP EDGE adds only
~2-4 points on top, with a fat NEGATIVE left tail (vol-spike years lose). Any
clean double-digit book return should trigger skepticism. Scales to
several hundred k bounded by drawdown tolerance, not liquidity. Sequence:
paper -> small live ($10-25k) -> sweet spot ONLY after the forward record
clears the kill. Speed on the loop, patience on the capital.

## 2026-07-24 — VRP machine complete and SCHEDULED (forward record begins)

Position management + account reconciliation added: manage_positions closes
each held spread at 50% of credit captured or DTE<=10, trusting actual
GET /v2/positions (not the ledger's intent) so it never closes a phantom;
open orders that never fill are marked 'unfilled', not force-closed. Full
loop verified end-to-end (open 200, manage/close logic, P&L, ledger).
SCHEDULED: vps/cron-vrp.sh runs weekdays 15:30 UTC (paper, PLACE mode) —
manages opens, writes when premium is genuinely rich and the stand-aside
clears, commits its ledger+report so the operator can watch. The machine is
now RUNNING and building its forward paper record. Currently writes nothing
(premium thin) — correct. Next builds (not blocking): live news feed for
real-time tail detection (v3), and surfacing the VRP book in the digest.

## 2026-07-31 — Strike-distance calibration: closer strike is a mirage; TLT/EEM dropped

Backfilled the new additions (7 ETFs × {1-SD, 0.5-SD}, real Alpaca option closes,
Feb 2024–Jul 2026) — closing the gap that DIA/GLD/TLT/EEM and the 0.5-SD arm had
zero historical calibration.

**Key finding (decision-grade, counterintuitive).** The 0.5-SD (closer) strike
clears the flat 20% gate ~10× more often (QQQ 3%→32%, GLD 2%→39%). That is a
mirage: richness = breakeven loss-rate, and a 0.5-SD strike carries ~31%
assignment odds vs ~16% at 1-SD, so 20% is fair at 1-SD but far too cheap at
0.5-SD. Held to each strike's OWN delta-fair bar, the conservative 1-SD strike is
fairly paid MORE often (4–9% of days) than the aggressive 0.5-SD (1–3%). Moving
the strike closer does not create edge — the market prices every moneyness
efficiently; the closer strike merely looks busier against a bar that's too low.

**Actions:** (1) keep the conservative 1-SD strike live — the "trade more"
shortcut would underwrite at unfair prices; (2) drop TLT (0% fairly paid at
either distance) and EEM (illiquid, n as low as 112) from UNDERLYINGS → keep
SPY/QQQ/IWM/DIA/GLD; (3) keep the 0.5-SD shadow arm running forward — richness is
calibration, only the forward shadow P&L measures the physical-vs-implied gap
that is the sole remaining edge. Calibration, not a P&L backtest (benign window).

## 2026-07-31 — Feedback incorporated: self-referential fair-bar; TLT thread

Operator feedback on the strike-distance finding (correct, incorporated):
- **The delta-fair bar was partly self-referential.** N(-1)=16% / N(-0.5)=31%
  come from the same realized-vol Gaussian that PLACES the strike, so "richness
  beats the delta bar" is nearly circular. Fixed the shadow readout
  (scripts/vrp_shadow_report.py) to judge realized breach against the MARKET's
  own priced breakeven (richness = credit/width, from real quotes), and to lead
  with realized P&L as the only verdict. The N(-sd) number is retained only as a
  labeled self-referential reference.
- **No profitability is established** — only "not obviously mispriced." The
  forward shadow P&L is the sole real test and has not spoken (first resolutions
  ~2026-09-04). Verdict on the book: PENDING.

**Open thread — TLT (do not treat the cut as the answer).** TLT was never fairly
paid at 1-SD (0%) *or* 0.5-SD (1.7%); median richness ~3%. Hypothesis to pull,
not bury: the equity variance-risk-premium may simply not exist in bonds — bond
option vol is rate-driven and may be fairly-to-cheaply priced, i.e. there is no
premium to sell there (and possibly vol to BUY). Alternatively an artifact of a
$2 width on a low-vol underlying. Either way it is a *finding about where VRP
lives*, not mere universe hygiene. Parked as a lead for the continued search
(Art 3), not closed.

## 2026-07-31 — Amendment 1 (v2.1) adopted after adversarial review

RECALIBRATION.md (Amendment 1) reviewed adversarially first (RECALIBRATION_REVIEW.md),
then adopted in corrected, scoped form.

**Reviewed and corrected before adoption:**
- **§2.9 percentile gate was the self-referential trap re-introduced** — a pure
  trailing-percentile gate fires ~(100−N)% of days regardless of fairness, and
  "correctness = reaches n≥30" is circular (always-write maximizes n). Reframed
  on adoption: the percentile gate is NOT a fairness test (ruin-avoidance stays
  in 2.2/2.4); it is a forward-tested deployment-TIMING hypothesis with a
  principled (not P&L-tuned) threshold + absolute floor + the shadow always-write
  arm as mandatory control. n≥30 is a decidability target, not a success metric.
- **Citation errors fixed:** the draft cites "Art 8" (governance is Art 6) and
  "rewrite Art 0.3" (the prohibition is 0.2; 0.3 is the generative mandate).
  Bounding applied to **0.2**, generative mandate 0.3 left intact.
- **2.10** adopted with an added venue-robustness caveat (event venues carry the
  100%-of-venue tail per 2.7).
- **Charter S / the Service REJECTED** — resurrects what v2.0 removed in full and
  contradicts the operator's standing "not publishing" direction. Not implemented.

**Adopted (v2.1):** 0.2 bounded to price-derived signals on liquid instruments
(untested input spaces — text/events/positioning/structure — in scope under the
same unamended discipline, each naming its mechanism); 2.9 (gate re-derivation);
2.10 (event contracts). Engine and brakes unchanged; only the fuel. No Book
position open at adoption, so 6.1's same-day bar did not bind. Opening charter
pair per §4.1: B′ (re-derived Book gate) + T (text signals) — the two pre-regs
drafted next; Charter T data collection blocked until its pre-reg is committed.

## 2026-07-31 — Forensic adjudication: the Service kill is logged (Finding a)

Task: adjudicate whether the "Service" removal was documented, blocking for any
Charter S revival. **Finding (a): a logged kill exists.**
- v1.0 (9a2bbec88, "The Book & The Service") committed the Service as Article 3;
  amendment governance was Article 8 (8.1/8.3); the mispricing prohibition was
  0.3. v2.0 (bdf0f70f1) removed the Service and renumbered (8→6, prohibition
  0.3→0.2, 0.3 reused for the generative mandate).
- The removal is documented at the dated decision-log entry **"2026-07-23 —
  Course correction: trading machine, not a publishing service,"** with operator
  rationale and an explicit list of what was cut (Article 3 publishing,
  Cochrane/UL sequencing, the auditor-conflict layer, conflict_check.py, service/).

**Consequence:** Charter S rejection STANDS on a logged operator kill; a Service
revival requires its own proposal that answers the 2026-07-23 entry.

**Version provenance of RECALIBRATION.md citations:** all three errors trace to a
single cause — RECALIBRATION was drafted against **v1.0** (9a2bbec88), not the
committed v2.0/v2.1. "Art 8.1/8.3" = v1.0's amendment article; "rewrite Art 0.3
(prohibition)" = v1.0's 0.3; "Charter S / the Service" = v1.0's Article 3. Every
citation matches v1.0 and is superseded in v2.0. Not an undocumented removal
(finding b) and not a chat-only invention (finding c) — a stale-snapshot draft.

## 2026-07-31 — Charter E Stage 0 built (measurement); spends no charter slot

Adversarial review first (RECALIBRATION_REVIEW.md, Charter E addendum): Stage 0
survives as a measurement with corrections — kill on absolute cost not the racing
magnitude (S0-1); snapshot-only, executed-order fee-verification and time-to-fill
struck as trading-incompatible, cost reported as a LOWER BOUND (S0-2); venue-
failure tail added per 2.10b (S0-4); N/days pinned (S0-5). §1.3 calibration
deferred with computed per-bucket n (~750 resolved contracts for a 2pp tail bias,
~3,400 for 1pp) as a hard precondition on Stage 1 (C-1..C-5).

**Sequencing reading (operator-confirmed):** Stage 0 is a read-only venue
cost-floor measurement/premise-check and **spends no charter slot** — it may kill
Charter E before E ever activates. The two-charter cap (§4.1: B′+T active) binds
at **Stage 1** activation, not at Stage 0.

Built (measurement only, no trading, no order code): venues/kalshi/ read-only
adapter (public /markets, no auth), snapshot.py (own gitignored kalshi.db — raw
snapshots NEVER committed, heeding the trader.db bloat), floor_report.py ->
reports/event-venue-floor-{date}.json. cron-kalshi.sh: snapshot 3×/day, report+
commit daily. Stage 0's report alone decides whether Charter E exists further.

## 2026-07-31 — Charter E DEAD at Stage 0 (both sides); cron sunset recommended

Stage 0 venue cost-floor study adjudicated per-side on the full Kalshi
open-market population (reports/event-venue-floor-2026-07-31.json). BOTH sides
die on cost — the honest negative the review predicted (S0-3):
- **(a) longshot-sell (<10c):** all-in cost 2c (<5c bucket, ~80% of price, fee
  floor alone) to 8c (5-10c, 107%). Plausible 1-2pp bias (1-2c) dwarfed. DEAD.
  Racing-takeout death reproduced on an order-book venue — the venue fee IS the
  takeout, ~80% at 2.5c vs parimutuel racing's 15-20%.
- **(b) near-certainty-buy (>90c):** all-in 3c (0.95-1.00, tightest) to 5c
  (0.90-0.95). Even 3c exceeds a 2pp edge (2c) by 1.5x; aggregate 5c = 2.5x a
  2pp / 5x a 1pp edge. DEAD on cost. Population thin (397 mkts >=90c) but that is
  NOT the decisive kill — cost is.
Both epitaphed in reviews/foundry/dead-ideas.json (charter-E · E1-longshot-side,
E1-near-certainty-side) + a failure lesson. **Charter E is dead at Stage 0.** The
buy-side-only pre-reg revision (conditional on (b) surviving) does NOT happen.

**Process note (caught, fixed):** the adapter's max_pages=30 default silently
truncated the population and hid the entire >90c tail — read as "no near-certainty
market" when it was just capped. Fixed (max_pages 30->800), re-measured. The
no-silent-caps lesson, in our own code.

**Cron sunset — RECOMMENDATION (operator decides, per instruction):** STOP the
Kalshi snapshot + report crons. The kill is structural (venue takeout) and will
not change, so further collection informs no decision; and post-truncation-fix
each snapshot writes ~800k rows (~80 MB) 3x/day — pointless disk accumulation.
KEEP venues/kalshi/ (adapter/report) as a reusable calibration instrument for any
future event-venue question. If left running, the cron-gc.sh >=80% disk guard is
the safety net. To sunset: remove the two cron-kalshi lines from the crontab.
