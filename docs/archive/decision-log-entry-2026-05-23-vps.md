# Decision Log Entry — 2026-05-23

Paste at the top of `decision-log.md`, above the 2026-05-17 entry.

---

## 2026-05-23 — Migrating cron from GitHub Actions to Hetzner VPS

**Findings from six days of cron data (2026-05-17 to 2026-05-23):**

- 69 invocations of 1,712 expected — 4.0% invocation rate
- 69 of 69 successful — 100% code success rate
- Config audit clean: cron expression correct, no concurrency conflicts,
  no path filters, no timeout dedup
- Diagnostic: runs scatter across minutes-of-hour rather than clustering
  at multiples of 5, proving GitHub is delaying then dropping schedule
  triggers — infrastructure-side, not config-side
- The 95% uptime gate as written cannot be cleared on GitHub Actions
  free-tier `*/5` cron. Documented free-tier averages of 70-85% are for
  hourly schedules; 5-min schedules on public repos with bot-only
  commits operate at 3-5%

**Decision: migrate the cron to a Hetzner CX22 VPS** ($5.83/month).
System cron runs the existing `fetch.py` unchanged. Pushes to GitHub
on completion. The GitHub Actions cron workflow is disabled (set to
manual-trigger only) but the YAML preserved in the repo for reference.

**Considered and rejected:**

- *Self-hosted GitHub Actions runner on VPS.* Same cost, slightly more
  elegant integration, more setup complexity. Not worth the marginal
  benefit over plain system cron.
- *AWS EventBridge + Lambda, or Cloudflare Workers Cron.* Free tier
  exists, but ~2-3 hours of config tax. Not justified at this scale.
- *Lower the significance bar from p<0.05 to p<0.10 to halve trade
  count.* Trading discipline for time is the failure mode
  philosophy.md warns against.
- *Slow the cron to */15 or */30.* Undercuts the data-accumulation
  rate that Week 4's walk-forward tuner depends on.

**What this gains:**

- 95% uptime gate becomes achievable as written — no amendment to the
  Phase 2 entry criteria required
- ~2,000+ successful runs per 4 weeks instead of ~280
- Real statistical power for Week 4's A/B comparator
- "Is cron reliable" stops being a recurring operational concern

**What this costs:**

- ~$12 over Phase 1 (8 weeks × $5.83/mo, prorated)
- One new failure mode: the VPS itself (mitigated by Hetzner's
  documented 99.9% uptime)
- ~30 minutes of operator setup time

**Amendment to 2026-05-17 hypothesis:**

- *Original:* 90%+ success rate by end of first calendar week (of
  GitHub-Actions-invoked runs)
- *Amended:* Two metrics tracked separately. Invocation rate (now
  VPS-controlled, target ≥99%) and code success rate (project-
  controlled, target ≥95%). Combined target is 95%+ uptime of
  *expected* runs over any 4-week window — which is exactly what the
  Phase 2 architectural gate measures. The hypothesis amendment
  removes the platform-induced ceiling that was making the original
  hypothesis unfalsifiable.

**Letter to future self at the moment of doubt:**

Future me, you're going to read this and wonder whether the $12 was
worth it. It was. The alternative was either lowering the gate
(which would have rendered Phase 2 entry meaningless) or living with
the cloud of "is the cron working" hanging over every operational
decision through Week 8. Six days of data is enough to commit; the
platform reality is documented; the move is correct. The discipline
of *boring infrastructure for the substrate of a reliability
experiment* is on-brand for the project. Don't second-guess.

You're also going to be tempted, in Week 5 or 6 when the VPS has a
hiccup, to think "we should have stayed on GitHub Actions." That
thought is wrong. The hiccup is bounded (worst case: lose a few
hours of bars, the runs table logs status='failed' for the missed
window, the data resumes). The GitHub Actions alternative was 95%
of runs *missing entirely*, with no audit trail of what wasn't run.
A VPS hiccup is visible; a missing GitHub invocation is invisible.
Visible failure is the gift.
