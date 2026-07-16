"""Project-wide constants and configuration.

Single source of truth for symbols, limits, risk controls, and the strategy
registry. Imported by fetch.py, signals.py, execute.py, replay.py.
"""

from typing import TypedDict


class StrategyVariant(TypedDict, total=False):
    strategy: str
    params: dict
    context_keys: list[str]
    enabled: bool
    phase_qualified: bool


WATCHED_SYMBOLS: list[str] = ["BTC/USD", "ETH/USD", "SOL/USD", "LINK/USD", "AVAX/USD"]

# Position-sizing limits — enforced in code, not honor system. PROJECT.md "Capital model".
MAX_POSITION_USD: float = 200.0
MAX_TOTAL_EXPOSURE_USD: float = 1_000.0
MAX_CONCURRENT_POSITIONS: int = 5

# Risk controls — PROJECT.md Layer 4.
STOP_LOSS_PCT: float = 0.03
TAKE_PROFIT_PCT: float = 0.05
TIME_EXIT_HOURS: int = 24
SYMBOL_COOLDOWN_HOURS: int = 1

# Backtest realism. TAKER_FEE_PCT is sourced: PROJECT.md "Honest expectations"
# ("0.25% Alpaca crypto fees... every round-trip costs ~$1" on a $200 position),
# charged on notional at both entry and exit. SLIPPAGE_PCT is NOT sourced from
# any project doc — no slippage assumption exists anywhere in PROJECT.md,
# decision-log.md, or roadmap.md. 0.05%/side is a conservative placeholder for
# liquid crypto pairs on 5-min bars; treat it as unconfirmed until it gets its
# own decision-log entry.
TAKER_FEE_PCT: float = 0.0025
SLIPPAGE_PCT: float = 0.0005

ALPACA_PAPER_BASE_URL: str = "https://paper-api.alpaca.markets"
ALPACA_DATA_BASE_URL: str = "https://data.alpaca.markets"

BAR_TIMEFRAME_MINUTES: int = 5

# Strategy registry. ALL VARIANTS RETIRED per decision-log 2026-07-02
# ("Retire Bollinger and MA-crossover") — every variant with a real sample
# was negative over the 6-month realistic-constraint backtest. Entries are
# kept with enabled=False (not deleted) so the replay reports that fed the
# decision stay reproducible. Nothing here is live; the next roster comes
# from LLM-surfaced candidates per the adaptation-ladder entry.
#
# Original registration context: the two defaults per PROJECT.md "Strategy
# registry" spec, plus the Week 3 parameter-sweep variants (roadmap.md
# Week 3 / decision_log_queue.md "Variant-explosion-to-Day-1"), registered
# together ahead of the Week 2 roster review so replay.py's evidence
# covered both questions at once: which base strategy, and which
# parameterization.
#
# bollinger_tight/loose/long/quick and macross_fast/slow are named verbatim
# in PROJECT.md's Week 3 spec ("Examples: ..."). bollinger_verytight,
# macross_veryfast, macross_veryslow, and macross_balanced are NOT in any
# project doc — added here to reach the 10-variant target, following the
# same single-parameter-perturbation-from-default pattern as the named
# ones. Flagging the split so it's auditable, not silently blended in.
#
# All variants share tp=0.05/sl=0.03 with the defaults — Week 3 doesn't
# specify per-variant risk parameters, and note replay.py's simulate_exit
# currently reads TAKE_PROFIT_PCT/STOP_LOSS_PCT from config globals, not
# from variant["params"], so a variant with different tp/sl wouldn't
# actually get it honored in backtest yet. Doesn't affect this batch since
# all values match the global defaults, but it's a real gap if a future
# variant wants different risk parameters.
STRATEGY_VARIANTS: dict[str, StrategyVariant] = {
    "bollinger_default": {
        "strategy": "bollinger",
        "params": {
            "period": 20,
            "stddev": 2.0,
            "tp": 0.05,
            "sl": 0.03,
            "time_exit_hours": 24,
        },
        "context_keys": [],
        "enabled": False,
        "phase_qualified": True,
    },
    "macross_default": {
        "strategy": "macross",
        "params": {"fast": 12, "slow": 26, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": True,
    },
    # --- Bollinger parameter sweep (5) ---
    "bollinger_tight": {
        "strategy": "bollinger",
        "params": {"period": 20, "stddev": 1.5, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "bollinger_loose": {
        "strategy": "bollinger",
        "params": {"period": 20, "stddev": 2.5, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "bollinger_long": {
        "strategy": "bollinger",
        "params": {"period": 40, "stddev": 2.0, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "bollinger_quick": {
        "strategy": "bollinger",
        "params": {"period": 10, "stddev": 2.0, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "bollinger_verytight": {  # not in PROJECT.md — extends the tight/loose pattern
        "strategy": "bollinger",
        "params": {"period": 20, "stddev": 1.0, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    # --- MA-crossover parameter sweep (5) ---
    "macross_fast": {
        "strategy": "macross",
        "params": {"fast": 5, "slow": 15, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "macross_slow": {
        "strategy": "macross",
        "params": {"fast": 20, "slow": 50, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "macross_veryfast": {  # not in PROJECT.md — extends the fast/slow pattern
        "strategy": "macross",
        "params": {"fast": 3, "slow": 8, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "macross_veryslow": {  # not in PROJECT.md — extends the fast/slow pattern
        "strategy": "macross",
        "params": {"fast": 30, "slow": 90, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "macross_balanced": {  # not in PROJECT.md — midpoint between default and fast
        "strategy": "macross",
        "params": {"fast": 8, "slow": 21, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
}
