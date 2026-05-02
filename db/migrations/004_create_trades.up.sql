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
    is_real_money INTEGER NOT NULL DEFAULT 0,
    alpaca_order_id TEXT,
    status TEXT NOT NULL
);
