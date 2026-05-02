CREATE TABLE llm_calls (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    prompt_full TEXT NOT NULL,
    response_full TEXT NOT NULL,
    model TEXT NOT NULL,
    latency_ms INTEGER NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    called_from TEXT NOT NULL
);
CREATE INDEX llm_calls_timestamp ON llm_calls (timestamp DESC);
CREATE INDEX llm_calls_called_from ON llm_calls (called_from);
