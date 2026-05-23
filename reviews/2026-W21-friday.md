# Friday adversarial review — 2026-W21

algotrading-paper / friday bear-case · 4G methodology

Week under review: **2026-05-17 → 2026-05-23** (curriculum days 1–7).
Forced steelmanning per `reviews/templates/friday-bear-case.md`. The bear
case only. No hedging, no "on the other hand." The bull case lives in
other conversations.

---

## The bear case, in one paragraph

Seven days into an eight-week curriculum, this project has produced
**zero signals, zero trades, zero decisions, and zero logged LLM
calls** — and spent the entire week on infrastructure that exists to
support a research question it has not yet begun to ask. The cron got
migrated, the bars got backfilled, the surface grew three new features,
and the gate math got recalibrated twice — all real work, all of it
*downstream of nothing*, because no strategy is registered and no trade
has been simulated live. Worse: the one discipline designed to catch
exactly this drift — the weekly adversarial review — **did not run last
week** (the 2026-05-22 review was skipped), so this is review #1, a day
late, with no prior baseline to measure degradation against. A project
whose stated edge is "epistemological aggression with methodological
rigor" has, at the one-week mark, logged its rigor in a `runs` table
that says `trades: 0` and exercised its epistemology through an LLM
client whose audit table (`llm_calls`) is **empty**. The substrate is
now excellent. The experiment has not started.

---

## Attack vectors

**1. The week bought no movement on the only question that matters.**
`signals=0, trades=0, decisions=0`. Day 7 of 56. The curriculum's
entire purpose — accumulate ~300 trades/variant to draw a
statistically defensible conclusion — has a numerator of zero and no
denominator yet. Every artifact shipped this week (VPS, backfill,
session markers, punch list, cache-busting, queue files) is scaffolding
for trades that do not exist. A reasonable outside observer would say:
this is a project that has gotten very good at preparing to start.

**2. The methodology that was supposed to catch #1 didn't run.** The
4G weekly adversarial review was committed in the 2026-04-26 reframe as
"the operational mechanism that catches both failure modes." There is
**no `reviews/*-friday.md` file before this one.** The 2026-05-22
review — due during the week under review — was skipped. The
drift-detection apparatus the methodology depends on (compare this
week's bear case to last week's; flag softening) is *inoperable on its
first run* because the discipline wasn't followed when it was first
due. A methodology that doesn't run cannot degrade gracefully; it
simply isn't a methodology yet. It's a template.

**3. The epistemological backbone is unmeasured — and this review
proves it.** The reframe's central claim is Claude-as-backbone:
"a synthesis engine applied from Week 0, an adversarial reviewer
applied weekly." The `llm_calls` table — built specifically to make
that backbone auditable for cost and drift — has **zero rows**. No
synthesis, no review, no extraction has been logged through
`claude_client.py`. This very document is being produced in Claude
Code, outside the audited client, so it will not appear in `llm_calls`
either. The project committed to measuring its unfair advantage and
has measured none of it. If someone asked "show me the evidence the
LLM backbone is doing work," the honest answer is an empty table.

**4. A week of infrastructure is the most respectable way to avoid the
scary work.** The cron-reliability investigation was thorough, correct,
and well-documented — and it was also a renewable supply of urgent,
legible, *safe* work that postponed the genuinely uncomfortable task:
committing to a strategy roster and watching it lose money in public.
Infrastructure has a seductive property — it always needs more of
itself. There is always another row to add to the surface, another
reliability number to chase. The bear case is not that the VPS work was
wrong; it's that the project found seven days of it precisely when the
alternative was the Week 2 roster decision that the reframe staked its
falsifiable hypothesis on.

**5. The curriculum clock was redefined the same week it became
unfavorable.** The 2026-05-17 entry moved the curriculum anchor to
"first successful cron run," which conveniently means the dismal
GitHub-era weeks don't count against the 8-week timeline. The stated
reasoning (measure operational data, not wall-clock) is sound. But the
*pattern* — discovering a metric is unflattering, then changing what
the metric measures — is the exact move `philosophy.md`'s "knowledge
failure" section warns against, and it was applied to the project's own
timeline. The anchor moved the goalposts toward the operator. That it
was logged doesn't make it not goalpost-moving; it makes it
*documented* goalpost-moving.

**6. The surface grew; it was supposed to shrink.**
`surface-philosophy.md` is explicit: "the surface gets less, not more,
as the project matures... If a future revision adds a zone, it has to
also remove one." This week added session markers, a bar-coverage row,
a whole punch-list page, and `cron_interval` plumbing — and removed
nothing. The surface is accreting features in direct violation of its
own founding discipline, at the precise moment (pre-data) when there is
the least actual information to display. A surface with more elements
and zero trades is decoration wearing the costume of instrumentation.

**7. The VPS is a fresh single point of failure, and its first day
already surfaced a data-integrity hazard.** GitHub's unreliability was
replaced with a $5.83/mo box that has: one writer, one deploy key, a
manual 30-minute setup nobody else can reproduce from memory, no
monitoring beyond a 90-minute stale indicator, and a single-writer
discipline that was discovered *by hitting the bug in production*
during the backfill. The migration's own rollout corrupted a commit
(binary `trader.db` conflict) and had to be redone on the VPS. "Visible
failure is the gift," the decision-log says — but a failure mode found
on day one by accident is not a gift, it's a near-miss that happened to
be cheap this time.

**8. The same un-actioned items keep appearing on every surface.** The
`.env.template` exposure decision-log entry is flagged in **two
places** — `pending.md` (kind=log) *and* `decision_log_queue.md` — and
remains unwritten weeks after the incident ("caught, rotated,
unlogged"). The future-self letters for the 2026-04-26 entries have
been "open" since 2026-04-26 — the project's entire life. Items that
recur across surfaces without being closed are not "tracked"; they are
*dismissed in slow motion*. The punch list made them more visible
without making them more done.

---

## Punch list, ordered by urgency

1. **Register a strategy or admit the curriculum is paused.** The Week 2
   roster decision is the falsifiable hypothesis from the reframe and it
   is the bottleneck for every downstream layer. Until a variant is
   registered, days 8–56 accumulate zero trades and the 8-week clock is
   burning on an empty registry. This is the only urgent item; the rest
   are hygiene.

2. **Run the adversarial review weekly, on time, from now on.** This is
   review #1 of a discipline that was due last week. The next one
   (2026-05-29) must exist, and it must compare to this one. If it
   slips, the methodology is dead and the reframe's "rigor" half has
   failed its own falsifiable test.

3. **Log the backbone, or stop claiming it.** Either route the
   adversarial reviews and synthesis through `claude_client.py` so
   `llm_calls` reflects reality, or write a decision-log entry conceding
   that the audited-LLM-backbone telemetry is aspirational and the
   reviews happen out-of-band. One or the other — the current state
   (claimed but unmeasured) is the worst of both.

4. **Write the `.env.template` exposure entry.** It has been flagged
   twice and deferred for weeks. Close it this weekend or delete it from
   both surfaces and admit it's not going to be written.

5. **Resolve the surface's accretion.** Per `surface-philosophy.md`,
   removing-one-when-adding-one. Either retire a surface element or
   write a decision-log entry explicitly suspending that discipline with
   a reason. Don't let it erode silently.

6. **Single-writer DB entry + VPS runbook.** The single-writer
   discipline is queued; write it before Week 4 tuning makes local DB
   mutation tempting. And the 30-minute VPS setup needs to be
   reproducible by someone who isn't the operator on the night they did
   it — the `vps/README.md` is a start; confirm it's actually sufficient.

---

## Calibration note

**There is no prior bear case to compare against.** This is the
methodology's first artifact, and the comparison the 4G drift-check
depends on — "is this week's bear case softer than last week's?" —
cannot be performed, because last week's review was never written. That
absence is itself the first calibration data point: the operator set up
the discipline (the template exists, committed Week 1) and then did not
execute it when it first came due. The proto-version of the
"recurring-attack-vector" check still applies, though: items open across
the project's whole life (future-self letters since 2026-04-26;
`.env.template` entry double-flagged) are the early-warning shape of
exactly the un-actioned-recurrence pattern the methodology is meant to
escalate.

This first review sets the floor. If it is soft, every subsequent
review degrades from a soft baseline. So the standard it sets is
deliberately harsh: a project that is excellent at infrastructure and
has not yet placed a single trade, one-eighth of the way through its
own clock, with its central methodological commitment (the weekly
review) already having missed its first scheduled run and its
epistemological commitment (the LLM backbone) showing zero telemetry.

> **If the project registers a strategy roster and logs its first live
> paper trade before next Friday, the bear case weakens materially.**
> **If next Friday arrives with `trades` still at 0 and no 2026-05-29
> review written, the bear case strengthens to: the experiment was never
> going to start, and the infrastructure was the project.**

---

paper-api.alpaca.markets/v2/orders  ·  4G adversarial review · drafted in Claude Code (not logged to llm_calls — see attack vector 3)

[github.com/pwysocan-droid/algotrading-paper](https://github.com/pwysocan-droid/algotrading-paper)
