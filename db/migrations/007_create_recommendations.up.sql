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
    promoted_by_decision_log_entry TEXT
);
