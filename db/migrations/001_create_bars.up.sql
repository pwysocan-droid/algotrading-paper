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
