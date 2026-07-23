# STATUS — read this first

One-file orientation for anyone (human or Claude) joining mid-flight.
Snapshot date: **2026-07-23**. If that looks stale, trust the live
artifacts it points to over the prose here.

## What this is

An autonomous algorithmic-trading research machine. It paper-trades
crypto ($100k Alpaca paper account, $1k real exposure ceiling) while an
LLM-driven "idea foundry" generates novel strategies, implements them,
falsifies them against 2.5 years of data, writes mechanism-level
post-mortems, and feeds the lessons back into the next round — with no
human in the loop. **No strategy has survived yet (43 tested, 0 alive),
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
- **Foundry**: rounds 001–007 complete, 43 ideas epitaphed in
  `reviews/foundry/dead-ideas.json` (verdicts + gradients + 27
  promoted failure lessons — the project's compounding asset). Round
  008 generates automatically next.
- **The one lead is gone, and the reopened gate keeps failing the same
  way**: self-referential gates (system observing its own outcomes)
  were best-of-round three rounds running, and r003's
  `slot_scarcity_conviction_gate` passed its own kill criterion
  (+1.75%/trade — but at n=7, verdict `inconclusive_starved`). r005
  closed the self-referential family (gated win rate indistinguishable
  from its own round's ungated engine, n=407/447). r006 reopened it on
  a genuinely new, cross-sectional (not own-outcome) mechanism
  (`constraint_rejection_pressure_release_engine`) and it died badly
  (n=556/559, edge/slot -$1.31/-$1.03, worst drawdown of that round)
  — with its own promised control comparison (gated vs. this engine's
  ungated breakouts) never actually run. r007 reopened the family
  again on the same reopening argument
  (`cross_sectional_dispersion_gate_trend_engine`, this round's
  canary) with a kill criterion explicitly designed to finally run
  that control — and the control was, again, never run; the idea died
  on absolute performance instead (n=387/392, edge/slot -$0.98/-$0.77).
  Two gate specs in two rounds have now promised the same control
  comparison and neither delivered it — promoted to a new failure
  lesson (any spec whose kill criterion needs a matched control must
  register that control as its own variant, or the comparison won't
  happen). No current lead; no current survivor.
- **Three consecutive continuation canaries have now fired negative**:
  r005's `multiday_magnitude_persistence_directional_hold`, r006's
  `multiweek_directional_regime_persistence_hold` (win 30.0%/29.2%,
  edge/slot -$6.49/-$6.75, worst of that round), and r007's
  `cross_sectional_dispersion_gate_trend_engine` (win 40.1%/39.8%,
  edge/slot -$0.98/-$0.77) — all three cleared clean premortem review
  and comfortable sample sizes, and all three died on the same
  underlying mechanism (REGIME IS THE VARIABLE / REVERSION AT EVERY
  MEASURED HORIZON). The reversion regime has now been checked at
  2-week, monthly, and synchronized-basket horizons and held every
  time; a clean premortem verdict continues to mean "no flaw found on
  paper," not "likely to survive" — only the gauntlet settles that.
  r007 also confirmed, twice in one round, that a premise check fixing
  a spec's raw base-rate math (100x population increases for both
  `liquidity_window_shock_fade_maker` and
  `epidemic_susceptible_depletion_terminal_burst`) does not guarantee
  the constrained gauntlet clears n>=100 — multi-day-hold specs occupy
  a portfolio slot for the length of the hold, and that occupancy, not
  raw signal frequency, is what starves the realized sample (new
  lesson, promoted this round).
- **Meta-result**: 43 falsifications across every lens suggest 5-min
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
| `reviews/foundry/dead-ideas.json` | 43 epitaphs + 27 lessons (the asset) |
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
