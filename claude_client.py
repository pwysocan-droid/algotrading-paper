"""Claude API client with two modes and a complete audit log.

The 2026-04-26 reframe entry moved LLM integration from Week 7 to Week 1
in three roles: feature extractor (Week 5+), weekly adversarial reviewer
(Week 1+), decision-log pattern surfacer (Month 2+). This client is the
substrate for all three.

Two modes:
  - complete(prompt, called_from)   → free-text response (used by the
                                      Friday adversarial review)
  - complete_structured(prompt, schema_cls, called_from)
                                    → Pydantic instance, enforced by
                                      tool-use (used by Week 5+ feature
                                      extraction; available now but not
                                      called yet)

Every call writes a row to the llm_calls table with the prompt (full +
hash), response, model, latency, token counts, and a free-text
called_from tag. Cost and performance are auditable from day one.

Every call also carries BASE_SYSTEM_PROMPT (the distillation discipline,
philosophy.md / decision-log.md 2026-07-02) as its base system prompt —
not optional per-call. Role-specific instructions (e.g. the Friday
adversarial reviewer's skeptic prompt) are passed via `system` and
layered on top of the base, never in place of it.

The default model is read from CLAUDE_MODEL env var (override) or falls
back to the current production Sonnet ID per the Anthropic docs at the
time of build. Do not hardcode the model in calling code — let
.env / DEFAULT_MODEL drive it so model upgrades are a config change.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Type, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel

import db

load_dotenv()


# Model routing per LLM role — decision-log 2026-07-16 (build queue: "Model
# routing per LLM role"). The nightly skeptic runs 365x/yr on a small prompt
# where Haiku is plenty; the weekly review and candidate synthesis are where
# depth pays, so they get the frontier default. IDs verified against the
# platform model catalog on 2026-07-16 (Haiku 4.5 $1/$5 per MTok, Opus 4.8
# $5/$25 per MTok).
#
# Resolution order per role: CLAUDE_MODEL_<ROLE> env > CLAUDE_MODEL env >
# the per-role default below. CLAUDE_MODEL alone (the pre-existing override)
# still pins every role to one model, preserving old behavior for anyone
# relying on it.
ROLE_MODEL_DEFAULTS = {
    "nightly": "claude-haiku-4-5",
    "review": "claude-opus-4-8",
    "synthesis": "claude-opus-4-8",
}
DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")
DEFAULT_MAX_TOKENS = 4096


def model_for_role(role: str) -> str:
    """Resolve the model for a named LLM role (see ROLE_MODEL_DEFAULTS)."""
    env_override = os.environ.get(f"CLAUDE_MODEL_{role.upper()}")
    if env_override:
        return env_override
    global_override = os.environ.get("CLAUDE_MODEL")
    if global_override:
        return global_override
    return ROLE_MODEL_DEFAULTS.get(role, DEFAULT_MODEL)


T = TypeVar("T", bound=BaseModel)


# The distillation discipline — philosophy.md "The animating disciplines" /
# decision-log.md 2026-07-02. Every call through this client carries this
# as the base system prompt; it is not optional per-call. Callers that need
# role-specific instructions (e.g. the Friday adversarial reviewer's
# skeptic prompt) pass them via `system` — those are layered on top of this,
# never a replacement for it.
BASE_SYSTEM_PROMPT = """\
Compression is the contribution, not the caveats.

- Lead with the action. First line says what to do.
- One recommendation, not seven considerations.
- Cut meta-commentary. No narrating the process.
- Don't hedge or pile on caveats — say the thing plainly.
- Default to actionable; trust the reader to ask for more depth if they want it.\
"""


def _build_system(system: str | None) -> str:
    """Compose the base distillation-discipline prompt with any caller-
    supplied, role-specific system text layered after it."""
    if not system:
        return BASE_SYSTEM_PROMPT
    return f"{BASE_SYSTEM_PROMPT}\n\n{system}"


@dataclass
class CompletionResult:
    text: str
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    latency_ms: int


@dataclass
class StructuredResult[T: BaseModel]:
    parsed: T
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    latency_ms: int


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _log_call(
    prompt: str,
    response_text: str,
    model: str,
    latency_ms: int,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
    called_from: str,
    db_path: Path | None = None,
) -> int:
    with db.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO llm_calls (
                timestamp, prompt_hash, prompt_full, response_full, model,
                latency_ms, prompt_tokens, completion_tokens, total_tokens, called_from
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                _hash_prompt(prompt),
                prompt,
                response_text,
                model,
                latency_ms,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                called_from,
            ),
        )
        return int(cur.lastrowid) if cur.lastrowid else 0


class ClaudeClient:
    """Thin wrapper around the Anthropic Messages API with audit logging."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        db_path: Path | None = None,
    ) -> None:
        from anthropic import Anthropic

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY must be set in .env or passed explicitly"
            )
        self._client = Anthropic(api_key=key)
        self._model = model
        self._db_path = db_path

    @property
    def model(self) -> str:
        return self._model

    def complete(
        self,
        prompt: str,
        called_from: str,
        *,
        system: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        log: bool = True,
    ) -> CompletionResult:
        start = time.perf_counter()
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "system": _build_system(system),
            "messages": [{"role": "user", "content": prompt}],
        }
        msg = self._client.messages.create(**kwargs)
        latency_ms = int((time.perf_counter() - start) * 1000)

        text_parts = [block.text for block in msg.content if block.type == "text"]
        text = "".join(text_parts)

        usage = getattr(msg, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", None) if usage else None
        completion_tokens = getattr(usage, "output_tokens", None) if usage else None
        total_tokens = (
            (prompt_tokens or 0) + (completion_tokens or 0)
            if prompt_tokens is not None and completion_tokens is not None
            else None
        )

        if log:
            _log_call(
                prompt=prompt,
                response_text=text,
                model=self._model,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                called_from=called_from,
                db_path=self._db_path,
            )

        return CompletionResult(
            text=text,
            model=self._model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )

    def complete_structured(
        self,
        prompt: str,
        schema_cls: Type[T],
        called_from: str,
        *,
        system: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        tool_name: str = "submit_response",
        tool_description: str | None = None,
        log: bool = True,
    ) -> StructuredResult[T]:
        """Force the response into a Pydantic schema via Anthropic tool-use.

        The schema's JSON Schema is wired as the tool's `input_schema`, and
        `tool_choice` is pinned to that tool — so the model must return a
        tool_use block whose `input` validates against the schema. Used in
        Week 5+ for sentiment / event extraction; available now but not
        called yet.
        """
        json_schema = schema_cls.model_json_schema()
        description = (
            tool_description
            or f"Submit a structured response matching the {schema_cls.__name__} schema."
        )

        start = time.perf_counter()
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "tools": [
                {
                    "name": tool_name,
                    "description": description,
                    "input_schema": json_schema,
                }
            ],
            "tool_choice": {"type": "tool", "name": tool_name},
            "system": _build_system(system),
            "messages": [{"role": "user", "content": prompt}],
        }
        msg = self._client.messages.create(**kwargs)
        latency_ms = int((time.perf_counter() - start) * 1000)

        tool_blocks = [b for b in msg.content if b.type == "tool_use" and b.name == tool_name]
        if not tool_blocks:
            raise RuntimeError(
                f"expected a tool_use block named {tool_name!r}, got none. "
                f"stop_reason={getattr(msg, 'stop_reason', '?')}"
            )
        tool_input = tool_blocks[0].input

        usage = getattr(msg, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", None) if usage else None
        completion_tokens = getattr(usage, "output_tokens", None) if usage else None
        total_tokens = (
            (prompt_tokens or 0) + (completion_tokens or 0)
            if prompt_tokens is not None and completion_tokens is not None
            else None
        )

        if log:
            _log_call(
                prompt=prompt,
                response_text=json.dumps(tool_input, default=str),
                model=self._model,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                called_from=called_from,
                db_path=self._db_path,
            )

        parsed = schema_cls.model_validate(tool_input)
        return StructuredResult(
            parsed=parsed,
            model=self._model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="One-shot Claude smoke test")
    parser.add_argument("--prompt", default="Say only the word 'pong' and nothing else.")
    parser.add_argument("--called-from", default="cli_smoke")
    args = parser.parse_args()

    db.migrate()
    client = ClaudeClient()
    result = client.complete(args.prompt, called_from=args.called_from)
    print(f"model={result.model} latency_ms={result.latency_ms}")
    print(f"prompt_tokens={result.prompt_tokens} completion_tokens={result.completion_tokens}")
    print("---")
    print(result.text)
