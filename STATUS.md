# STATUS — read this first

One-file orientation for anyone (human or Claude) joining mid-flight.
Snapshot date: **2026-07-31**. If that looks stale, trust the live
artifacts it points to over the prose here.

## What this is (and the pivot that defines the current era)

An LLM-driven trading-research machine. It began as an autonomous crypto
**idea-foundry** — generate strategies, falsify them against 2.5 years of
data, epitaph the failures, compound the lessons. That program reached an
honest conclusion: **~43 falsifications across two markets and every horizon
found no mispricing edge that survives costs.** Hunting mispricing at retail
scale in liquid markets does not pay. The historical statistical budget is
spent (forward-only from here).

The machine then **pivoted from *predicting* to *underwriting*** — see
`CONSTITUTION.md` (v2.0, "The Book"). The two positive findings were
risk-premium-*shaped* (compensation for bearing risk, not reward for
predicting), so the machine now earns — if it earns at all — by selling
bounded, defined-risk insurance and refusing to write it when it isn't
richly paid. **The generators are halted** (budget spent); what runs now is
the Book candidate plus forward-only monitoring.

## The topline result so far

**There is no easy variance premium to harvest in liquid ETF options — the
market prices it fairly at every moneyness, so the machine's honest job is to
*wait*, and whether even the rare rich days pay is still unproven.** The
2-year real-option backfill showed premium is fairly priced only ~2–9% of
days at the conservative strike, and moving the strike closer just underwrites
at worse odds. No edge demonstrated; none ruled out. The verdict rests on
forward realized P&L that has not spoken yet (first shadow resolutions
~2026-09-04).

## The loop (all VPS-resident — nothing depends on any laptop)

| UTC | what | cron |
| --- | --- | --- |
| every 5 min | crypto fetch → signals → trade → manage exits → push (live A/B) | `cron-fetch.sh` |
| every 5 min | context tape | `cron-context.sh` |
| 03:32 daily | nightly skeptic + parity check + **digest email** (the heartbeat) | `cron-skeptic.sh` |
| 15:30 Mon–Fri | **VRP machine**: manage spreads → resolve shadows → scan/write (paper) | `cron-vrp.sh` |
| 03:34 Friday | adversarial bear-case review | `cron-friday.sh` |
| 06:00 Sunday | **git gc** (packs the DB-heavy history; prevents disk bloat) | `cron-gc.sh` |

**Removed** (generators halted 2026-07-24): `cron-foundry.sh`,
`cron-implementer.sh`, `cron-outside.sh`. A `GENERATORS_HALTED` sentinel
suppresses the false foundry-stall alarm.

Surfaces: dashboard https://pwysocan-droid.github.io/algotrading-paper/surface/
· daily digest email (a STALE warning or silence = the pipeline is broken).

## Current state — The Book (Candidate #1: variance-risk-premium harvester)

- **What it does** (`scripts/vrp_harvester.py`): sells defined-risk
  put-credit spreads on **SPY/QQQ/IWM/DIA/GLD** when a ~1-realized-SD-OTM
  strike pays a rich credit (gate: credit ≥ 20% of width), unless an LLM
  stand-aside finds a genuinely underpriced tail. Max loss = width − credit
  (contractual). Paper account (Alpaca level-3, $100k); **live is gated**.
- **Executed record: n = 0** — premium is genuinely thin (real quotes run
  12–13% of width vs the 20% gate). Correct behavior, not a bug: the machine
  waits for the rare rich day.
- **Shadow arm** (`book/shadow.jsonl`, Art 3.2): logs every ETF's proposed
  spread daily at **two strikes** (1-SD live + 0.5-SD shadow-only) and
  resolves hypothetical P&L at expiry — evaluates the decision rule on ~250
  days/yr at zero risk. Readout: `scripts/vrp_shadow_report.py`. First
  resolutions ~2026-09-04.
- **Backfill calibration** (`reports/vrp-richness-backfill-*.json`, real
  Alpaca closes, Feb 2024–Jul 2026): the topline above. Dropped **TLT**
  (never fairly paid — VRP may not exist in bonds; open thread) and **EEM**
  (illiquid) from the universe.
- **Live gate, pre-registered** (`book/pre-reg-live-gate.md`): n ≥ 30 closed,
  net-positive after costs, beats a dumb always-write arm AND the drift null,
  zero bound breaches, loss-rate under the premium-implied breakeven.
  12-month deadline. **Operator owns funding + options approval** (~$10k
  floor, $50–100k to size properly); this record owns the performance bar.
- **Crypto live A/B** still accumulates in the background (the only forward
  evidence from the old program): `null_baseline` + 2 arms since 2026-07-16.

## Learnings (the compounding asset — how the machine avoids fooling itself)

Transferable method lessons live in `docs/field-notes.md`. The load-bearing ones:

- **Measure the instrument before trusting its verdicts**; measure the ceiling
  of the input space; every causal claim needs a control arm; match the
  yardstick to the thesis; compare to the drift null, not zero; correct for
  multiple testing; **n < 30 makes no claim**; a fixed dataset's statistical
  budget is spent by adaptive reuse → **stop generating, never stop verifying.**
- **Regime is the variable** — reversion held at every measured horizon; an
  effect real for years can invert.
- **New this session (VRP):**
  - *Don't validate against a self-referential bar.* Judging "fairly paid" via
    a threshold derived from the same vol model that places the strike is
    circular; use the market's own priced breakeven (credit/width). Only
    forward realized P&L tests profitability — a calibration can at best say
    "not obviously mispriced." (`feedback_self_referential_validation` memory.)
  - *A busy-looking parameter can be a mirage.* The closer 0.5-SD strike clears
    the flat 20% gate ~10× more, but delta-adjusted it's fairly paid *less*
    often — a fixed gate over varying risk. Caught before deployment.
  - *Where a premium lives is itself a finding* — TLT/bonds show ~no premium;
    parked as a search lead, not just cut.

## Hard rules & failure modes (learned the expensive way)

- **Single-writer**: only the VPS writes `trader.db`. Never push a locally
  modified copy.
- **Locked architecture** (decision-log): capital model, Phase-2 gates/exits,
  schema, no-ML, no-oracle. Going live is always a human decision.
- **DB-in-git bloats the repo**: the fetch loop commits `trader.db`/`context.db`
  every run (Option A backup). Auto-gc fell behind once and loose objects hit
  **28 GB, filling the VPS disk** (2026-07-31). Fixed: memory-capped pack
  config (`pack.threads=1/window=5/windowMemory=96m` — the 3.7 GB box OOMs a
  default gc) + weekly `cron-gc.sh`. If disk climbs again, run
  `git -c pack.threads=1 -c pack.windowMemory=96m gc`.
- **Gmail connector is draft-only**; cloud CCR routines died silently — use
  VPS-resident crons.
- **LLM fire-rate/frequency guesses miss by 10–2000×** — premise-check cheap
  distribution claims against real data first.
- **Alarms judge only the most recent run** (forgive recovered incidents) or
  they train the operator to ignore them.

## File map

| file | role |
| --- | --- |
| `STATUS.md` | this brief — bump the snapshot date when you revise it |
| `CONSTITUTION.md` | The Book — the founding charter (v2.0) |
| `book/pre-reg-variance-premium.md` | Candidate #1 spec |
| `book/pre-reg-live-gate.md` | the 5-point paper→live performance gate |
| `book/positions.jsonl` · `book/shadow.jsonl` | live ledger · zero-risk shadow record |
| `decision-log.md` | dated decisions, newest last — the why behind everything |
| `docs/field-notes.md` | transferable method/epistemics lessons |
| `scripts/vrp_harvester.py` | the VRP machine (manage + shadow + scan/write) |
| `scripts/vrp_shadow_report.py` · `vrp_richness_backfill.py` | shadow readout · calibration |
| `reviews/foundry/dead-ideas.json` | 43 crypto epitaphs + failure lessons |
| `config.py` · `signals.py` · `replay.py` · `execute.py` | crypto A/B machinery |

## If you're a fresh Claude session

Read this file, then `CONSTITUTION.md`, then the tail of `decision-log.md`
(last ~5 entries), then `book/pre-reg-live-gate.md`. That's ~10 minutes to
full context. Before changing anything: keep the test suite green, respect the
hard rules above (most exist because something already went wrong once), and
remember the current posture is **wait-and-verify, not generate.**
