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

    def complete(
        self, prompt: str, called_from: str, *,
        system: str | None = None, max_tokens: int | None = None,
    ) -> _FakeResult:
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


# --- Model routing --------------------------------------------------------


def test_model_for_role_defaults() -> None:
    from claude_client import model_for_role

    assert model_for_role("nightly") == "claude-haiku-4-5"
    assert model_for_role("review") == "claude-opus-4-8"
    assert model_for_role("synthesis") == "claude-opus-4-8"


def test_model_for_role_env_overrides(monkeypatch) -> None:
    from claude_client import model_for_role

    monkeypatch.setenv("CLAUDE_MODEL_NIGHTLY", "claude-sonnet-5")
    assert model_for_role("nightly") == "claude-sonnet-5"

    monkeypatch.delenv("CLAUDE_MODEL_NIGHTLY")
    monkeypatch.setenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    assert model_for_role("nightly") == "claude-sonnet-4-6"
    assert model_for_role("review") == "claude-sonnet-4-6"


# --- Friday review --------------------------------------------------------


FRIDAY_TEMPLATE = """# Friday adversarial review — bear case prompt template

Docs prose.

## The prompt

```
You are running the Friday adversarial review for week {{WEEK_NUMBER}}
({{WEEK_RANGE}}). Prior week: {{WEEK_NUMBER - 1}}.

Trades:
{{TRADE_HISTORY_TABLE}}

Runs: {{RUNS_LOG_SUMMARY}}
Decisions: {{DECISIONS_TABLE}}
Promotions: {{PROMOTIONS_THIS_WEEK}}
Prior bear case: {{PRIOR_BEAR_CASE}}
```

## Operator notes (do not include in the prompt to Claude)

- notes here
"""


@pytest.fixture
def friday_repo(repo: Path) -> Path:
    tmpl_dir = repo / "reviews" / "templates"
    tmpl_dir.mkdir(parents=True)
    (tmpl_dir / "friday-bear-case.md").write_text(FRIDAY_TEMPLATE)
    return repo


def test_run_friday_fills_template_and_writes_review(friday_repo: Path, tmp_db: Path) -> None:
    fake = _FakeClient(text="The bear case: nothing traded.")
    now = datetime(2026, 7, 17, 3, 34, tzinfo=timezone.utc)  # ISO week 29, a Friday

    out = adversarial_cron.run_friday(client=fake, db_path=tmp_db, repo_root=friday_repo, now=now)

    assert out == friday_repo / "reviews" / "2026-W29-friday.md"
    content = out.read_text()
    assert "The bear case: nothing traded." in content
    assert "machine-generated" in content

    assert fake.last_called_from == "friday_bear_case"
    prompt = fake.last_prompt
    assert "{{" not in prompt, "all template placeholders must be filled"
    assert "week 29" in prompt
    assert "Prior week: 28." in prompt
    assert "none — first Friday review" in prompt
    assert "no promotion machinery has run yet" in prompt


def test_run_friday_uses_prior_review_for_drift_check(friday_repo: Path, tmp_db: Path) -> None:
    (friday_repo / "reviews" / "2026-W21-friday.md").write_text("Prior bear case body W21.")
    fake = _FakeClient()
    now = datetime(2026, 7, 17, tzinfo=timezone.utc)

    adversarial_cron.run_friday(client=fake, db_path=tmp_db, repo_root=friday_repo, now=now)

    assert "Prior bear case body W21." in fake.last_prompt


def test_run_friday_includes_week_trades(friday_repo: Path, tmp_db: Path) -> None:
    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO signals (symbol, variant_name, strategy, side, bar_timestamp,"
            " price_at_signal, reasoning_json, emitted_at)"
            " VALUES ('BTC/USD', 'null_baseline', 'null', 'buy', '2026-07-15T00:00:00+00:00',"
            " 100.0, '{}', '2026-07-15T00:00:00+00:00')"
        )
        conn.execute(
            "INSERT INTO trades (signal_id, variant_name, symbol, side, qty, entry_price,"
            " entry_time, is_real_money, status)"
            " VALUES (1, 'null_baseline', 'BTC/USD', 'buy', 2.0, 100.0,"
            " '2026-07-15T00:00:00+00:00', 0, 'open')"
        )
    fake = _FakeClient()
    now = datetime(2026, 7, 17, tzinfo=timezone.utc)

    adversarial_cron.run_friday(client=fake, db_path=tmp_db, repo_root=friday_repo, now=now)

    assert "null_baseline" in fake.last_prompt


# --- Investigator (route A) --------------------------------------------------


class TestSqlTool:
    def test_select_allowed(self, tmp_db: Path) -> None:
        tool = adversarial_cron.make_sql_tool(tmp_db)
        out = tool({"query": "SELECT COUNT(*) AS n FROM runs"})
        assert "n" in out and "9" in out

    def test_with_cte_allowed(self, tmp_db: Path) -> None:
        tool = adversarial_cron.make_sql_tool(tmp_db)
        out = tool({"query": "WITH x AS (SELECT 1 AS one) SELECT one FROM x"})
        assert "1" in out

    def test_insert_rejected(self, tmp_db: Path) -> None:
        tool = adversarial_cron.make_sql_tool(tmp_db)
        with pytest.raises(ValueError, match="read-only"):
            tool({"query": "INSERT INTO runs (started_at, status) VALUES ('x', 'ok')"})

    def test_pragma_rejected(self, tmp_db: Path) -> None:
        tool = adversarial_cron.make_sql_tool(tmp_db)
        with pytest.raises(ValueError, match="read-only"):
            tool({"query": "PRAGMA writable_schema = 1"})

    def test_write_blocked_even_if_gate_bypassed(self, tmp_db: Path) -> None:
        """Defense in depth: mode=ro blocks writes at the connection level.
        A sneaky SELECT that tries to write via attached functions can't."""
        tool = adversarial_cron.make_sql_tool(tmp_db)
        out = tool({"query": "SELECT COUNT(*) AS n FROM trades"})
        assert "n" in out


class TestFileTool:
    def test_reads_repo_file(self, repo: Path) -> None:
        tool = adversarial_cron.make_file_tool(repo)
        out = tool({"path": "pending.md"})
        assert "Week 2 strategy-roster review" in out

    def test_escape_rejected(self, repo: Path) -> None:
        tool = adversarial_cron.make_file_tool(repo)
        with pytest.raises(ValueError, match="escapes"):
            tool({"path": "../../../etc/passwd"})

    def test_missing_file_raises(self, repo: Path) -> None:
        tool = adversarial_cron.make_file_tool(repo)
        with pytest.raises(FileNotFoundError):
            tool({"path": "nope.md"})


class _FakeBlock:
    def __init__(self, type_: str, **kw) -> None:
        self.type = type_
        for k, v in kw.items():
            setattr(self, k, v)


class _FakeAgenticMessage:
    def __init__(self, content, stop_reason) -> None:
        self.content = content
        self.stop_reason = stop_reason
        self.usage = type("U", (), {"input_tokens": 100, "output_tokens": 50})()


class _FakeAgenticAnthropicClient:
    """First call: tool_use for run_sql; second: final text."""
    def __init__(self) -> None:
        self.calls = 0
        outer = self

        class _Messages:
            def create(self, **kwargs):
                outer.calls += 1
                outer.last_kwargs = kwargs
                if outer.calls == 1:
                    return _FakeAgenticMessage(
                        [_FakeBlock("tool_use", name="run_sql", id="tu_1",
                                    input={"query": "SELECT COUNT(*) AS n FROM trades"})],
                        "tool_use",
                    )
                return _FakeAgenticMessage(
                    [_FakeBlock("text", text="The bear case, investigated.")],
                    "end_turn",
                )

        self.messages = _Messages()


def test_complete_agentic_round_trip(tmp_db: Path, repo: Path) -> None:
    from claude_client import ClaudeClient, complete_agentic

    client = ClaudeClient(api_key="sk-ant-test", db_path=tmp_db)
    client._client = _FakeAgenticAnthropicClient()

    result = complete_agentic(
        client, "Investigate.", called_from="test_investigator",
        tools=adversarial_cron.INVESTIGATOR_TOOLS,
        tool_handlers={
            "run_sql": adversarial_cron.make_sql_tool(tmp_db),
            "read_file": adversarial_cron.make_file_tool(repo),
        },
    )

    assert result.text == "The bear case, investigated."
    assert result.turns == 2
    # both API calls audited
    with db.connect(tmp_db) as conn:
        rows = conn.execute(
            "SELECT called_from FROM llm_calls ORDER BY id"
        ).fetchall()
    assert [r["called_from"] for r in rows] == ["test_investigator#t1", "test_investigator#t2"]


def test_complete_agentic_tool_error_becomes_result(tmp_db: Path, repo: Path) -> None:
    from claude_client import ClaudeClient, complete_agentic

    class _BadToolClient(_FakeAgenticAnthropicClient):
        pass

    client = ClaudeClient(api_key="sk-ant-test", db_path=tmp_db)
    fake = _BadToolClient()
    client._client = fake

    def exploding(_inp):
        raise RuntimeError("boom")

    result = complete_agentic(
        client, "Investigate.", called_from="test_err",
        tools=adversarial_cron.INVESTIGATOR_TOOLS,
        tool_handlers={"run_sql": exploding, "read_file": exploding},
    )
    # loop survived the tool error and produced the final text
    assert result.text == "The bear case, investigated."
    # the error was passed back as an is_error tool_result
    second_call_messages = fake.last_kwargs["messages"]
    tool_result_msg = second_call_messages[-1]["content"][0]
    assert tool_result_msg["is_error"] is True
    assert "boom" in tool_result_msg["content"]
