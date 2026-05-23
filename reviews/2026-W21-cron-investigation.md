# Cron invocation investigation — 2026-W21

algotrading-paper / cron investigation · diagnostic

Question: why is GitHub Actions invoking at **3.97%** of the documented
`*/5` cadence (68 of 1,712 over 6 days) when published free-tier
averages are 70–85%?

Diagnostic pass only — no workflow changes (operator instruction).
Generated 2026-05-23.

---

## § 00 — Verdict up front

Every **config-level** cause is ruled out. The cron expression is
correct, there are no path/branch filters, the concurrency group never
collides (runs are 30s and ~2h apart), and runtimes are nowhere near
the timeout. The repo is public, so Actions minutes are unlimited —
billing/quota is not the constraint.

The drops are **GitHub-infrastructure-side and silent**: the ~1,640
missing invocations were never created as run records (not logged as
"skipped" or "cancelled" — they simply never happened). The single
specific driver consistent with all evidence is the **`*/5` frequency
itself** — the most aggressively deprioritized schedule interval GitHub
offers. The published 70–85% figures are typically measured on hourly-
or-slower schedules; sub-hourly schedules on public repos sit in a much
worse regime.

The clinching evidence is in § 06 (minute-of-hour distribution).

---

## § 01 — Cron expression

```yaml
on:
  schedule:
    - cron: '*/5 * * * *'
  workflow_dispatch:
```

Confirmed `*/5 * * * *` — every 5 minutes, no typo, no unusual field.
This is the **shortest interval GitHub allows** and (per GitHub docs +
widespread community reports) the one most subject to delay and
dropping. **Not misconfigured, but it is the highest-risk setting.**

---

## § 02 — Concurrency settings

```yaml
concurrency:
  group: fetch-and-commit
  cancel-in-progress: false
```

A concurrency group *can* cause skips: if a run is in progress when the
next trigger fires, the new one queues; if a third arrives, GitHub keeps
only one pending run and drops the rest.

**Not a factor here.** Runs complete in 27–37s (§ 03) and arrive ~2h
apart (W21 reliability report). They never overlap, so the concurrency
group never has anything to serialize or drop. `cancel-in-progress:
false` is also the safe setting (it wouldn't cancel a running fetch).
Ruled out.

---

## § 03 — Workflow runtime vs the 4-minute timeout

8 most-recent completed runs, via the timing API:

| Run | Duration |
| --- | --- |
| 1 | 31s |
| 2 | 27s |
| 3 | 30s |
| 4 | 32s |
| 5 | 34s |
| 6 | 30s |
| 7 | 27s |
| 8 | 37s |

`timeout-minutes: 4` (240s). Runs use **~12–15% of the budget.** No run
approaches the timeout, so timeout-triggered termination or dedup is
**ruled out.** The pipeline is fast and healthy when it runs.

---

## § 04 — "Skipped" runs in the Actions tab

Queried the Actions API for all runs of every status across all
workflows:

- Total `fetch-and-commit` runs recorded: **69**
- Breakdown by conclusion: **69 × success**, 0 × anything else
- Non-success runs across the entire repo: **0**

**There are no skipped runs to find.** GitHub does not record dropped
schedule triggers as "skipped" entries — they are never instantiated as
runs at all. This is why the `runs` table (which only sees runs that
actually execute fetch.py) and the Actions UI agree: 68 cron-kind DB
rows ≈ 67 schedule-event runs + the difference from manual dispatches.
The missing ~1,640 invocations left no trace anywhere. The drop is
invisible by design.

Event breakdown of the 69 runs: **67 schedule + 2 workflow_dispatch**
(the 2 dispatches are the manual triggers from 2026-05-17 and -18).

---

## § 05 — Path filters / branch restrictions

```yaml
on:
  schedule:
    - cron: '*/5 * * * *'
  workflow_dispatch:
```

The `schedule` trigger has **no `branches`, `branches-ignore`, `paths`,
or `paths-ignore` filters** (those aren't even valid on `schedule`, but
worth confirming none were mis-added elsewhere). Scheduled workflows run
against the default branch (`main`), and 67 schedule events did fire, so
the schedule is correctly registered on the default branch. **Ruled
out.**

---

## § 06 — Minute-of-hour distribution (the clinching evidence)

If the `*/5` schedule were firing on its grid and merely dropping some
ticks, surviving runs would land at minutes that are **multiples of 5**
(`:00, :05, :10, :15, …`). They do not. Distribution of the 69 runs'
creation minute:

```
:05 ██ :06 █ :07 ██ :08 █ :09 █ :11 █ :13 █ :15 █ :17 ██ :18 █
:19 ██ :20 ███ :21 █ :22 █ :24 ██ :25 █ :26 ██ :27 ██ :28 █ :29 ███
:30 ██ :33 ██ :34 ██ :35 ███ :38 █████ :40 █ :43 █ :44 ██ :45 █████
:47 ████ :48 ██ :50 █ :52 █ :54 █ :55 ██ :56 █ :57 █ :58 █ :59 █
```

Runs land at essentially **every minute of the hour, roughly uniformly**
— `:06, :07, :08, :09, :11, :13, :17, :19, :21, :22…`. Almost none are
on the `*/5` grid by intent; the few that are (`:05, :15, :20, :30, :35,
:45, :55`) are coincidental given the spread.

This is the signature of GitHub **delaying** the schedule event by an
arbitrary, load-dependent amount and **collapsing** most ticks entirely.
A run "scheduled" for `:05` actually materializes at `:07` or `:19` or
not at all. The uniform minute spread proves the timing is set by
GitHub's queue drain, not by our cron grid.

---

## § 07 — What's specific to this setup

Published 70–85% free-tier figures and our 3.97% are not measuring the
same thing. The factors that put this setup in the worse regime, in
order of confidence:

1. **`*/5` is the most-deprioritized interval (high confidence).**
   GitHub's scheduler explicitly deprioritizes high-frequency schedules
   and drops queued ones under load. The 70–85% figures circulate for
   hourly / daily schedules. A 5-minute schedule asks GitHub for 288
   runs/day; it is the single highest-risk scheduling choice in the
   product. This alone plausibly accounts for most of the gap.

2. **Public repo, bot-only commits (low confidence, unverifiable).**
   GitHub deprioritizes scheduled workflows on repos without recent
   *human* activity (the well-documented rule is full disable after 60
   days of inactivity; partial throttling before that is plausible but
   not documented). This repo's only recent pushes are the workflow's
   own bot commits (`actions@github.com`), which may not count as the
   "activity" that keeps schedules prioritized. Cannot be confirmed from
   outside GitHub.

3. **Overnight-UTC clustering (observed, mechanism unclear).** The W21
   reliability report found all five longest gaps begin 01:26–06:39 UTC.
   That is *off* GitHub's documented US-daytime peak-load window
   (14:00–23:00 UTC), so the clustering is not simply "high load."
   Mechanism unexplained; flagged as an anomaly, not attributed.

---

## § 08 — What was ruled out

| Candidate | Status |
| --- | --- |
| Wrong cron expression | Ruled out — `*/5 * * * *` confirmed |
| Concurrency-induced skips | Ruled out — runs never overlap |
| Timeout-triggered termination | Ruled out — 27–37s vs 240s budget |
| "Skipped" runs hidden in UI | N/A — drops are never instantiated, nothing to find |
| Path / branch filters | Ruled out — none present |
| Billing / quota exhaustion | Ruled out — public repo, unlimited minutes |
| Pipeline failures | Ruled out — 100% success on runs that fire |

---

## § 09 — Diagnostic conclusion

The 3.97% rate is **not caused by anything in the repository's
configuration.** It is GitHub's scheduler delaying and dropping the
`*/5` schedule at the infrastructure level, evidenced by (a) the uniform
minute-of-hour spread, (b) the absence of any logged skip/cancel, and
(c) healthy fast runs whenever GitHub does fire. The most actionable
specific factor is the `*/5` frequency itself — the highest-risk
scheduling interval GitHub offers.

No workflow change made in this pass (operator instruction). The
remediation question — less-aggressive GH schedule vs. external
scheduler — is the Week 2 scheduler-migration decision already logged in
`pending.md` and decision-log 2026-05-18.

---

paper-api.alpaca.markets/v2/orders  ·  generated by manual investigation against Actions API + runs table

[github.com/pwysocan-droid/algotrading-paper](https://github.com/pwysocan-droid/algotrading-paper)
