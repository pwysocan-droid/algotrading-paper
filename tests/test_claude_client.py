"""Integration test for claude_client.py.

Calls the live Anthropic API with a trivial prompt and verifies:
  - the response shape is what we expect
  - the llm_calls table row was written with non-null fields

Skipped if ANTHROPIC_API_KEY is not set in the environment, so the rest
of the test suite stays green on machines without API access.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import db


pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live API integration test",
)


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


def test_complete_smoke(tmp_db: Path) -> None:
    from claude_client import ClaudeClient

    client = ClaudeClient(db_path=tmp_db)
    result = client.complete(
        prompt="Say only the word 'pong' and nothing else.",
        called_from="test_smoke",
        max_tokens=20,
    )
    assert result.text.strip().lower().startswith("pong")
    assert result.model.startswith("claude-")
    assert result.latency_ms > 0
    assert result.prompt_tokens is not None
    assert result.completion_tokens is not None
    assert result.total_tokens == result.prompt_tokens + result.completion_tokens

    with db.connect(tmp_db) as conn:
        row = conn.execute(
            "SELECT * FROM llm_calls ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row is not None
    assert row["called_from"] == "test_smoke"
    assert row["prompt_full"] == "Say only the word 'pong' and nothing else."
    assert row["response_full"]
    assert row["model"].startswith("claude-")
    assert row["latency_ms"] > 0
    assert row["prompt_tokens"] is not None
    assert row["completion_tokens"] is not None
    assert row["prompt_hash"]
    assert len(row["prompt_hash"]) == 64
