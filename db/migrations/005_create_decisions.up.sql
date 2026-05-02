CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES signals(id),
    decided_at TEXT NOT NULL,
    action TEXT NOT NULL,
    trade_id INTEGER REFERENCES trades(id),
    reason TEXT NOT NULL
);
