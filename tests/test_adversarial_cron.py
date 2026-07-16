"""Tests for adversarial_cron.py — fake client, no network, no API key."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

import adversarial_cron
import db
from render_index import read_yaml_md_records


@dataclass
class _FakeResult:
    text: str
    model: str = "claude-test"


class _FakeClient:
    def __init__(self, text: str = "The project is stalling.\n\nTOMORROW: register a strategy.") -> None:
        self._text = text
        self.last_prompt: str | None = None
        self.last_system: str | None = None
        self.last_called_from: str | None = None

    def complete(self, prompt: str, called_from: str, *, system: str | None = None) -> _FakeResult:
        self.last_prompt = prompt
        self.last_system = system
        self.last_called_from = called_from
        return _FakeResult(text=self._text)


PENDING_TEMPLATE = """# Pending

Docs prose up here explaining the format.

---

- thing: Week 2 strategy-roster review
  detail: resolved or not
  when: 10d
  kind: gate
  promoted: true

- thing: Some open ops item
  when: open
  kind: ops
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "pending.md").write_text(PENDING_TEMPLATE)
    return tmp_path


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    with db.connect(path) as conn:
        for i in range(9):
            conn.execute(
                "INSERT INTO runs (started_at, finished_at, status, bars_added, kind) "
                "VALUES (?, ?, 'ok', ?, 'cron')",
                (f"2026-07-0{i % 9 + 1}T00:00:00+00:00", f"2026-07-0{i % 9 + 1}T00:00:01+00:00", 85),
            )
    return path


def test_read_recent_runs_returns_newest_first_capped(tmp_db: Path) -> None:
    with db.connect(tmp_db) as conn:
        runs = adversarial_cron.read_recent_runs(conn)
    assert len(runs) == 7
    assert runs[0]["id"] > runs[-1]["id"]


def test_build_prompt_includes_runs_and_pending() -> None:
    now = datetime(2026, 7, 3, tzinfo=timezone.utc)
    runs = [{"id": 1, "started_at": "t", "finished_at": "t", "status": "ok", "bars_added": 5, "kind": "cron"}]
    pending = [{"thing": "Open item", "detail": "d", "when": "open", "kind": "ops"}]
    prompt = adversarial_cron.build_prompt(runs, pending, now)
    assert "run 1" in prompt
    assert "Open item" in prompt
    assert "2026-07-03" in prompt


def test_run_nightly_writes_review_and_pending_item(repo: Path, tmp_db: Path) -> None:
    fake = _FakeClient()
    now = datetime(2026, 7, 3, 3, 32, tzinfo=timezone.utc)

    out = adversarial_cron.run_nightly(client=fake, db_path=tmp_db, repo_root=repo, now=now)

    assert out == repo / "reviews" / "nightly" / "2026-07-03.md"
    content = out.read_text()
    assert "The project is stalling." in content
    assert "TOMORROW: register a strategy." in content

    assert fake.last_called_from == "adversarial_cron"
    assert fake.last_system == adversarial_cron.SKEPTIC_SYSTEM
    assert "Open pending items" in fake.last_prompt

    records = read_yaml_md_records(repo / "pending.md")
    nightly = [r for r in records if str(r["thing"]).startswith("Nightly skeptic")]
    assert len(nightly) == 1
    assert nightly[0]["thing"] == "Nightly skeptic · 2026-07-03"
    assert nightly[0]["kind"] == "ops"
    assert "stalling" in nightly[0]["detail"]
    # original items untouched
    assert any(r["thing"] == "Week 2 strategy-roster review" for r in records)


def test_run_nightly_replaces_prior_item_not_accumulates(repo: Path, tmp_db: Path) -> None:
    fake = _FakeClient()
    day1 = datetime(2026, 7, 3, tzinfo=timezone.utc)
    day2 = datetime(2026, 7, 4, tzinfo=timezone.utc)

    adversarial_cron.run_nightly(client=fake, db_path=tmp_db, repo_root=repo, now=day1)
    adversarial_cron.run_nightly(client=fake, db_path=tmp_db, repo_root=repo, now=day2)

    records = read_yaml_md_records(repo / "pending.md")
    nightly = [r for r in records if str(r["thing"]).startswith("Nightly skeptic")]
    assert len(nightly) == 1
    assert nightly[0]["thing"] == "Nightly skeptic · 2026-07-04"
    # both review files exist — only the pending pointer is replaced
    assert (repo / "reviews" / "nightly" / "2026-07-03.md").exists()
    assert (repo / "reviews" / "nightly" / "2026-07-04.md").exists()


def test_prior_nightly_item_not_fed_back_to_skeptic(repo: Path, tmp_db: Path) -> None:
    fake = _FakeClient()
    day1 = datetime(2026, 7, 3, tzinfo=timezone.utc)
    day2 = datetime(2026, 7, 4, tzinfo=timezone.utc)

    adversarial_cron.run_nightly(client=fake, db_path=tmp_db, repo_root=repo, now=day1)
    adversarial_cron.run_nightly(client=fake, db_path=tmp_db, repo_root=repo, now=day2)

    # day2's prompt must not contain day1's pending item (the header line
    # "Nightly skeptic run, ..." is the prompt's own title, so check for
    # the item form specifically)
    assert "Nightly skeptic · 2026-07-03" not in fake.last_prompt


def test_pending_still_parses_after_many_runs(repo: Path, tmp_db: Path) -> None:
    fake = _FakeClient(text='Line with "double quotes" and: colons, dashes - etc.')
    for day in range(3, 8):
        now = datetime(2026, 7, day, tzinfo=timezone.utc)
        adversarial_cron.run_nightly(client=fake, db_path=tmp_db, repo_root=repo, now=now)
    records = read_yaml_md_records(repo / "pending.md")
    assert len(records) == 3  # 2 originals + 1 nightly
    assert sum(1 for r in records if str(r["thing"]).startswith("Nightly skeptic")) == 1


def test_long_first_line_truncated(repo: Path, tmp_db: Path) -> None:
    fake = _FakeClient(text="x" * 300)
    now = datetime(2026, 7, 3, tzinfo=timezone.utc)
    adversarial_cron.run_nightly(client=fake, db_path=tmp_db, repo_root=repo, now=now)
    records = read_yaml_md_records(repo / "pending.md")
    nightly = [r for r in records if str(r["thing"]).startswith("Nightly skeptic")][0]
    assert len(nightly["detail"]) == 100
    assert nightly["detail"].endswith("...")
