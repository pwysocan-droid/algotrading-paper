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

# Strategy registry. The two defaults, per PROJECT.md "Strategy registry"
# spec — registered ahead of the Week 2 roster review so replay.py can
# produce real evidence for that decision instead of the review running
# on zero data. No parameter-sweep variants here yet; that's the second,
# gated step.
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
        "enabled": True,
        "phase_qualified": True,
    },
    "macross_default": {
        "strategy": "macross",
        "params": {"fast": 12, "slow": 26, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": True,
        "phase_qualified": True,
    },
}
