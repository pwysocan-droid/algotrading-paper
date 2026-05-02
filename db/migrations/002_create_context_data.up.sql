CREATE TABLE context_data (
    source TEXT NOT NULL,
    key TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    value_numeric REAL,
    value_text TEXT,
    metadata_json TEXT,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (source, key, timestamp)
);
CREATE INDEX context_lookup ON context_data (source, key, timestamp DESC);
