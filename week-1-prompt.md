# Week 1 — Opening Prompt for Claude Code

Use this prompt verbatim (or near-verbatim) when starting Week 1 in
Claude Code. It supersedes the opener in `setup.md`, which was
drafted before the 2026-04-26 reframe. This prompt reflects:

- The reframe (LLM integration moved from Week 7 to Week 1)
- Week 0 synthesis findings (cluster-4 methodologies, look-ahead-
  bias guard, future-self-letter format)
- The report-format spec (`report-format-spec.md` — INDEX page,
  v1/v2 patterns, em-dash empty states, four-stat bands, `§`
  section markers)
- Explicit scope-bounding (Week 1 is skeleton + LLM client + report
  rendering; not variants, not tuner, not external sources)

---

## The prompt

```
Read the following files in this order, in full, before writing any
code:

1. PROJECT.md
2. philosophy.md
3. decision-log.md (entire file — newest entry on top is the 2026-
   04-26 reframe; pay particular attention to it)
4. playbook.md
5. week-0-synthesis.md (Week 0 deliverable; informs how you build
   Week 1's LLM integration and what disciplines to bake in)
6. report-format-spec.md (defines INDEX.md and routine report
   formats — non-negotiable for any markdown output you produce)
7. roadmap.md (navigational; the to-do list against which Week 1's
   deliverable is measured)

Once you've read all seven, reply with a one-paragraph confirmation
that summarizes what Week 1's scope IS and what Week 1's scope is
NOT, plus name the three load-bearing format conventions from the
report-format spec (em-dash empty states, four-stat band, §
section markers). Don't write code yet. I want to verify you
understand the scope before you start building.

# Week 1 scope: build

The skeleton of the system, end-to-end, with no strategies
registered and no external data sources connected, but with the
LLM client and the methodology-supporting file structure in place,
and with the report-rendering layer that will serve every routine
output for the rest of the project.

## 1. Database layer (db.py)

Versioned migrations using the same pattern as my wagon-watcher
project: paired .up.sql / .down.sql files, a schema_migrations
table tracking applied migrations, with idempotent application.
Include tests for migration up/down (apply each migration, verify
schema; roll back, verify schema returned to previous state).

The seven tables specified in PROJECT.md's Schema section: bars,
context_data, signals, trades, decisions, runs, recommendations.
Use the exact column definitions in PROJECT.md.

Plus an eighth table for the LLM call log (per Week 0 reframe):
llm_calls, with columns: id (PK), timestamp, prompt_hash,
prompt_full, response_full, model, latency_ms, prompt_tokens,
completion_tokens, total_tokens, called_from (free-text tag like
'adversarial_review' or 'feature_extraction').

Migrations live in db/migrations/ as 001_create_bars.up.sql /
001_create_bars.down.sql, etc. One migration per table is fine.

## 2. Data layer (fetch.py)

Polls Alpaca market data for the five WATCHED_SYMBOLS
(BTC/USD, ETH/USD, SOL/USD, LINK/USD, AVAX/USD), 5-minute bars,
writes to bars table. Idempotent: re-running over the same window
should not produce duplicate rows (use the (symbol, timestamp)
primary key for upsert behavior).

Build against both fixture data (canned bars in tests/fixtures/
for unit tests) and live Alpaca paper API. Use the credentials in
.env.

Failed fetches log a row to runs with status='failed'. Successful
runs log status='ok' with bars_added count. The runs table is the
audit trail for system health; its writes are non-negotiable.

## 3. Signal layer (signals.py)

Skeleton only. The signal layer reads from bars and (later)
context_data, runs each enabled variant in STRATEGY_VARIANTS, and
emits Signal objects to the signals table. For Week 1,
STRATEGY_VARIANTS is an empty dict — no strategies are registered.
The signal layer should run cleanly against an empty registry and
emit zero signals.

The shape of the strategy-variant interface should match
PROJECT.md's specification exactly: each variant is
(strategy_name, params, context_keys, enabled, phase_qualified).
Pure functions; no side effects beyond the database writes the
signal-layer driver performs.

## 4. Execution layer (execute.py)

Skeleton only. Reads from signals, applies position-limit checks
($200/trade max, $1,000 total exposure max, 5 concurrent positions
max), writes to trades and decisions. For Week 1, with no
strategies registered, execute.py runs cleanly against zero
signals and emits zero trades.

The position-limit checks must be enforced in code, not honor
system. The execution layer refuses to place an order that would
breach any limit, and logs a decision row with action='rejected'
and reason explaining which limit was breached.

## 5. Replay tool (replay.py)

Reads bars + (empty) STRATEGY_VARIANTS, runs the signal layer in
backtest mode against historical bars, runs the execution layer
against the resulting (empty) signals, produces a markdown report
in reports/ following the report-format spec's v1 pattern.

CRITICAL: look-ahead-bias guard. When `replay.py` simulates a
trade, the entry price for a signal generated on bar N's close
must be the OPEN of bar N+1, not bar N's close. The signal is
"available" at bar N's close in real time, but the trade can only
execute against the next bar's open. Without this guard, backtest
results will be optimistic by the size of the typical close-to-
open move, which over hundreds of trades is substantial. This was
flagged in week-0-synthesis.md as a build-quality concern.
Implement the guard correctly the first time and add a test that
verifies it.

The Week 1 deliverable: `replay.py --variant=null --period=30d`
runs end-to-end against the bars table, produces a v1-pattern
report, and the report shows zero trades (because there are no
strategies registered). Per the report-format spec, the empty-
state must be a fully-formed report — same header, same four-
stat band (with em-dashes for not-yet-present values, explicit
zeros for real-zero values), same dominant table (with explicit
"no variants registered" placeholder), same footer. NOT a
placeholder report saying "no data yet."

## 6. Report rendering module (render.py)

Per report-format-spec.md's "Implementation note: render module"
section. Single module that emits markdown reports following the
v1 (snapshot) and v2 (temporal) patterns from the spec.

Required exports for Week 1:

- `render_v1_report(data: dict) -> str` — for snapshot reports
- `render_index(state: dict) -> str` — for INDEX.md
- Utility functions for the four-stat band, the flags section,
  the numeric formatting (per the table in the spec), and the
  trade ID linking

`render_v2_report` (for temporal reports) does NOT need to be
built in Week 1. The first v2 report is the weekly A/B in Week 4.
Defer.

`replay.py` calls `render_v1_report` to produce its output.
`render_index.py` (next deliverable) calls `render_index` to
produce INDEX.md.

## 7. Index page generator (render_index.py)

A small script that:

- Scans the repo for the latest of each surface kind (`reports/`,
  `reports/ab/`, `recommendations/`, `reviews/`, plus
  `week-N-status.md` files at the root)
- Computes the project-level four-stat values: system uptime over
  the last 4 weeks (from runs table), trades this week (from
  trades table, ISO week boundary), Phase 2 gates passed (a
  function checking the three gates against current state), days
  to phase 1 review (calendar arithmetic against the curriculum
  end date)
- Calls `render_index` from render.py with the assembled state
- Writes INDEX.md at the repo root, overwriting any prior version

Idempotent: running it twice in a row should produce the same
output.

For Week 1, almost every surface kind has no instances yet, so
INDEX.md will be heavily em-dashed. That's correct. The empty-
state version is the deliverable.

Implementation note: this script should be runnable manually
(`python render_index.py`) and also callable from a git pre-
commit hook or a workflow trigger. Wire the manual mode for
Week 1; the auto-regeneration trigger is Week 2 scope when the
cron lands.

## 8. Claude API client (claude_client.py)

The reframe moved LLM integration from Week 7 to Week 1. Build a
clean Claude API client that:

- Reads ANTHROPIC_API_KEY from .env
- Uses the Messages API. Verify the current production Sonnet
  model identifier against the Anthropic API docs at the time of
  build; do not hardcode a model string from this prompt
- Logs every call to the llm_calls table with: timestamp, prompt
  (full and hash), response, model, latency, token counts,
  called_from tag — so cost and performance are auditable from
  day one
- Has a structured-output mode that takes a Pydantic schema and
  returns a parsed object. This is the mode Week 5+ feature-
  extraction will use
- Has a free-text mode for the adversarial-review prompts (Week 1
  has one defined; later weeks may add more)

For Week 1, build the client and write a single integration test
that calls the API with a trivial prompt and verifies the
response shape. Don't over-build — there's no strategy yet to
extract features for.

## 9. Adversarial-review prompt template (reviews/templates/friday-bear-case.md)

Per cluster-4 methodology 4G. Structured prompt template that
Claude reads each Friday to argue the bear case against the
week's results. For Week 1, draft the template; refine over
Phase 1.

The template should:

- Take as input: the week's trade history, the week's runs log,
  the week's decisions log, the prior week's bear case (when
  available)
- Instruct Claude to argue the strongest possible bear case:
  "your strategies are overfit, your promotion was lucky, your
  data source is noise, your A/B comparator is finding spurious
  significance" — forced steelmanning, not balanced review
- Specifically prohibit hedging or "well, on the other hand"
  framings
- Compare the current week's bear case to the prior week's (when
  available) and flag if the bear case is getting milder over
  time — that drift is itself a signal worth catching

Lives in reviews/templates/. Each Friday's actual review goes in
reviews/YYYY-WW-friday.md.

## 10. The reviews/ directory structure

Create the directory:

```
reviews/
├── templates/
│   ├── friday-bear-case.md
│   └── (later: prediction.md, patterns.md as those methodologies
│       come online)
├── (Friday reviews accumulate as YYYY-WW-friday.md)
├── (preregistered predictions accumulate as YYYY-WW-prediction.md
│   from Week 2 onward, per cluster-4 methodology 4A)
└── (monthly pattern surfacing accumulates as YYYY-MM-patterns.md
    from Month 2 onward, per cluster-4 methodology 4H)
```

For Week 1, only the templates/ subdirectory needs content.

## 11. Future-self-letter convention in decision-log.md

Cluster-4 methodology 4F adopts future-self letters as a section
appended to specific decision-log entries (Phase 2 exit
conditions, Phase 2 entry gates, the reframe entry's adaptive
clause, and any future hard-rule entry). The format isn't
infrastructure — it's a documentation convention.

Add a short section to the top of decision-log.md (before the
2026-04-26 entries) titled "Future-self-letter convention" that
specifies the format, with an example. The example should be a
worked future-self letter for the Phase 2 drawdown trigger. Don't
write letters for all the existing entries in this prompt — that's
a separate session that needs the operator in the room. Just
establish the convention.

# Week 1 scope: do NOT build

These belong to later weeks and have decision-log entries gating
their introduction. Building any of them now would violate the
curriculum's one-factor-at-a-time discipline:

- ANY actual strategies (Bollinger, MA-crossover, or candidates
  surfaced in week-0-synthesis.md). The Week 2 strategy-roster
  review decides what gets registered, after the synthesis-
  informed decision is committed to decision-log.md.
- The walk-forward tuner (tune.py) — Week 4 scope.
- The A/B comparator (compare.py) — Week 4 scope.
- The v2 report renderer (`render_v2_report` in render.py) — Week
  4 scope, when the first temporal report appears.
- ANY external data sources (Fear & Greed Index, BTC dominance,
  news feeds) — Weeks 5+.
- LLM-derived features for trading decisions — Week 7 in original
  spec, brought forward but only after Week 4's promotion-loop
  infrastructure is in place. Week 1's LLM client is for the
  adversarial review only.
- Any styled HTML rendering of reports. Markdown is the source-
  of-truth. The HTML surface decision is deferred to Week 2 per
  the roadmap.
- Any analytics dashboards or reporting beyond the markdown
  reports the spec covers.
- Any cron / GitHub Actions wiring. The 5-minute live cron is
  Week 2 scope; Week 1 ends with `replay.py` and `render_index.py`
  running on demand, not on schedule.

If you find yourself wanting to build any of the above because it
"would be cleaner to do now" or "is a small addition" — stop. Add
a note to a TODO file noting what you wanted to do and why; we'll
review it at end-of-week. Scope creep is the curriculum's
documented failure mode.

# Process

- Build in this order: db.py + migrations → fetch.py → render.py
  (utilities first, then v1 renderer) → signals.py skeleton →
  execute.py skeleton → replay.py → render_index.py →
  claude_client.py → adversarial-review template → future-self-
  letter convention. The render module comes early because every
  subsequent deliverable that produces output uses it.
- Each module gets unit tests. The tests for db.py migrations,
  the look-ahead-bias guard in replay.py, and the empty-state
  rendering in render.py are non-negotiable. Other tests are
  best-effort given the scope.
- After each module, commit with a clear message. Don't squash
  Week 1 into a single commit; the granularity helps the
  decision-log review.
- At end of week (or whenever you think Week 1 is done), produce
  week-1-status.md as a v1-pattern report listing: what was built,
  what tests pass, what's deferred to Week 2, and any decisions
  you made that should be in decision-log.md (build-time choices
  that aren't spec'd in PROJECT.md, e.g., specific Pydantic
  schemas for the LLM structured-output mode).

# Verification

Week 1 is done when:

- All eight tables exist with correct schemas, verified by
  inspecting the SQLite file
- `python -m pytest tests/` passes with all tests green
- `replay.py --variant=null --period=30d` runs end-to-end against
  bars and produces a v1-pattern empty-state report — em-dashes
  where appropriate, explicit zeros where appropriate, fully-
  formed sections throughout, NOT a "no data yet" placeholder
- `python render_index.py` produces INDEX.md at the repo root,
  reflecting the state described above (heavily em-dashed surface
  list, project-level four-stat band populated)
- `claude_client.py`'s integration test passes (one real API
  call, verified response shape, llm_calls table row written)
- `reviews/templates/friday-bear-case.md` exists and is readable
- `decision-log.md` has the future-self-letter convention section
  at the top, with one worked example for the Phase 2 drawdown
  trigger
- `week-1-status.md` exists at the repo root as a v1-pattern
  report

If any of these fails or is unclear, say so explicitly in
week-1-status.md rather than working around it.
```

---

## Notes on using the prompt

- Paste the prompt (between the triple-backtick fences above) into
  Claude Code as the opening message of the Week 1 conversation.
- Claude Code should respond first with the one-paragraph scope
  confirmation plus the three named conventions. If the
  confirmation is wrong (it adds scope, drops scope, or misframes
  any of the conventions), correct before letting it start
  building.
- If Claude Code wants to deviate from the build order or skip
  tests, treat that as a yellow flag and ask why. Sometimes the
  reasoning is good (a simpler dependency order); sometimes it's
  scope-creep instinct.
- At end of week, run the cluster-4 4G adversarial review against
  the Week 1 status report. The first Friday review is on
  infrastructure, not strategies, but the discipline of running it
  matters more than the substance.
