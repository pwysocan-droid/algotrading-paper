# algotrading-paper / week-1 status

Build complete  ·  10 modules wired  ·  72 tests passing, 1 skipped

2026-05-02T23:53:00Z

[↗ latest replay](reports/2026-05-02-replay.md)  ·  [↗ index](INDEX.md)

| Modules built | Tests | Verification gate | Days to phase 1 review |
| :--- | :--- | :--- | :--- |
| **10** | **72 / 73** | **7 / 8** | **57** |
| db, fetch, render, signals, execute, replay, render_index, claude_client, friday-bear-case template, future-self-letter convention | 1 skipped (live API) | 1 pending operator action | calendar |

## § 01 — Modules built · in build order

| Module | Tests | Notes |
| --- | --- | --- |
| `db.py` + `db/migrations/` | 8 | 8 paired up/down SQL migrations covering bars / context_data / signals / trades / decisions / runs / recommendations / llm_calls. `schema_migrations` table tracks applied versions; `migrate()` and `rollback(steps=N)` are both idempotent. |
| `fetch.py` (+ `config.py`) | 6 | Alpaca crypto-bars source for the five `WATCHED_SYMBOLS`, idempotent UPSERT on (symbol, timestamp). Every run logs to `runs` — success or failure. `FakeBarSource` fixture lets unit tests run without hitting the live API. |
| `render.py` | 25 | v1 (snapshot) renderer + `render_index` + utilities for currency / pct / ratio / count / ISO timestamp / human time / variant name / trade ID / 8-char unicode sparkline. v2 (temporal) renderer deferred to Week 4. |
| `signals.py` | 6 | Skeleton + driver. `STRATEGY_REGISTRY` is empty for Week 1; runs cleanly against an empty registry and emits zero signals. `Signal` / `BarRow` / `StrategyFn` shapes stable for Week 2. |
| `execute.py` | 8 | Position-limit enforcement: \$200/trade · \$1,000 total · 5 concurrent · 1h per-symbol cooldown — all in code, all tested. Every signal produces a `decisions` row (placed or rejected with reason). |
| `replay.py` | 8 | The deliverable. Look-ahead-bias guard: signal on bar N's close → entry at bar N+1's OPEN, never bar N's close. Signal on the last bar in the window drops (no future open available). |
| `render_index.py` | 11 | Surface discovery, project-level four-stat (uptime / trades-this-week / Phase 2 gates 0–3 / days to phase 1 review), idempotent given a stable now. |
| `claude_client.py` | 1 (skipped) | `complete()` free-text + `complete_structured()` Pydantic-via-tool-use, both auto-log to `llm_calls`. Default model `claude-sonnet-4-6` verified against [Anthropic docs](https://platform.claude.com/docs/en/docs/about-claude/models/overview) at build time. |
| `reviews/templates/friday-bear-case.md` | — | Cluster-4 4G prompt template. Four mandatory sections, no hedging, drift check vs prior week. First filled review goes in `reviews/YYYY-WW-friday.md`. |
| `decision-log.md` future-self-letter convention | — | Cluster-4 4F. Three-paragraph format; one worked example for the Phase 2 drawdown exit (\$700 floor). Retroactive letter-writing for existing 2026-04-26 entries deferred to Week 2 per the prompt. |

## § 02 — Tests by suite

| Suite | Passing | Skipped | Non-negotiable |
| --- | --- | --- | --- |
| `test_db.py` | 8 | 0 | migrations up/down round-trip ✓ |
| `test_fetch.py` | 6 | 0 | — |
| `test_render.py` | 25 | 0 | empty-state fully-formed ✓ |
| `test_signals.py` | 6 | 0 | — |
| `test_execute.py` | 8 | 0 | — |
| `test_replay.py` | 8 | 0 | look-ahead-bias guard ✓ |
| `test_render_index.py` | 11 | 0 | idempotency ✓ |
| `test_claude_client.py` | 0 | 1 | live-API smoke (gated on `ANTHROPIC_API_KEY`) |
| **total** | **72** | **1** | all four non-negotiables green |

## § 03 — Verification gate · prompt's eight items

| Item | Status | Notes |
| --- | --- | --- |
| All eight tables exist with correct schemas | ✓ | `python db.py migrate && python db.py status` lists all 8 plus `schema_migrations` |
| `python -m pytest tests/` all green | ✓ | 72 passing, 1 skipped (gated, intentional) |
| `replay.py --variant=null --period=30d` produces v1-pattern empty-state report | ✓ | `reports/2026-05-02-replay.md` — em-dashes for not-yet-present, explicit zeros for real-zero, fully-formed sections, no "no data yet" |
| `python render_index.py` produces INDEX.md | ✓ | `INDEX.md` at repo root, project-level four-stat populated, surfaces table heavily em-dashed (correct for Week 1) |
| `claude_client.py` integration test passes | **deferred** | Test exists and is correct; SKIPPED until operator creates real `.env` with `ANTHROPIC_API_KEY` per setup.md step 6. Run `pytest tests/test_claude_client.py -v` after .env is in place. |
| `reviews/templates/friday-bear-case.md` exists and is readable | ✓ | 182 lines, four mandatory sections, drift-check section comparing vs prior week |
| `decision-log.md` future-self-letter convention with one worked example | ✓ | Convention section above 2026-04-26 entries; example is the Phase 2 drawdown exit (\$700 floor) |
| `week-1-status.md` exists at repo root as a v1-pattern report | ✓ | this file |

## § 04 — Build-time decisions worth a `decision-log.md` entry

These were build-time choices that aren't spec'd in PROJECT.md. Each is candidate for a `decision-log.md` entry the operator may want to commit.

| Decision | Rationale | Reversible? |
| --- | --- | --- |
| Default Claude model: `claude-sonnet-4-6` | Verified at build time against Anthropic docs (latest production Sonnet). Read from `CLAUDE_MODEL` env var so model upgrades are config, not code. | yes — flip env var |
| `simulate_exit` is conservative when SL and TP both cross in the same bar | When both are hit in the same bar without intra-bar tick data, assume stop-loss filled first — worst-case for the trade. Prevents backtest optimism on volatile bars. Affects backtest results materially when bar volatility is high. | yes — flag-driven later |
| Phase 1 review target date: **2026-06-28** | 57 days from 2026-05-02 ≈ 8 weeks plus a small buffer. Configurable via `--review-date` CLI. Picked so `Days to phase 1 review` is non-zero from Week 1; operator should override with the actual planned end date. | yes — CLI flag |
| Project layout: flat scripts at repo root | Matches PROJECT.md's "Pipeline" diagram (`fetch.py` → `signals.py` → ...). Not a `src/` layout. `requirements.txt` + `dev-requirements.txt` instead of `pyproject.toml` because this is research scripts, not a library. | yes but disruptive |
| Anthropic structured output via tool-use with `input_schema = Pydantic.model_json_schema()` and `tool_choice` pinned | The Anthropic SDK doesn't have a `response_format` param like OpenAI's; tool-use is the supported way to enforce a schema. `complete_structured` returns a parsed Pydantic instance. First real call is Week 5+ feature extraction; not exercised in Week 1. | yes — module-local |
| Look-ahead-bias guard semantics: signal on the *last* bar in the window is *dropped* (no future open available) | The alternative (back-fill the entry to the same bar's close) reintroduces look-ahead bias by construction. Test `test_signal_on_last_bar_drops_no_entry_available` enforces. | non-negotiable |
| Trade-ID rendering: zero-padded to 4 digits when integer (`#0142`) | Matches the report-format-spec example. String trade-IDs (e.g., Alpaca's UUIDs) render verbatim with `#` prefix. | yes |
| Foreign keys enforced via `PRAGMA foreign_keys = ON` per connection | SQLite's default is OFF; without this, FK violations fail silently. | yes |
| `runs.bars_added` includes UPSERT replacements as well as inserts (uses `executemany.rowcount` from SQLite) | Re-fetching a window with overlapping data records the bar count as the upsert count. The audit trail then reflects "bars touched," not "new bars only." Worth noting when interpreting `runs` rows for uptime calculation. | yes — counter rename |

## § 05 — Deferred to Week 2

Per the curriculum and the prompt's explicit "do NOT build" list:

| Item | Why deferred |
| --- | --- |
| Strategy registration (Bollinger / MA-crossover or Week-0-surfaced replacements) | Week 2 strategy-roster review — `STRATEGY_VARIANTS` empty for now |
| Live `fetch.py` against the real Alpaca paper API (full 30-day backfill) | Operator runs once `.env` exists; tested logic via fixtures works against either source |
| `compare.py` (A/B comparator) | Week 4 |
| `tune.py` (walk-forward tuner) | Week 4 |
| `render_v2_report` (temporal pattern) | Week 4 — first temporal report is the weekly A/B |
| Layer 2 (`context.py`) and any external data sources | Week 5+ |
| LLM-derived features for trading decisions | Week 7 in the original spec, dependent on Week 4's promotion-loop infrastructure first |
| GitHub Actions cron / 5-minute live schedule | Week 2 |
| Styled HTML report surface | Week 2 review per roadmap |
| Future-self letters for the existing 2026-04-26 hard-rule entries (entry gates, exit conditions, reframe adaptive clause) | Week 2 — needs operator-in-the-room session per the prompt |

## § 06 — One pending gate item · operator action required

`claude_client.py`'s integration test is the only verification-gate item that doesn't pass automatically. It's gated on `ANTHROPIC_API_KEY` being present in the environment. After completing setup.md step 6 (creating real `.env` with the four credentials), run:

```
source .venv/bin/activate
python -m pytest tests/test_claude_client.py -v
```

Expected: 1 passed, 0 skipped. The test asserts the response shape and that an `llm_calls` row was written with non-null token counts and a 64-char SHA-256 prompt hash. A pass closes the gate. A failure means either the API key is bad or the Anthropic SDK shape changed since build time — both are debuggable from the `llm_calls` row contents.

## § 07 — Notes

The empty state is the *correct* state for Week 1. The replay reports zero trades because zero strategies are registered; the INDEX surfaces table is heavily em-dashed because most surfaces don't appear until Week 4+. Per the report-format-spec's "Empty-state full rendering" rule, both are fully-formed reports that happen to have zero rows — same header, same four-stat band, same dominant table with explicit "no variants registered" / "not yet · Week N" placeholders, same footer. Not a "no data yet" stub. The format conventions are load-bearing now, not later.

§ Flags · none

## § 08 — Post-Week-1 amendments

| Date | What | Reference |
| --- | --- | --- |
| 2026-05-17 | Cron wire-up: `.github/workflows/fetch-and-commit.yml` runs every 5 minutes — fetch → render INDEX → commit `trader.db` + `INDEX.md` → push. Single workflow, single commit per run. | [decision-log.md](decision-log.md) 2026-05-17 entry · [setup.md](setup.md) "Cron commit-back pattern" |
| 2026-05-17 | Curriculum anchor switched from hardcoded date to `get_curriculum_start()` — first `runs` row with `status='ok'` + 56 days. Was `first_successful_run_at`; renamed for clarity. Sublabel now `ends YYYY-MM-DD` instead of `calendar`. | [render_index.py](render_index.py) |
| 2026-05-17 | `trader.db` whitelisted in `.gitignore` and committed (9.9MB initial state from the 30-day backfill). Cron commits subsequent state on every successful run. | [.gitignore](.gitignore) |

---

paper-api.alpaca.markets/v2/orders  ·  generated by week-1-status (manual, v0.1.0)

[github.com/pwysocan-droid/algotrading-paper](https://github.com/pwysocan-droid/algotrading-paper)
