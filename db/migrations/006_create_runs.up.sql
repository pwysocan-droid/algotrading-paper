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
