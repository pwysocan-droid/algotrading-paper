# STATUS — read this first

One-file orientation for anyone (human or Claude) joining mid-flight.
Snapshot date: **2026-07-20**. If that looks stale, trust the live
artifacts it points to over the prose here.

## What this is

An autonomous algorithmic-trading research machine. It paper-trades
crypto ($100k Alpaca paper account, $1k real exposure ceiling) while an
LLM-driven "idea foundry" generates novel strategies, implements them,
falsifies them against 2.5 years of data, writes mechanism-level
post-mortems, and feeds the lessons back into the next round — with no
human in the loop. **No strategy has survived yet (33 tested, 0 alive),
and that record is the product**: fast, honest falsification with
compounding lessons, while a live A/B accumulates the only evidence
that ultimately counts.

## The loop (all VPS-resident — nothing depends on any laptop)

| UTC | what | where |
| --- | --- | --- |
| every 5 min | fetch bars → signals → trade → manage exits → push | vps cron `cron-fetch.sh` |
| 03:32 | nightly skeptic + parity check + digest render + **digest email** | `cron-skeptic.sh` |
| 04:02 / 16:02 | foundry autopilot: gauntlet implemented rounds; synthesize next round when epitaphs land | `cron-foundry.sh` → `scripts/foundry_autopilot.py` |
| 09:02 / 21:02 | **implementer**: headless Claude Code on the VPS implements new round specs / writes epitaphs | `cron-implementer.sh` |
| Friday | adversarial review (bear-case investigator with SQL/file tools) | `cron-friday.sh` |

Surfaces: dashboard https://pwysocan-droid.github.io/algotrading-paper/surface/
(answer-first topline: now / pipeline / health + all-time tiles) ·
daily digest email to the operator (a STALE warning or silence = the
pipeline itself is broken — the email is the heartbeat).

## Current research state

- **Live A/B** (the only evidence that counts): 3 arms since 2026-07-16
  — `null_baseline` placebo + `weekend_illiquidity_momentum` +
  `volume_thrust_regime_shift`. Promotion gate: an arm must beat null
  at p<0.05 over 100+ closed trades (`compare.py`). Clock position:
  ~10 closed. This takes weeks and cannot be compressed.
- **Foundry**: rounds 001–005 complete, 33 ideas epitaphed in
  `reviews/foundry/dead-ideas.json` (verdicts + gradients + 24
  promoted failure lessons — the project's compounding asset). Round
  006 generates automatically next.
- **The one lead is gone**: self-referential gates (system observing
  its own outcomes) were best-of-round three rounds running, and
  r003's `slot_scarcity_conviction_gate` passed its own kill criterion
  (+1.75%/trade — but at n=7, verdict `inconclusive_starved`). r005
  ran the family's largest-sample test yet, pairing a looser
  single-scalar gate with a strong multi-day engine
  (`placebo_streak_gated_weekly_trend_engine`, n=407/447): the gated
  win rate was statistically indistinguishable from the SAME round's
  ungated version of the identical engine, satisfying the family's own
  pre-registered retirement clause. The gate family is now CLOSED, not
  just weakened — five rounds, five specs, one small-sample outlier
  that regressed to the pooled mean exactly as the 2026-07-19
  meta-analysis predicted. No current lead; no current survivor.
- **r005 also reconfirmed the regime problem**: two multi-day
  trend-continuation ideas (`trailing_return_rank_persistence_hold`,
  `multiday_magnitude_persistence_directional_hold`) died on the same
  mechanism — directional momentum in this 2024-25 archive runs
  negative (per the `REGIME IS THE VARIABLE` lesson), so any spec that
  bets on trend continuation without addressing the regime flip
  inherits that sign error. A third idea
  (`weekly_pullback_limit_into_uptrend`) starved to n=3, ~186x under
  its own base-rate estimate — the worst fire-rate miss on record,
  newly promoted into a lesson about rare-touch conjunctions.
- **Meta-result**: 33 falsifications across every lens suggest 5-min
  OHLCV-alone may hold no retail-scale edge after costs. The untried
  structural lever is **Layer-2 context data** (funding rates,
  fear/greed, on-chain) — queued in `build_queue.md`.

## Validated machinery (the levers)

- Backtest realism: fees 0.25%/leg + slippage 0.05%/leg + full
  portfolio constraints (5 slots, $1k ceiling, 1h/symbol cooldown).
  Fitness = **edge per constraint slot** (net P&L / placed trade).
- Per-variant exits (`tp`/`sl`/`time_exit_hours` in params) — honored
  by replay AND live. Horizon is a lever.
- Maker/limit fill model (`fill_model='maker'` in replay; gauntlet
  `--fill-model` axis): validated 12/12 matched pairs, ~+$0.14/slot.
  Cost is a design input. Live execution still sends market orders.
- Train/holdout discipline: the 2026 window is NEVER used for
  selection; the holdout answers one question per candidate, ever,
  and has not been burned.
- Sim-to-live parity: nightly deterministic shadow replay
  (`parity_check.py`) + weekly calibration report + an end-to-end test
  pinning the live/replay `system_state` key contract.

## Failure modes & hard rules (learned the expensive way)

- **Single-writer**: only the VPS writes `trader.db`. Never push a
  locally modified copy.
- Locked architecture (decision-log): capital model, Phase-2
  gates/exits, schema, no-ML, no-oracle. Foundry variants register
  `enabled=False`; going live is a human decision, always.
- The claude.ai Gmail connector is draft-only; cloud CCR routines died
  silently 5/5 — both disabled, superseded by VPS-resident equivalents.
- Fire-rate predictions from LLM synthesis miss by 10–2000x: premise-
  check cheap distribution claims against real bars BEFORE gauntling
  (`CONJUNCTIONS MULTIPLY TO ZERO` lesson).
- n<30 placed = no claim, regardless of sign. Positive small samples
  are quarantined, not celebrated.
- Alarms must forgive recovered incidents (`pipeline_health` judges
  only the most recent run) or they train the operator to ignore them.

## File map

| file | role |
| --- | --- |
| `STATUS.md` | this brief — update the snapshot date when you revise it |
| `PROJECT.md` | founding intent, capital model, honest expectations |
| `OPERATOR.md` | every trigger/schedule + what only the human decides |
| `decision-log.md` | dated decisions, newest first — the why behind everything |
| `reviews/foundry/dead-ideas.json` | 33 epitaphs + 24 lessons (the asset) |
| `build_queue.md` / `pending.md` | agreed-but-deferred work / awaiting human |
| `config.py` | variants registry (3 enabled), costs, limits |
| `signals.py` / `replay.py` / `execute.py` | strategies · backtest engine · live execution |
| `scripts/` | foundry, gauntlet, autopilot, digest, surface generators |
| `reports/` | gauntlets, digests, calibration, sweeps (timestamped) |

## If you're a fresh Claude session

Read this file, then `OPERATOR.md`, then the tail of `decision-log.md`
(top 3 entries), then `reviews/foundry/dead-ideas.json`'s
`failure_lessons`. That's ~10 minutes to full context. Before changing
anything: the test suite (360+) must stay green, and check the hard
rules above — most of them exist because something already went wrong
once.
