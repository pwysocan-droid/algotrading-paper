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

# Maker/limit fill model (the cost lever — decision-log 2026-07-17 "The
# levers are the strategy"). Alpaca crypto base fee tier is 0.15% maker /
# 0.25% taker. A maker fill pays no slippage (it IS the resting liquidity)
# but carries fill risk: replay models entries as a limit at the signal
# bar's close that must be traded THROUGH (strictly) within the timeout
# window or the signal expires unfilled. Backtest-only until validated;
# live execution still sends market orders.
MAKER_FEE_PCT: float = 0.0015
LIMIT_FILL_TIMEOUT_BARS: int = 12  # 1 hour of 5-min bars

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
    # The placebo arm — the ONLY live variant (phase1-review.md § 5 term 1,
    # first live loop; decision-log 2026-07-16). Never retired: every higher
    # rung of the adaptation ladder is measured against it.
    "null_baseline": {
        "strategy": "null",
        "params": {"p": 0.10, "tp": 0.05, "sl": 0.03},
        "context_keys": [],
        "enabled": True,
        "phase_qualified": False,
    },
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
    # ── LLM-surfaced candidates (reviews/candidates-2026-07-16.md) ──────
    # Registered disabled: the gauntlet (6-month constrained replay,
    # scored by edge per constraint slot) decides which top 2 go live.
    "liquidation_cascade_reclaim": {
        "strategy": "cascade_reclaim",
        "params": {"lookback_bars": 288, "sigma_mult": 4.0, "min_range_pct": 0.02,
                   "cascade_search_bars": 6, "vol_mult": 1.5},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "btc_leads_alt_lag_capture": {
        "strategy": "btc_lag",
        "params": {"window_bars": 36, "btc_lookback_bars": 3, "btc_impulse_pct": 0.012,
                   "lag_ratio": 0.5, "alt_vol_mult": 1.2,
                   "traded_symbols": ["SOL", "LINK", "AVAX"]},
        "context_keys": ["btc_bars"],
        "enabled": False,
        "phase_qualified": False,
    },
    "dead_zone_range_break": {
        "strategy": "deadzone_break",
        "params": {"window_bars": 288, "deadzone_start_utc": 0, "deadzone_end_utc": 6,
                   "max_coil_range": 0.015, "deadzone_vol_ratio": 0.6,
                   "break_buffer": 0.001, "vol_expansion_mult": 2.0,
                   "session_window_utc": [7, 12]},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    # Gauntlet top 2 (reports/gauntlet-2026-07-16.md) — LIVE as A/B arms
    # against null_baseline, NOT as winners: every candidate was net-
    # negative after fees in the 180d replay. Registration is the live
    # experiment the Phase 1b term committed to; promotion still requires
    # beating null at p<0.05 over 100+ trades (decision-log 2026-07-16).
    "volume_thrust_regime_shift": {
        "strategy": "vol_thrust",
        "params": {"window_bars": 288, "vol_zscore": 3.0, "thrust_body_pct": 0.008,
                   "thrust_search_bars": 3},
        "context_keys": [],
        "enabled": True,
        "phase_qualified": False,
    },
    "weekend_illiquidity_momentum": {
        "strategy": "weekend_momentum",
        "params": {"window_bars": 72, "mom_lookback_bars": 12, "mom_threshold": 0.015,
                   "signif_ratio": 2.0, "persistence_bars": 3},
        "context_keys": [],
        "enabled": True,
        "phase_qualified": False,
    },
    # ── Foundry round 001 (reviews/foundry/round-001.md) ────────────────
    # Disabled: awaiting the multi-year gauntlet. Kill criteria in the
    # round file; deaths get epitaphs in reviews/foundry/dead-ideas.json.
    "entropy_collapse_impulse": {
        "strategy": "entropy_impulse",
        "params": {"entropy_window": 24, "coil_percentile": 15, "coil_min_bars": 6,
                   "surprise_sigma": 2.5, "hist_window": 288, "n_bins": 5},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "omori_aftershock_ladder": {
        "strategy": "omori_aftershock",
        "params": {"mainshock_sigma": 4.0, "mainshock_vol_mult": 3.0, "std_window": 96,
                   "aftershock_window": 12, "retrace_skip_pct": 50,
                   "aftershock_vol_window": 24},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "failed_auction_rejection_wick": {
        "strategy": "auction_wick",
        "params": {"extreme_window": 48, "wick_body_mult": 2.0,
                   "wick_range_frac": 0.6, "vol_mult": 2.5},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "round_number_overshoot_snap": {
        "strategy": "round_number_snap",
        "params": {"overshoot_frac": 0.004, "vol_mult": 2.0, "vol_window": 48,
                   "fresh_level_window": 24},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "drawdown_regime_contrarian_gate": {
        "strategy": "regime_gate_breakout",
        "params": {"breakout_window": 24, "vol_mult": 1.5, "vol_window": 48,
                   "null_lookback": 288, "null_winrate_gate": 0.35,
                   "drawdown_cluster_max": 2},
        "context_keys": ["system_state"],
        "enabled": False,
        "phase_qualified": False,
    },
    # ── Foundry round 002 (reviews/foundry/round-002.md) ────────────────
    "conditional_entropy_regime_expansion": {
        "strategy": "cond_entropy_expansion",
        "params": {"entropy_jump": 0.35, "vol_mult": 2.2, "cond_order": 2,
                   "long_window": 60, "short_window": 12},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "epidemic_r0_crossover_ignition": {
        "strategy": "r0_ignition",
        "params": {"r0_thresh": 1.5, "decay_lambda": 0.85, "window": 6,
                   "consistency_bars": 5, "median_window": 60},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "absorption_shelf_breakout": {
        "strategy": "absorption_shelf",
        "params": {"shelf_len": 6, "vol_mult": 1.3, "body_frac": 0.4,
                   "span_frac": 1.2, "break_atr": 0.5, "atr_window": 14},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "options_expiry_pin_release": {
        "strategy": "expiry_pin_release",
        "params": {"pin_span_pct": 0.8, "break_frac_pct": 0.35, "vol_mult": 1.5,
                   "pre_window": 12, "post_window_min": 60, "friday_weight": True},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "rejection_streak_gated_ignition": {
        "strategy": "rejection_gated_ignition",
        "params": {"gate_rej": 0.6, "gate_stop": 0.5, "rej_window": 50,
                   "placebo_window": 10, "r0_thresh": 1.5, "consistency_bars": 5},
        "context_keys": ["system_state"],
        "enabled": False,
        "phase_qualified": False,
    },
    # ── Foundry round 003 (reviews/foundry/round-003.md) ────────────────
    "gap_fill_exhaustion_continuation": {
        "strategy": "gap_exhaustion",
        "params": {"gap_threshold": 0.004, "body_lookback": 50,
                   "volume_lookback": 50, "tp": 0.05, "sl": 0.03,
                   "time_exit_hours": 24},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "asian_to_london_handoff_thrust": {
        "strategy": "asian_london_handoff",
        "params": {"asian_start_utc": 0, "asian_end_utc": 6,
                   "london_window_start_utc": 7, "london_window_end_utc": 9,
                   "body_lookback": 50, "volume_lookback": 50,
                   "tp": 0.05, "sl": 0.03, "time_exit_hours": 24},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "slot_scarcity_conviction_gate": {
        "strategy": "slot_scarcity_gate",
        "params": {"trade_window": 10, "stop_rate_gate": 0.5,
                   "gap_threshold": 0.004, "body_lookback": 50,
                   "volume_lookback": 50, "tp": 0.05, "sl": 0.03,
                   "time_exit_hours": 24},
        "context_keys": ["system_state"],
        "enabled": False,
        "phase_qualified": False,
    },
    "post_shock_multiday_drift": {
        "strategy": "post_shock_drift",
        "params": {"shock_threshold": 0.03, "volume_mult": 3.0,
                   "volume_lookback": 100, "tp": 0.12, "sl": 0.05,
                   "time_exit_hours": 120},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "pullback_to_breakout_level_limit": {
        "strategy": "breakout_retest_limit",
        "params": {"level_lookback": 48, "breakout_margin": 0.005,
                   "volume_lookback": 50, "retest_window_bars": 24,
                   "tp": 0.05, "sl": 0.03, "time_exit_hours": 24},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    # ── Foundry round 004 (reviews/foundry/round-004.md) ────────────────
    "trend_persistence_regime_gated_engine": {
        "strategy": "trend_persistence_gated",
        "params": {"donchian_lookback": 24, "vol_window": 12,
                   "vol_baseline_window": 96, "vol_expansion_mult": 1.3,
                   "close_position_pct": 0.2, "null_winrate_thresh": 0.38,
                   "stopcluster_thresh": 0.5, "tp": 0.06, "sl": 0.03,
                   "time_exit_hours": 24},
        "context_keys": ["system_state"],
        "enabled": False,
        "phase_qualified": False,
    },
    "return_magnitude_compressibility_break": {
        "strategy": "magnitude_surprise_break",
        "params": {"mag_window": 48, "surprise_thresh": 3.0,
                   "prior_quiet_window": 24, "prior_quiet_max": 1.5,
                   "close_position_pct": 0.25, "tp": 0.07, "sl": 0.03,
                   "time_exit_hours": 36},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "hawkes_self_excitation_intensity_entry": {
        "strategy": "hawkes_intensity_entry",
        "params": {"event_mult": 1.5, "median_window": 96,
                   "kernel_decay": 0.3, "intensity_window": 12,
                   "intensity_thresh": 1.5, "cum_disp_max_pct": 1.0,
                   "tp": 0.06, "sl": 0.03, "time_exit_hours": 24},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "one_sided_range_expansion_thrust": {
        "strategy": "one_sided_expansion_thrust",
        "params": {"body_mult": 2.0, "vol_mult": 1.5, "median_window": 96,
                   "same_dir_wick_max": 0.15, "opp_wick_max": 0.4,
                   "extreme_lookback": 12, "tp": 0.06, "sl": 0.03,
                   "time_exit_hours": 24},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
    "round_number_breach_continuation": {
        "strategy": "round_number_breach",
        "params": {"proximity_pct": 0.3, "coil_bars_required": 6,
                   "coil_window": 12, "breach_pct": 0.4, "vol_mult": 1.3,
                   "close_position_pct": 0.25, "tp": 0.06, "sl": 0.03,
                   "time_exit_hours": 24},
        "context_keys": [],
        "enabled": False,
        "phase_qualified": False,
    },
}
