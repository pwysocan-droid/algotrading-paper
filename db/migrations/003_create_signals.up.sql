CREATE TABLE signals (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    variant_name TEXT NOT NULL,
    strategy TEXT NOT NULL,
    side TEXT NOT NULL,
    bar_timestamp TEXT NOT NULL,
    price_at_signal REAL NOT NULL,
    reasoning_json TEXT NOT NULL,
    context_used_json TEXT,
    emitted_at TEXT NOT NULL,
    UNIQUE (symbol, variant_name, bar_timestamp, side)
);
