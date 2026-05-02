# algotrading-paper

A paper-trading research project that runs continuously, learns from
its own results within statistically defensible bounds, and earns the
right to deploy real capital by demonstrating that the *system itself*
works — not by hope.

The financial-markets sibling of the wagon-watcher. Same architectural
lineage: continuous observation of a public data feed, anomaly
detection against a learned baseline, auditable decision-making.
Different operational profile: where the wagon-watcher is observational
with human action on top, this project is autonomous (within strict
limits) with human-reviewed learning on top.

The Bloomberg-terminal pattern, distilled and run on a $0 budget
during Phase 1, then $1,000 of seed capital in Phase 2.

---

## Project philosophy

Three principles, stated up front because every architectural decision
in this doc serves them.

### 1. Spend the cheap part recklessly. Spend the expensive part carefully.

Paper trading is the cheap part. Real money is the expensive part.

Most retail traders do this backwards: they paper-trade timidly for
two weeks, get bored, and dump real money in. This project inverts
the discipline. Phase 1 (paper) is aggressive: many variants, fast
iteration, willingness to throw away half of what we built last week.
Phase 2 (real money) is conservative: frozen sources, frozen prompts,
no new variants without paper-validation first.

The transition between phases is *earned by data*, not chosen by
calendar.

### 2. The constraint is statistical power, not creativity.

Most retail trading projects don't fail because the strategies are
bad. They fail because the *learning loop is too slow* to detect that
the strategies are bad before the budget runs out. With ~10 trades per
day per variant, ~30 days are required to draw any statistically
defensible conclusion about whether a strategy works.

Therefore: the most efficient learning approach is not "try more
strategies faster." It is "maximize the rate at which we produce
statistically significant conclusions." Almost every architectural
decision in this doc serves that constraint.

The two implementations that follow from this principle:

- **Many variants in parallel, not many strategies in series.** Time
  is the scarce resource. Ten variants for a month produces ten
  evaluations; one strategy for ten months produces one. The
  registry pattern (below) supports arbitrary parallel variants
  with no per-variant infrastructure cost.
- **One factor at a time, not factorial designs.** Renaissance and
  Two Sigma can run factorial experiments because they trade tens of
  thousands of times per day. We can't. With limited trials, the
  technique that produces the most *learnable* results is changing
  one variable at a time — adding one external data source per week
  and measuring whether it helped, rather than five at once and
  guessing.

### 3. Boring strategies, exotic infrastructure.

Bollinger Bands and MA-crossover are textbook. They are 40+ years old.
They are not expected to beat the market.

What's being built and learned is the *system around them* — the
replay tool, the A/B comparator, the walk-forward tuner, the
external-research integration, the auditable decision log. A working
system on top of two known-failure-mode strategies is more valuable
than a broken system on top of clever-sounding ones, because the
system can outlive the strategies. The strategies can be swapped
out. The system can't be retrofitted.

A losing strategy you can debug is more valuable than a winning
strategy you can't explain.

---

## Phase structure

### Phase 1 — Paper

No real money. Architecture proves out, both strategies run, the
learning loop operates, you accumulate enough data to actually
evaluate. **Aggressive iteration, weekly variant explosion, willingness
to cut things that aren't working.**

Duration: 8 weeks minimum. The 8-week curriculum below is the
recommended path.

### Phase 2 — Seed real capital ($1,000)

Triggered when *all three* of the following are true:

1. **System uptime ≥ 95%** over the prior 4 weeks of cron runs (i.e.,
   not stalled on infrastructure issues for >5% of expected runs).
2. **At least one A/B-validated promotion has occurred** — the
   walk-forward tuner produced a recommendation, the recommendation
   was promoted into the registry as a new variant, that variant ran
   in parallel with its predecessor, and the A/B comparator declared
   it the winner with p<0.05 over a minimum 100 trades. *This is the
   architecture-based gate. It tests whether the experiment itself
   worked, regardless of whether any specific strategy was profitable.*
3. **Phase 1 paper P&L is positive over the prior 30 days** OR the
   user explicitly overrides this condition with a written justification
   in `decision-log.md`. (Negative-P&L Phase 2 entry is allowed but
   must be a deliberate decision, not a default.)

When Phase 2 begins:

- Live capital: $1,000 in a real Alpaca account
- Position sizing: max $200 per trade, max $1,000 total exposure,
  max 5 concurrent positions (same code, same constants, no changes)
- All variants and external data sources frozen at the configuration
  that earned the Phase 2 promotion
- New variants and new data sources continue to be developed in a
  parallel paper instance — never against the live account

### Phase 2 exit conditions

Real money returns to paper (or the project is archived) when *any*
of the following:

1. **Drawdown:** real-money account drops below $700 (-30%). Stop
   trading immediately, return remaining capital to paper, postmortem.
2. **Variance from paper:** if real-money returns diverge from paper-
   money returns by more than 50% over any 2-week window, something
   is wrong (likely fees, slippage, or an execution bug). Return to
   paper, debug, re-qualify.
3. **Time:** after 8 weeks of real money regardless of P&L, the
   project enters a mandatory review week. Either continue with a
   written justification, scale up with a written justification, or
   archive.

These rules exist to be re-read in week 4 of Phase 2 when the temptation
to override them will be at its peak.

---

## Architecture

Six conceptual layers. Each runs as its own module, each can be tested
in isolation, each can be replaced without touching the others.

```
┌─────────────────────────────────────────────────────────┐
│ 6. Learning layer        — replay, A/B, re-tuning       │
├─────────────────────────────────────────────────────────┤
│ 5. Analytics layer       — digests, dashboards          │
├─────────────────────────────────────────────────────────┤
│ 4. Execution layer       — places orders via Alpaca     │
├─────────────────────────────────────────────────────────┤
│ 3. Signal layer          — strategies emit buy/sell     │
├─────────────────────────────────────────────────────────┤
│ 2. Context layer         — external research data       │
├─────────────────────────────────────────────────────────┤
│ 1. Data layer            — fetches and stores OHLCV     │
└─────────────────────────────────────────────────────────┘
```

**Hard rule: each layer only depends on layers below it.** Same
discipline as wagon-watcher's pipeline, with two new layers (Context
and Learning) reflecting this project's additional ambition.

### Layer 1 — Data
Polls Alpaca market data every 5 minutes. Pulls OHLCV bars for watched
symbols. Writes to SQLite. Source of truth for "what did the market do."

### Layer 2 — Context (new vs. wagon-watcher)
Pulls external research data on its own schedule (varies by source —
F&G is daily, news is hourly, on-chain metrics every 6 hours). Stores
in its own tables. Exposes a clean read API to the signal layer.
Phase 1 sources are added one at a time per the curriculum below.

### Layer 3 — Signal
For each symbol, runs each *enabled* strategy variant against the
latest bars and (optionally) context. A strategy variant is:
`(strategy_name, params, context_keys)`. Pure functions, no side effects.
Returns `Signal | None` with full reasoning logged.

### Layer 4 — Execution
Receives signals. Decides whether to act based on position-sizing rules
($200/trade, $1000 total, 5 concurrent), risk controls (-3% stop, +5%
target, 24h time exit), and one-trade-per-symbol-per-hour cooldown.
Places paper or real orders via Alpaca depending on phase. Logs every
decision — placed AND rejected.

### Layer 5 — Analytics
Daily digest, weekly performance report, trade replay views.
Reads from DB; writes only to `reports/`.

### Layer 6 — Learning
Three modules, each independent, each running offline (separate cron):

- **Replay (`replay.py`):** ad-hoc, given a variant and a date range,
  reports what would have traded. Foundation of the learning loop.
- **A/B comparator (`compare.py`):** reads `trades`, groups by
  variant, computes Sharpe + max DD + win rate + statistical
  significance of pairwise differences. Reports; does not auto-promote.
- **Walk-forward tuner (`tune.py`):** daily at 02:00 UTC. Re-runs
  replay over the last 30 days with a parameter grid. Writes
  top-3 candidates per base strategy to `recommendations` table.

**Layer 6 never modifies live strategy parameters automatically.**
It recommends; humans promote. This boundary is non-negotiable.
Online ML at retail scale (~10 trades/day) is statistically broken —
too few data points, near-certain overfitting. Manual review is the
safety valve, and the discipline of writing down *why* a promotion
was approved is itself part of the learning.

---

## Capital model

Alpaca paper accounts default to $100,000. Phase 1 treats the account
as if it had $1,000 by enforcing **strict position limits in code**:

- Max position size per trade: **$200**
- Max total open exposure: **$1,000**
- Max concurrent open positions: **5**

Enforced in code, not honor system. The execution layer refuses to
place an order that would breach any limit. The full $100k paper
balance exists only as safety margin — if a bug attempts a $5,000
trade, the position-limit check rejects it before the order goes out.

Phase 2 uses the same code, same constants, against a real $1,000
account. The constraint *is* the discipline.

---

## The 8-week curriculum

This is the build/learn sequence, optimized for maximum statistical
power within the time budget. Each week ends with a working,
committable state and a specific learning outcome.

### Week 1 — Architecture only, no strategies

Build: data layer, signal layer skeleton (no strategies registered),
execution layer skeleton, replay tool.

Deliverable: `replay.py --variant=null --period=30d` runs, produces
a report showing zero trades. The plumbing works end-to-end.

Learning outcome: the system can fetch, store, query, and replay.
Failure modes that show up here are infrastructure failures, not
strategy failures — easiest to debug.

### Week 2 — Two strategies, one variant each

Build: register `bollinger_default` (period=20, σ=2, tp=5%, sl=3%)
and `macross_default` (fast=12, slow=26, tp=5%, sl=3%). Both run
live paper. Both replay against the last 6 months of historical bars.

Deliverable: 6 months of replay results + ~14 days of live paper
trades. First A/B comparator output (likely insignificant — too few
trades).

Learning outcome: how the two strategies behave on historical data
across different market regimes (the last 6 months almost certainly
include both trends and chops, so both strategies will have good and
bad weeks).

### Week 3 — Variant explosion

Build: register 6–10 parameter variants of each base strategy.
Examples: `bollinger_tight` (σ=1.5), `bollinger_loose` (σ=2.5),
`bollinger_long` (period=40), `bollinger_quick` (period=10),
`macross_fast` (5/15), `macross_slow` (20/50), etc.

All variants run in parallel. The execution layer enforces the
overall position limits across the entire portfolio of variants —
*not* per-variant — so adding variants doesn't increase total
exposure.

Deliverable: a ranked list of which parameter combinations are
working and which aren't. First statistically-suggestive A/B results
(though probably not significant yet — that takes ~30 trades minimum).

Learning outcome: the parameter sensitivity of each strategy.
**This is when learning actually starts compounding.**

### Week 4 — Walk-forward tuner online

Build: `tune.py` runs nightly at 02:00 UTC. Re-runs replay over the
last 30 days with a parameter grid. Writes top-3 candidates per base
strategy to `recommendations` table. Each morning, review and promote
the top candidate (if its hypothetical-P&L exceeds the live variant
by >20%).

Deliverable: at least one human-promoted variant in the registry by
end of week 4. The system is now demonstrably self-improving.

Learning outcome: whether the walk-forward tuner produces variants
that hold up *out-of-sample* (in week 5+) or only look good
*in-sample* (during the period they were tuned on). This is the
single most important question about whether the learning loop works.

### Week 5 — One external data source: Crypto Fear & Greed Index

Build: Layer 2 (Context) goes live. F&G API is the simplest possible
external source — single number, daily update, lagged-but-meaningful.
Cache in `context_data` table. Build one new variant per strategy
that uses it (e.g., `bollinger_fg_contrarian`: only buy on Bollinger
oversold IF F&G < 30; only sell on overbought IF F&G > 70). Run
alongside existing variants.

Deliverable: 1 week of A/B data on whether F&G-conditioning helped.

Learning outcome: whether sentiment-conditioning improves a textbook
strategy at all. Likely answer: marginally, in some regimes. That's
fine — the goal is to find out, not to prove a hypothesis.

### Week 6 — Second external data source (conditional)

Build: if F&G demonstrably helped in week 5, add a second source —
CoinGecko BTC dominance. If F&G didn't help, *cut* it and try
something else (e.g., Glassnode exchange inflows). The discipline of
cutting things that don't work is what most retail systems lack.

Deliverable: 1 week of A/B data on the second source.

Learning outcome: which categories of external data move the needle
for technical strategies and which don't. By end of week 6 you should
have a working hypothesis.

### Week 7 — LLM as feature extractor

Build: Claude API integration. Twice-daily, the system pulls the top
5 crypto news headlines from a fixed set of RSS feeds (CoinDesk, The
Block, Decrypt) and asks Claude to produce a structured sentiment
score per watched token. Score is cached for the next 12 hours. One
new variant per strategy uses it.

**The LLM does not decide trades.** It produces a number. Rule-based
strategies decide trades using that number alongside technical
indicators. This is feature extraction, not delegation.

Cost: ~$10–20/week. Logged with input/output/model/latency for every
call.

Deliverable: 1 week of A/B data on whether LLM-derived sentiment
features improve performance.

Learning outcome: whether unstructured-text-via-LLM is a useful signal
source at retail size, or whether it's noise dressed up as signal.

### Week 8 — Decision week

No new building. The system runs as-is. Generate a comprehensive
8-week review:

- Which variants survived and why
- Which external sources contributed and which didn't
- What the walk-forward tuner promoted and whether those promotions
  outperformed
- Total paper P&L, max drawdown, Sharpe per variant, system uptime
- Phase 2 entry decision: do all three gates pass?

Deliverable: `phase1-review.md` in the repo. Decision committed in
writing before any real money moves.

Learning outcome: whether *the experiment itself* worked — independent
of whether any specific strategy was profitable.

---

## What's explicitly NOT in scope

These are temptations the project will face. Listed here so they can
be re-read when they become tempting.

- **Online ML / training models on trade history.** With ~10 trades/day,
  there's far too little data to train anything that won't overfit.
  Layer 6 is rule-based parameter search and statistical comparison,
  not a model. This boundary is non-negotiable through v2.
- **LLM-as-oracle.** The LLM never directly decides trades. It only
  produces structured features that feed rule-based strategies.
- **More than one new external source per week in Phase 1.** Adding
  three sources at once produces a tangle that can't be untangled.
  One factor at a time.
- **Equities in Phase 1.** Equities introduce market hours, the PDT
  rule, dividend events, and after-hours gaps — every one of which is
  a debugging surface. Phase 1 proves the architecture against one
  clock and one fee structure. v2 (after Phase 2 stabilizes or after
  Phase 1 archives) is when equities arrive.
- **Pattern-day-trader workarounds.** If a strategy somehow generates
  >3 day-trades in 5 days on a real-money equities account, the broker
  will reject the orders. Crypto sidesteps this. Don't try to engineer
  around it.
- **High-frequency trading.** The cron is 5 minutes. HFT is microseconds.
  Different game, different infrastructure, different budget.
- **New strategy families in Phase 1.** Volatility breakout, pairs
  trading, momentum-on-volume — all interesting, all out of scope for
  Phase 1. Phase 1 proves the system on two textbook strategies. New
  families come in v2 once the *system* is proven.
- **Real-money trading before Phase 2 gates pass.** No exceptions.

---

## Schema

Seven tables. The wagon-watcher uses five; this project's additional
two are `context_data` and `recommendations`.

### `bars`
```sql
CREATE TABLE bars (
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (symbol, timestamp)
);
CREATE INDEX bars_symbol_ts ON bars (symbol, timestamp DESC);
```

### `context_data` (new)
External research data. Generic key-value-with-timestamp shape so new
sources slot in without schema changes.

```sql
CREATE TABLE context_data (
    source TEXT NOT NULL,           -- 'fear_greed' | 'btc_dominance' | 'llm_sentiment' | etc.
    key TEXT NOT NULL,              -- e.g., 'BTC' for token-specific, 'global' for market-wide
    timestamp TEXT NOT NULL,
    value_numeric REAL,
    value_text TEXT,
    metadata_json TEXT,             -- source-specific extra fields
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (source, key, timestamp)
);
CREATE INDEX context_lookup ON context_data (source, key, timestamp DESC);
```

### `signals`
```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    variant_name TEXT NOT NULL,
    strategy TEXT NOT NULL,
    side TEXT NOT NULL,
    bar_timestamp TEXT NOT NULL,
    price_at_signal REAL NOT NULL,
    reasoning_json TEXT NOT NULL,
    context_used_json TEXT,         -- which context keys were read
    emitted_at TEXT NOT NULL,
    UNIQUE (symbol, variant_name, bar_timestamp, side)
);
```

### `trades`
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    signal_id INTEGER REFERENCES signals(id),
    variant_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    qty REAL NOT NULL,
    entry_price REAL NOT NULL,
    entry_time TEXT NOT NULL,
    exit_price REAL,
    exit_time TEXT,
    exit_reason TEXT,
    pnl_usd REAL,
    pnl_pct REAL,
    is_real_money INTEGER NOT NULL DEFAULT 0,  -- 0 = paper, 1 = real
    alpaca_order_id TEXT,
    status TEXT NOT NULL
);
```

### `decisions`
```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES signals(id),
    decided_at TEXT NOT NULL,
    action TEXT NOT NULL,
    trade_id INTEGER REFERENCES trades(id),
    reason TEXT NOT NULL
);
```

### `runs`
```sql
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    bars_added INTEGER,
    context_rows_added INTEGER,
    signals_emitted INTEGER,
    trades_placed INTEGER,
    error_text TEXT
);
```

### `recommendations` (new)
```sql
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    base_strategy TEXT NOT NULL,
    proposed_name TEXT NOT NULL,
    proposed_params_json TEXT NOT NULL,
    backtested_period TEXT NOT NULL,
    backtest_pnl_usd REAL NOT NULL,
    backtest_sharpe REAL,
    backtest_max_dd REAL,
    n_trades INTEGER NOT NULL,
    promoted INTEGER DEFAULT 0,
    promoted_at TEXT,
    promoted_by_decision_log_entry TEXT  -- ref to decision-log.md entry
);
```

---

## Strategy registry

Single source of truth for "what's running." Read by the execution
layer; written to (proposed-additions only) by the learning layer.

```python
STRATEGY_VARIANTS = {
    "bollinger_default": {
        "strategy": "bollinger",
        "params": {"period": 20, "stddev": 2.0,
                   "tp": 0.05, "sl": 0.03,
                   "time_exit_hours": 24},
        "context_keys": [],
        "enabled": True,
        "phase_qualified": True,  # cleared for Phase 2 if reached
    },
    "macross_default": {
        "strategy": "macross",
        "params": {"fast": 12, "slow": 26,
                   "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": True,
        "phase_qualified": True,
    },
    # Variants from Layer 6 walk-forward recommendations get added
    # here as humans promote them.
    # "bollinger_v2_tuned": { ... },
    # "bollinger_fg_contrarian": { ..., "context_keys": ["fear_greed"] },
}
```

When a variant is promoted from `recommendations` table to this
registry, the corresponding row is updated (`promoted=1`,
`promoted_at` and `promoted_by_decision_log_entry` set). Both the code
change and the decision-log entry are required for the promotion to
count as "valid" toward the Phase 2 gates.

---

## Watched symbols (Phase 1)

Crypto only, USD-denominated, 24/7 trading.

```python
WATCHED_SYMBOLS = ["BTC/USD", "ETH/USD", "SOL/USD", "LINK/USD", "AVAX/USD"]
```

Five is enough variety to see strategies behave differently across
assets, few enough to debug each one individually. v2 expands this
list and adds equities.

---

## External data sources (Phase 1)

Added one per week per the curriculum. Frozen at Phase 2 entry.

| Source | Layer 2 key | Cost | Cadence | Added in week |
|---|---|---|---|---|
| Crypto Fear & Greed Index | `fear_greed` | free | daily | 5 |
| (TBD week 6 — depends on week 5 result) | — | free | — | 6 |
| Claude API (news sentiment) | `llm_sentiment` | ~$10–20/wk | 12h | 7 |

If a source doesn't help in its evaluation week, it's *cut*, not
preserved. The discipline of cutting things that don't work is the
discipline most retail systems lack. Cuts must be logged in
`decision-log.md` with the reasoning.

---

## Pipeline

```
fetch.py        → bars
context.py      → context_data
       ↓
signals.py      → signals
       ↓
execute.py      → trades + decisions
       ↓
analytics.py    → reports/

(separate cron, daily 02:00 UTC)
tune.py         → recommendations
compare.py      → reports/ab/
```

Each script exits non-zero on failure. The pipeline fails closed: if
`fetch.py` breaks, signals don't fire on stale data; if `signals.py`
breaks, no trades; if `execute.py` breaks, the analytics still
produces its report (showing the gap).

---

## UI / Design

Reuse the wagon-watcher design system unchanged: SBB structural
foundation, contemporary ECAL practice as the modern layer. Inter as
the open-source default sans, JetBrains/IBM Plex Mono for data, no
Helvetica anywhere. SBB Red `#EB0000` as the only signal color.

The trade ID is the canonical identifier in this project, the way the
VIN was canonical in wagon-watcher. Every reference to a trade is
rendered as the trade ID, monospace, underlined, linking to the
Alpaca dashboard view of that order. In Phase 2 the same convention
applies but links go to the live-account view instead of paper.

Surfaces:

- **Daily digest (`reports/YYYY-MM-DD.md`):** committed to git,
  GitHub-rendered. Section markers, tabular data, marginalia footer.
- **Weekly A/B report (`reports/ab/YYYY-WW.md`):** per-variant
  P&L curves as inline mono-text ASCII. No images — phone-readable.
- **Recommendations (`recommendations/YYYY-MM-DD.md`):** human-
  readable form of recommendations table. Reviewed before promoting.
- **Phase review (`phase1-review.md`, `phase2-review.md`):** the
  decision documents that gate phase transitions.
- **Notification embeds:** identical card style to wagon-watcher.
  Tier 1 alerts get the SBB-Red 3px left rule.

---

## Honest expectations

Most retail algorithmic-trading systems lose money. The reasons:

- **Spreads and fees** eat margin faster than retail strategies can
  earn it. At $200 per trade with 0.25% Alpaca crypto fees, every
  round-trip costs ~$1. A strategy needs to clear $1 per round-trip
  on average just to break even.
- **Survivorship bias** — published strategies are the ones that
  worked. The ones that didn't are invisible.
- **Overfitting** — parameter tuning on historical data produces
  strategies that look great in backtest and fail live. The
  walk-forward tuner mitigates but does not eliminate this.
- **Regime change** — markets shift; what worked stops working.

The two strategies here will exhibit some or all of these failures.
The walk-forward recommendations will too — some will be overfit to
recent noise and fail in the next 30 days.

That's expected. The point of the project is to *observe* the
failures cleanly enough to learn from them. Phase 2 is the test of
whether the lessons learned in Phase 1 generalize to real capital —
and that's a real question, not a foregone conclusion. It's
plausible the system loses the full $1,000 in Phase 2 even after a
successful Phase 1. If that happens, the postmortem is the deliverable.

---

## What "done" means

Phase 1 is "done" when the 8-week curriculum completes and a
`phase1-review.md` is committed with the Phase 2 decision (proceed,
extend Phase 1, or archive).

Phase 2 is "done" when one of: the drawdown threshold is hit, the
8-week mandatory review reaches its decision point, or the user
explicitly archives.

The repo is archived once Phase 2 ends (in any direction) with a
final postmortem. The architecture is reusable for v2 if the user
wants to keep going; the *project* is bounded.

Until then, this is a research project, not a hobby. New features
only get built if they help understand whether the system works —
not because they sound interesting.
