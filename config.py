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

ALPACA_PAPER_BASE_URL: str = "https://paper-api.alpaca.markets"
ALPACA_DATA_BASE_URL: str = "https://data.alpaca.markets"

BAR_TIMEFRAME_MINUTES: int = 5

# Strategy registry — empty for Week 1 per the curriculum (PROJECT.md "Week 1").
# Variants get added here in Week 2 after the strategy-roster review.
STRATEGY_VARIANTS: dict[str, StrategyVariant] = {}
