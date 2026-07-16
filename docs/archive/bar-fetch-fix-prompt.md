# Bar-fetch fix — for Claude Code

Ship this as its own commit. Do not bundle with other changes.

---

## The prompt

```
One change, one commit, ship now.

In .github/workflows/fetch-and-commit.yml, change the fetch.py
invocation from `--minutes=15` to `--minutes=90`.

Context: GH cron's actual cadence is ~60 min (not the documented
5 min), and at times runs ~210 min between executions. The 15-min
lookback was designed for a 5-min cron with 3× overlap. At the
real cadence, ~91% of expected bars are being silently dropped —
the live surface's `accumulating · bar coverage` row currently
reads 9%. The walk-forward tuner, A/B comparator, and replay tool
all read from the bars table; a Swiss-cheese bars dataset would
corrupt every downstream layer of the project.

Verification after the change:
1. Run the workflow manually (gh workflow run) so we don't wait
   for the next scheduled execution.
2. Confirm Alpaca returns ~18 bars per symbol per call instead
   of ~3. No API cost concern at this rate.
3. Confirm the workflow exits clean.
4. Over the next 24 hours, the `accumulating · bar coverage`
   row on the surface should climb from 9% toward ~95%. If it
   doesn't, something else is wrong upstream (Alpaca rate limit
   on the larger lookback, or the bars table not accepting the
   higher write volume) — not the fix's fault, but worth flagging.

Commit message: "Widen bar-fetch lookback to 90 min to match
actual cron cadence."

Do NOT in this commit:
- Touch any other file
- Adjust the cron schedule itself
- Add the cadence-recalibration decision-log entry (separate commit,
  separate session)
- Add the cron-variance accumulating row (separate work, deferred)
- Move pending items around
- Bundle with the Week 2 scheduler migration

This is one line of YAML and a commit message. Ship it.
```

---

## After Claude Code finishes

Wait one cron run. Check the live surface at
`https://pwysocan-droid.github.io/algotrading-paper/surface/` —
`accumulating · bar coverage` should start climbing within the
next 1-2 cron cycles. If it does, the fix worked and you can
move to the decision-log entry next.

If `bar coverage` stays at 9% or drops further, the fix didn't
take and the upstream cause needs investigation — most likely
Alpaca rate limiting or GH cron lag worsening independently.
