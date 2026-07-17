# Operator runbook — the parts only a human triggers

Everything recurring runs on the VPS cron with zero attention: the
5-minute fetch/trade/exit cycle, nightly skeptic (03:32 UTC), Friday
investigator review (03:34 UTC Fri), learnings ledger, rounds/digest
aggregation, Pages deploys. This file is the short list of what does
NOT run by itself.

## 1. Turn the foundry crank (~1 hour, weekly-ish)

Open Claude Code in this folder and say:

> Run the foundry cycle: implement the latest round, run the staged
> gauntlet, write the epitaphs, and generate the next round.

That's the whole trigger. Claude implements the specs from the newest
`reviews/foundry/round-*.md`, runs
`python scripts/run_gauntlet.py --staged --days 930 --db research_bars.db --names <...>`,
writes gradient-rich epitaphs into `reviews/foundry/dead-ideas.json`,
and fires the next round's synthesis. If a session is lost mid-cycle,
just say it again — every step is idempotent or checkpointed in git.

## 2. Read the results (no session needed)

- Live: https://pwysocan-droid.github.io/algotrading-paper/surface/
- Learnings dashboard: .../surface/learnings.html
- Rounds by date: .../surface/rounds.html
- Digest: reports/digest-YYYY-MM-DD.md — emailed daily ~06:30 Pacific
  to pwysocan@gmail.com by the `digest-mailer` cloud routine
  (trig_01NjtGaNPuFbLWzikmt5iuQw). If the digest is >1 day stale it
  emails a STALE warning instead — that email is the heartbeat.

Cloud routines (manage at https://claude.ai/code/routines):
- `foundry-implementer` (trig_01CB7gU6mXGFXSRj4kvDd74N, 08:00+20:00
  UTC): the keyless half of the closed seam — implements new round
  specs and writes epitaphs, pushing to the repo. Pairs with the VPS
  autopilot (gauntlets + next-round generation).
- `digest-mailer` (trig_01NjtGaNPuFbLWzikmt5iuQw, 13:30 UTC): above.

## 3. Decisions only you can make

- **Promotion**: when `python compare.py --a <arm>` shows a candidate
  beating null at p<0.05 over 100+ closed trades, the promotion is
  your call — read the future-self letter on the Phase 2 entry gates
  first (decision-log.md).
- **Phase 1b review, 2026-08-14 hard stop**: extend or archive,
  against the § 5 terms in phase1-review.md.
- **Amending the future-self letters**: they're drafts in your voice;
  edit freely.

## 4. If something looks wrong

- Site stale >90 min → check `ssh trader@62.238.45.142`, then
  vps/README.md's debug section.
- A missed Friday review is an archive trigger — the cron has a
  static-template fallback, so a miss means the VPS itself is down.
