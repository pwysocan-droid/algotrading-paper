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


# --- Idea foundry ------------------------------------------------------------


def test_foundry_prompt_embeds_registry_and_lenses(tmp_path, monkeypatch):
    from scripts import idea_foundry as f

    registry = {
        "failure_lessons": ["FEE FLOOR: lesson text"],
        "ideas": [
            {"name": "old_idea", "lineage": "retail X", "verdict": "dead",
             "epitaph": "it died because Y"},
        ],
    }
    prompt = f.build_prompt(registry, f.LENSES)
    assert "FEE FLOOR: lesson text" in prompt
    assert "old_idea" in prompt and "it died because Y" in prompt
    for key, _ in f.LENSES:
        assert key in prompt
    assert "kill_criterion" in prompt


def test_foundry_lens_rotation_covers_all_lenses(monkeypatch):
    """5-of-8 per round (all 8 at once truncated the synthesis call);
    the rotation must cycle every lens through consecutive rounds."""
    from scripts import idea_foundry as f

    per_round = [f.lenses_for_round(n) for n in range(1, 9)]
    assert all(len(l) == f.ROUND_LENS_COUNT for l in per_round)
    seen = {key for l in per_round[:2] for key, _ in l}
    assert seen == {key for key, _ in f.LENSES}, (
        "two consecutive rounds must already cover all lenses"
    )
    # default build_prompt (no lens arg) stays inside the round budget
    reg = {"failure_lessons": ["x"], "ideas": []}
    assert f"exactly {f.ROUND_LENS_COUNT} strategy" in f.build_prompt(reg)


def test_foundry_round_numbering(tmp_path, monkeypatch):
    from scripts import idea_foundry as f

    monkeypatch.setattr(f, "FOUNDRY_DIR", tmp_path)
    assert f._next_round_number() == 1
    (tmp_path / "round-001.json").write_text("{}")
    (tmp_path / "round-002.json").write_text("{}")
    assert f._next_round_number() == 3


def test_foundry_round_writes_artifacts(tmp_path, monkeypatch):
    from scripts import idea_foundry as f
    from scripts.idea_foundry import FoundryIdea, FoundryRound

    monkeypatch.setattr(f, "FOUNDRY_DIR", tmp_path)
    monkeypatch.setattr(f, "REGISTRY_PATH", tmp_path / "dead-ideas.json")
    (tmp_path / "dead-ideas.json").write_text(json.dumps({
        "failure_lessons": ["lesson"], "ideas": [],
    }))

    round_obj = FoundryRound(
        round_thesis="Explore the unexplored.",
        ideas=[
            FoundryIdea(
                name=f"idea_{k}", lens=lens_key,
                mechanism="m", lineage_check="not a descendant of anything",
                entry_rule="do x", params={"p": 1},
                expected_fire_rate="0.1/day", fee_survival="moves >1%",
                kill_criterion="edge/slot < 0",
            )
            for k, (lens_key, _) in enumerate(f.lenses_for_round(1))
        ],
    )

    class _R:
        parsed = round_obj
        model = "claude-test"

    class _C:
        def complete_structured(self, **kw):
            assert kw["called_from"] == "idea_foundry"
            return _R()

    out = f.run_round(client=_C(), now=datetime(2026, 7, 17, tzinfo=timezone.utc))
    assert out.name == "round-001.md"
    assert (tmp_path / "round-001.json").exists()
    md = out.read_text()
    assert "Explore the unexplored." in md
    assert "idea_0" in md and "Kill criterion" in md


def test_pipeline_health_flags_stall_and_alert(tmp_path):
    from datetime import datetime, timezone
    from scripts.generate_rounds import pipeline_health

    now = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
    foundry = tmp_path / "reviews" / "foundry"
    foundry.mkdir(parents=True)
    logs = tmp_path / "vps" / "logs"
    logs.mkdir(parents=True)

    # fresh round, clean logs -> healthy
    rnd = foundry / "round-001.json"
    rnd.write_text("{}")

    def _h():  # disk usage is the host's, not the fixture's — ignore it
        return [w for w in pipeline_health(tmp_path, now=now) if "DISK" not in w]
    assert _h() == []

    # ALERT in today's foundry log -> flagged
    (logs / "foundry-2026-07-17.log").write_text("ALERT: autopilot FAILED")
    assert any("ALERT" in w for w in _h())

    # stale round (>3 days) -> flagged
    import os
    old = now.timestamp() - 4 * 86400
    os.utime(rnd, (old, old))
    assert any("STALLED" in w for w in _h())


def test_foundry_rejects_bad_rounds(monkeypatch, tmp_path):
    """Semantic guards: wrong count, duplicate names, collisions with the
    registry or existing variants must raise at generation time."""
    import json as _json
    from scripts import idea_foundry as f

    idea = {
        "name": "fresh_idea", "lens": "x", "mechanism": "m",
        "lineage_check": "lc", "entry_rule": "er", "params": {},
        "expected_fire_rate": "e", "fee_survival": "fs", "kill_criterion": "k",
    }

    class FakeResult:
        model = "fake"

        def __init__(self, ideas):
            self.parsed = f.FoundryRound(
                ideas=[f.FoundryIdea(**i) for i in ideas], round_thesis="t")

    class FakeClient:
        def __init__(self, ideas):
            self._ideas = ideas

        def complete_structured(self, **kwargs):
            return FakeResult(self._ideas)

    monkeypatch.setattr(f, "FOUNDRY_DIR", tmp_path)
    reg = tmp_path / "dead-ideas.json"
    reg.write_text(_json.dumps({"failure_lessons": [], "ideas": [
        {"name": "dead_old", "lineage": "x", "verdict": "dead"}]}))
    monkeypatch.setattr(f, "REGISTRY_PATH", reg)

    import pytest as _pytest
    with _pytest.raises(RuntimeError, match="expected 5 ideas"):
        f.run_round(client=FakeClient([idea]))

    five_dupes = [dict(idea, name="same")] * 5
    with _pytest.raises(RuntimeError, match="duplicate"):
        f.run_round(client=FakeClient(five_dupes))

    five = [dict(idea, name=f"n{i}") for i in range(4)] + [dict(idea, name="dead_old")]
    with _pytest.raises(RuntimeError, match="collide"):
        f.run_round(client=FakeClient(five))


def test_pipeline_health_forgives_recovered_alerts(tmp_path):
    """An ALERT followed by a later successful run is recovered — the
    digest must stop alarming (2026-07-18: first digest alarmed on a
    crash fixed 12 hours earlier)."""
    from datetime import datetime, timezone
    from scripts.generate_rounds import pipeline_health

    now = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
    (tmp_path / "reviews" / "foundry").mkdir(parents=True)
    (tmp_path / "reviews" / "foundry" / "round-001.json").write_text("{}")
    logs = tmp_path / "vps" / "logs"
    logs.mkdir(parents=True)

    # failed run, then a clean one -> recovered, no warning
    (logs / "foundry-2026-07-18.log").write_text(
        "=== autopilot 2026-07-18T04:02:00Z ===\n"
        "ALERT: foundry_autopilot FAILED\n"
        "=== done 2026-07-18T04:02:10Z ===\n"
        "=== autopilot 2026-07-18T16:02:00Z ===\n"
        "condition B: generating\n"
        "=== done 2026-07-18T16:04:00Z ===\n"
    )
    assert [w for w in pipeline_health(tmp_path, now=now) if "DISK" not in w] == []

    # failure in the MOST RECENT run -> alarm
    (logs / "foundry-2026-07-18.log").write_text(
        "=== autopilot 2026-07-18T04:02:00Z ===\n"
        "ok\n"
        "=== done 2026-07-18T04:02:10Z ===\n"
        "=== autopilot 2026-07-18T16:02:00Z ===\n"
        "ALERT: foundry_autopilot FAILED\n"
        "=== done 2026-07-18T16:04:00Z ===\n"
    )
    assert any("FOUNDRY ALERT" in w for w in pipeline_health(tmp_path, now=now))
