"""Tests for claude_client.py.

Two groups:
  - System-prompt composition (base distillation discipline + layered
    role-specific text) — pure unit tests against a fake Anthropic client,
    no network, no API key required.
  - Integration smoke test against the live API — skipped if
    ANTHROPIC_API_KEY is not set, so the rest of the suite stays green on
    machines without API access.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

import db


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeToolUseBlock:
    def __init__(self, name: str, input_: dict[str, Any]) -> None:
        self.type = "tool_use"
        self.name = name
        self.input = input_


class _FakeUsage:
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeMessage:
    def __init__(self, content: list[Any], stop_reason: str = "end_turn") -> None:
        self.content = content
        self.usage = _FakeUsage(10, 5)
        self.stop_reason = stop_reason


class _FakeMessagesEndpoint:
    def __init__(self, response: _FakeMessage) -> None:
        self._response = response
        self.last_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> _FakeMessage:
        self.last_kwargs = kwargs
        return self._response


class _FakeAnthropicClient:
    def __init__(self, response: _FakeMessage) -> None:
        self.messages = _FakeMessagesEndpoint(response)


def _client_with_fake(tmp_db: Path, response: _FakeMessage):
    from claude_client import ClaudeClient

    client = ClaudeClient(api_key="sk-ant-test-fake-key", db_path=tmp_db)
    fake = _FakeAnthropicClient(response)
    client._client = fake  # bypass the real SDK entirely — no network call
    return client, fake


def test_build_system_with_no_caller_system_returns_base() -> None:
    from claude_client import BASE_SYSTEM_PROMPT, _build_system

    assert _build_system(None) == BASE_SYSTEM_PROMPT


def test_build_system_layers_caller_system_after_base() -> None:
    from claude_client import BASE_SYSTEM_PROMPT, _build_system

    result = _build_system("Skeptic prompt: bear case only.")
    assert result.startswith(BASE_SYSTEM_PROMPT)
    assert result.endswith("Skeptic prompt: bear case only.")
    assert BASE_SYSTEM_PROMPT in result


def test_complete_always_sends_base_system_prompt(tmp_db: Path) -> None:
    from claude_client import BASE_SYSTEM_PROMPT

    response = _FakeMessage(content=[_FakeTextBlock("ok")])
    client, fake = _client_with_fake(tmp_db, response)

    client.complete(prompt="hi", called_from="test")

    assert fake.messages.last_kwargs["system"] == BASE_SYSTEM_PROMPT


def test_complete_layers_role_specific_system_on_base(tmp_db: Path) -> None:
    from claude_client import BASE_SYSTEM_PROMPT

    response = _FakeMessage(content=[_FakeTextBlock("ok")])
    client, fake = _client_with_fake(tmp_db, response)

    client.complete(prompt="hi", called_from="test", system="Skeptic prompt.")

    sent_system = fake.messages.last_kwargs["system"]
    assert sent_system.startswith(BASE_SYSTEM_PROMPT)
    assert "Skeptic prompt." in sent_system


def test_complete_structured_always_sends_base_system_prompt(tmp_db: Path) -> None:
    from pydantic import BaseModel

    from claude_client import BASE_SYSTEM_PROMPT

    class Trivial(BaseModel):
        ok: bool

    response = _FakeMessage(
        content=[_FakeToolUseBlock("submit_response", {"ok": True})]
    )
    client, fake = _client_with_fake(tmp_db, response)

    client.complete_structured(prompt="hi", schema_cls=Trivial, called_from="test")

    assert fake.messages.last_kwargs["system"] == BASE_SYSTEM_PROMPT


def test_complete_structured_layers_role_specific_system_on_base(tmp_db: Path) -> None:
    from pydantic import BaseModel

    from claude_client import BASE_SYSTEM_PROMPT

    class Trivial(BaseModel):
        ok: bool

    response = _FakeMessage(
        content=[_FakeToolUseBlock("submit_response", {"ok": True})]
    )
    client, fake = _client_with_fake(tmp_db, response)

    client.complete_structured(
        prompt="hi", schema_cls=Trivial, called_from="test", system="Extractor prompt."
    )

    sent_system = fake.messages.last_kwargs["system"]
    assert sent_system.startswith(BASE_SYSTEM_PROMPT)
    assert "Extractor prompt." in sent_system


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live API integration test",
)
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


def test_structured_retries_on_malformed_then_succeeds(monkeypatch, tmp_path):
    """Round-005 failure class (2026-07-19): a malformed tool input on
    attempt 1 must trigger a retry, not a 12h pipeline stall."""
    from pydantic import BaseModel
    import claude_client as cc

    class Shape(BaseModel):
        ideas: list[str]
        thesis: str

    class _Block:
        type = "tool_use"
        name = "submit_response"
        def __init__(self, inp): self.input = inp

    class _Msg:
        stop_reason = "tool_use"
        usage = None
        def __init__(self, inp): self.content = [_Block(inp)]

    calls = {"n": 0}

    class _Messages:
        def create(self, **kw):
            calls["n"] += 1
            if calls["n"] == 1:
                return _Msg({"thesis": "everything crammed here, no ideas"})
            return _Msg({"ideas": ["a", "b"], "thesis": "ok"})

    class _Fake:
        messages = _Messages()

    client = cc.ClaudeClient(api_key="test", db_path=tmp_path / "x.db")
    client._client = _Fake()
    result = client.complete_structured(
        prompt="p", schema_cls=Shape, called_from="test", log=False)
    assert calls["n"] == 2
    assert result.parsed.ideas == ["a", "b"]


def test_structured_raises_after_exhausted_retries(monkeypatch, tmp_path):
    from pydantic import BaseModel
    import claude_client as cc
    import pytest as _pytest

    class Shape(BaseModel):
        ideas: list[str]

    class _Block:
        type = "tool_use"
        name = "submit_response"
        input = {"wrong": True}

    class _Msg:
        stop_reason = "tool_use"
        usage = None
        content = [_Block()]

    class _Messages:
        def create(self, **kw): return _Msg()

    class _Fake:
        messages = _Messages()

    client = cc.ClaudeClient(api_key="test", db_path=tmp_path / "x.db")
    client._client = _Fake()
    with _pytest.raises(RuntimeError, match="after 3 attempts"):
        client.complete_structured(
            prompt="p", schema_cls=Shape, called_from="test", log=False)
