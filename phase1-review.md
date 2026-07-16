# Phase 1 review — algotrading-paper

Written 2026-07-16, four days after the review date (2026-07-12,
curriculum anchor 2026-05-17 + 56 days). The lateness is itself
evidence and is treated as such in § 3.

**Verdict: extend Phase 1 — with terms.** Not a free extension: § 5
commits dated, falsifiable conditions under which the extension ends
in archive. This document argues extension; the operator signs it by
committing it (or edits the verdict before committing).

---

## 1. Gate math, honestly

| Gate | Requirement | Status |
| --- | --- | --- |
| 1 · Architectural | ≥95% uptime over prior 4 weeks | **PASSED** — 100.0%, ~8,000 consecutive VPS cron runs since 2026-05-23 |
| 2 · Promotion | ≥1 A/B-validated promotion (p<0.05, 100+ trades) | **UNPASSABLE AS POSED** — zero live trades ever; roster retired 2026-07-02; nothing registered to promote |
| 3 · Performance | positive 30-day P&L or written override | **FAILED** — no live P&L exists; the only P&L evidence (6-month backtest) is −$1,719 net |

One of three. Phase 2 is not close, and no honest reading says
otherwise.

## 2. What Phase 1 actually produced

**Method findings (real, defensible, earned):**

- Textbook Bollinger and MA-crossover lose money net of realistic
  constraints and fees on 6 months of 5-minute crypto data — every
  variant with n>100 negative (reports/2026-07-02-replay-6month.md).
  A clean negative is a result; PROJECT.md predicted exactly this.
- **Constraints dominate strategy.** 99.6% of candidate signals died
  on cooldown/exposure/concurrency before execution. Selection among
  strategies barely matters next to selection *within the constraint
  budget*. This redefines what a good candidate is: signal quality
  per constraint slot, not signal frequency.
- **An unconstrained backtest lies.** The first replay pass showed
  +$1,085; the same strategies under real constraints and fees showed
  −$782. The delta is the size of the lie. Caught before any decision
  was made on it — the discipline working.
- Free-tier scheduled infrastructure (GH Actions cron ~4% delivery,
  Pages deploys colliding) fails quietly; a $5/mo VPS with system
  cron delivered 100.0%. Boring infrastructure won.

**Market findings: none.** Zero signals, zero trades, zero live
feedback cycles. Ten weeks in, the project has learned nothing about
markets that a backtest couldn't have said — because only backtests
have run.

## 3. The pattern the review must name

The reviews that were supposed to catch drift didn't run: 2026-05-22
skipped, then a 47-day operator gap, then Fridays 07-03 and 07-10
missed, then this review itself written four days late. The W21
bear case predicted it: *"the infrastructure was the project."*
Every discipline that depended on the operator showing up failed
whenever the operator didn't. The one discipline that now runs
without the operator (nightly skeptic, deployed 2026-07-16, cron on
the VPS) worked on its first night. The lesson is structural:
**disciplines must be machine-scheduled or they are aspirations.**

## 4. Why extend rather than archive

1. **The expensive part is built and passing its gate.** The
   substrate (data layer, execution enforcement, replay with honest
   costs, audited LLM client, always-on skeptic) is exactly what the
   next phase needs, and it now runs unattended.
2. **The thesis is untested, not falsified.** The reframe's bet —
   LLM-surfaced candidates filtered by discipline — never ran. Weeks
   0–10 exercised the rigor half only. Archiving now judges the
   thesis on evidence that doesn't touch it.
3. **The learning failure has a specific, fixable shape** (§ 5):
   learnings live as prose, hypotheses have no due dates, and no live
   loop has ever closed. All three have concrete mechanical fixes.

The sunk-cost check, adversarially: "we built so much" is not a
reason to continue — it's the classic reason bad projects continue.
The reason to continue is (2): the animating hypothesis remains
untested and the cost of testing it from here is weeks, not months,
precisely because of (1).

## 5. Terms of extension — Phase 1b

Phase 1b runs **2026-07-17 → 2026-08-14 (4 weeks, hard stop)**.
Archive triggers automatically if any of these is unmet:

1. **A live loop closes within 7 days** (by 2026-07-24): the null
   variant (random signals, the placebo arm parked in roadmap.md)
   registered and running through signals.py → execute.py on the VPS
   cron — real rows in signals/decisions/trades. It will lose money
   slowly by design; its job is to prove the loop and give the A/B
   comparator its baseline arm.
2. **An LLM-surfaced candidate roster is registered within 14 days**
   (by 2026-07-31): Claude-proposed candidates, replayed under
   constraints+costs, best 2–3 registered live alongside null.
   The fitness function is § 2's finding: expected edge per
   constraint slot.
3. **Learnings become data, not prose, within 14 days**: a learnings
   ledger (structured: claim, status validated/pending/falsified,
   evidence link, next check date) extracted from decision-log.md
   via complete_structured(), surfaced on a dashboard page, checked
   by the nightly skeptic. Every falsifiable hypothesis in the log
   gets a due date; overdue = surfaced.
4. **Reviews stay machine-scheduled.** Nightly skeptic (running) and
   the Friday review generated by cron, operator edits rather than
   authors. A missed Friday in Phase 1b is an archive trigger, not a
   pending item.
5. **Phase 1b review 2026-08-14** measures: null-variant trade count
   (target: enough to prove the pipeline, ~100+), candidate-vs-null
   A/B state, and ledger discipline. Gate 2 is re-posed against the
   new roster. Two consecutive missed terms at any point = archive
   without a further review.

## 6. What does not change

Capital model, Phase 2 gates and exits, the eight-table schema,
no-online-ML, no-LLM-as-oracle: all locked per 2026-04-26 entries.
The null variant and LLM-candidate roster operate inside the same
$200/$1,000/5-position ceilings. Nothing in this review touches
real money; gate math above shows Phase 2 is not on the table.

---

paper-api.alpaca.markets/v2/orders · phase 1 review · verdict: extend with terms

[github.com/pwysocan-droid/algotrading-paper](https://github.com/pwysocan-droid/algotrading-paper)
