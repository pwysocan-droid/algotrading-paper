"""Tests for scripts/generate_learnings.py — fake client, no network."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts import generate_learnings as gl
from scripts.generate_learnings import Hypothesis, LedgerExtraction, Learning


class _FakeStructuredResult:
    def __init__(self, parsed: LedgerExtraction) -> None:
        self.parsed = parsed
        self.model = "claude-test"


class _FakeClient:
    def __init__(self, extraction: LedgerExtraction) -> None:
        self._extraction = extraction
        self.calls = 0
        self.last_system: str | None = None

    def complete_structured(self, prompt, schema_cls, called_from, *,
                            system=None, max_tokens=None):
        self.calls += 1
        self.last_system = system
        assert schema_cls is LedgerExtraction
        assert called_from == "learnings_ledger"
        return _FakeStructuredResult(self._extraction)


@pytest.fixture
def sandbox(tmp_path: Path, monkeypatch):
    """Point the module's paths at a temp repo."""
    (tmp_path / "surface").mkdir()
    (tmp_path / "decision-log.md").write_text("## 2026-07-02 — entry\n\nSome decision.\n")
    monkeypatch.setattr(gl, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gl, "LEDGER_PATH", tmp_path / "surface" / "learnings.json")
    return tmp_path


EXTRACTION = LedgerExtraction(
    learnings=[
        Learning(claim="Constraints dominate strategy.", status="validated",
                 evidence="2026-07-02 roster entry", next_check=None),
        Learning(claim="VPS uptime holds at 100%.", status="pending",
                 evidence="2026-07-02 gap entry", next_check="2026-07-01"),
    ],
    hypotheses=[
        Hypothesis(commitment="Roster decision by end of Week 2.",
                   source_entry="2026-04-26 reframe", due="2026-05-31",
                   status="resolved-against",
                   resolution="Resolved 2026-07-02: both strategies retired."),
    ],
)


def test_generates_ledger_with_all_layers(sandbox: Path) -> None:
    fake = _FakeClient(EXTRACTION)
    now = datetime(2026, 7, 16, tzinfo=timezone.utc)

    written = gl.generate(client=fake, now=now)

    assert written is True
    ledger = json.loads((sandbox / "surface" / "learnings.json").read_text())
    assert len(ledger["questions"]) == 5
    assert {q["id"] for q in ledger["questions"]} == {
        "fees-slippage", "parameter-robustness", "constraint-dominance",
        "sentiment-value", "tuner-out-of-sample",
    }
    assert len(ledger["learnings"]) == 2
    assert ledger["hypotheses"][0]["status"] == "resolved-against"
    assert ledger["decision_log_sha256"]


def test_overdue_pending_checks_flagged(sandbox: Path) -> None:
    fake = _FakeClient(EXTRACTION)
    now = datetime(2026, 7, 16, tzinfo=timezone.utc)

    gl.generate(client=fake, now=now)

    ledger = json.loads((sandbox / "surface" / "learnings.json").read_text())
    # the pending learning with next_check 2026-07-01 < today is overdue;
    # the validated one is not
    assert len(ledger["overdue"]) == 1
    assert ledger["overdue"][0]["claim"] == "VPS uptime holds at 100%."


def test_hash_gate_skips_unchanged_log(sandbox: Path) -> None:
    fake = _FakeClient(EXTRACTION)
    now = datetime(2026, 7, 16, tzinfo=timezone.utc)

    assert gl.generate(client=fake, now=now) is True
    assert gl.generate(client=fake, now=now) is False, "unchanged log must skip the LLM"
    assert fake.calls == 1


def test_changed_log_reextracts(sandbox: Path) -> None:
    fake = _FakeClient(EXTRACTION)
    now = datetime(2026, 7, 16, tzinfo=timezone.utc)

    gl.generate(client=fake, now=now)
    (sandbox / "decision-log.md").write_text("## new entry\n")
    assert gl.generate(client=fake, now=now) is True
    assert fake.calls == 2


def test_force_bypasses_hash_gate(sandbox: Path) -> None:
    fake = _FakeClient(EXTRACTION)
    now = datetime(2026, 7, 16, tzinfo=timezone.utc)

    gl.generate(client=fake, now=now)
    assert gl.generate(client=fake, force=True, now=now) is True
    assert fake.calls == 2


def test_corrupt_existing_ledger_regenerates(sandbox: Path) -> None:
    (sandbox / "surface" / "learnings.json").write_text("not json")
    fake = _FakeClient(EXTRACTION)
    assert gl.generate(client=fake, now=datetime(2026, 7, 16, tzinfo=timezone.utc)) is True
