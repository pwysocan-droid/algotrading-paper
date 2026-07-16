"""Generate surface/learnings.json — the learnings ledger.

Phase 1b term 3 (phase1-review.md § 5): learnings become data, not
prose. The ledger has two layers:

1. The five knowledge-success questions from philosophy.md § "Knowledge
   success" — fixed, hand-maintained here, because they are the
   project's pre-registered success criteria and must not drift with an
   LLM's mood. Each carries a status and evidence pointers.
2. LLM-extracted learnings and falsifiable hypotheses mined from
   decision-log.md via ClaudeClient.complete_structured() — the first
   real use of the structured mode built in May. Every extracted claim
   carries status (validated/pending/falsified), evidence, and a
   next-check date; overdue checks are the dashboard's red flags.

Extraction is hash-gated: the LLM runs only when decision-log.md's
sha256 differs from the one recorded in the existing ledger, so the
nightly cron re-extracts only on real changes (~free otherwise).

Run on the VPS (writes llm_calls via the single writer):
    python scripts/generate_learnings.py [--force]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel, Field

import db

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / "surface" / "learnings.json"

# Layer 1 — philosophy.md's five knowledge-success questions, verbatim.
# Statuses here are operator/code-maintained; the LLM never edits these.
KNOWLEDGE_QUESTIONS = [
    {
        "id": "fees-slippage",
        "question": "What's the actual impact of fees and slippage on retail-size paper-traded crypto strategies?",
        "status": "answered",
        "summary": "~$1/round-trip on $200 positions (0.25% taker both legs). "
                   "Gross +$1,085 became net -$782 on the 3-month backtest — "
                   "the delta is the answer. Fees erase thin edges.",
        "evidence": ["reports/2026-07-02-replay-gate.md", "decision-log.md 2026-07-02 roster entry"],
    },
    {
        "id": "parameter-robustness",
        "question": "Which parameter ranges of Bollinger and MA-crossover are robust to regime shifts, and which are overfit?",
        "status": "answered",
        "summary": "None are robust: all 12 variants with n>100 negative over 6 "
                   "months net of costs. Per-regime conditioning untested (rung 3).",
        "evidence": ["reports/2026-07-02-replay-6month.md"],
    },
    {
        "id": "constraint-dominance",
        "question": "(Emergent) Do constraints or strategies determine outcomes at this scale?",
        "status": "answered",
        "summary": "Constraints dominate: 99.6% of candidate signals died on "
                   "cooldown/exposure/concurrency. Candidate fitness = edge per "
                   "constraint slot, not signal frequency.",
        "evidence": ["reports/2026-07-02-replay-6month.md § 04"],
    },
    {
        "id": "sentiment-value",
        "question": "Does sentiment data (Fear & Greed) improve technical strategies, or is it noise?",
        "status": "untested",
        "summary": "Layer 2 (context) never went live; deferred past Phase 1b "
                   "per one-factor-at-a-time.",
        "evidence": [],
    },
    {
        "id": "tuner-out-of-sample",
        "question": "Does the walk-forward tuner produce variants that hold up out-of-sample?",
        "status": "untested",
        "summary": "tune.py never built; compare.py (the scoring instrument) "
                   "now exists. Blocked on the candidate roster accumulating "
                   "live trades.",
        "evidence": ["compare.py"],
    },
]


class Learning(BaseModel):
    claim: str = Field(description="One-sentence, falsifiable statement of what was learned")
    status: str = Field(description="'validated' | 'pending' | 'falsified'")
    evidence: str = Field(description="The decision-log entry date/title or file that supports it")
    next_check: str | None = Field(
        default=None,
        description="ISO date when this claim should be re-verified, null if settled",
    )


class Hypothesis(BaseModel):
    commitment: str = Field(description="The falsifiable hypothesis as committed")
    source_entry: str = Field(description="Decision-log entry date/title that committed it")
    due: str | None = Field(default=None, description="ISO due date if one was stated")
    status: str = Field(description="'open' | 'resolved-for' | 'resolved-against' | 'overdue'")
    resolution: str | None = Field(default=None, description="How it resolved, if it did")


class LedgerExtraction(BaseModel):
    learnings: list[Learning] = Field(description="Every distinct learning in the log")
    hypotheses: list[Hypothesis] = Field(
        description="Every 'falsifiable hypothesis this entry commits to' and similar pre-commitments"
    )


EXTRACTION_SYSTEM = """\
You are extracting a learnings ledger from a trading project's decision
log. Extract only claims the log actually supports — no invention, no
softening. A learning is 'validated' only if evidence in the log or its
referenced reports confirms it; 'falsified' if later entries contradict
it; otherwise 'pending'. For hypotheses, judge from entry dates whether
stated deadlines have passed: unresolved past-deadline hypotheses are
'overdue', and if a later entry records the outcome, use
'resolved-for'/'resolved-against'. Dates you output must appear in or be
directly computable from the log text.\
"""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _current_ledger_hash() -> str | None:
    if not LEDGER_PATH.exists():
        return None
    try:
        return json.loads(LEDGER_PATH.read_text()).get("decision_log_sha256")
    except (json.JSONDecodeError, AttributeError):
        return None


def generate(client=None, force: bool = False, now: datetime | None = None) -> bool:
    """Regenerate the ledger if decision-log.md changed. Returns True if
    written. `client` injectable for tests (needs .complete_structured
    returning an object with .parsed)."""
    ts = now or datetime.now(timezone.utc)
    log_path = REPO_ROOT / "decision-log.md"
    log_sha = _sha(log_path)

    if not force and log_sha == _current_ledger_hash():
        return False

    if client is None:
        from claude_client import ClaudeClient, model_for_role

        client = ClaudeClient(model=model_for_role("synthesis"))
    result = client.complete_structured(
        prompt=(
            "Extract the learnings ledger from this decision log:\n\n"
            + log_path.read_text()
        ),
        schema_cls=LedgerExtraction,
        called_from="learnings_ledger",
        system=EXTRACTION_SYSTEM,
        max_tokens=8192,
    )
    extraction: LedgerExtraction = result.parsed

    # Flag overdue next-checks / hypotheses relative to today.
    today = ts.date().isoformat()
    overdue_checks = [
        l.model_dump() for l in extraction.learnings
        if l.next_check and l.next_check < today and l.status == "pending"
    ]

    ledger = {
        "generated_at": ts.isoformat(),
        "decision_log_sha256": log_sha,
        "questions": KNOWLEDGE_QUESTIONS,
        "learnings": [l.model_dump() for l in extraction.learnings],
        "hypotheses": [h.model_dump() for h in extraction.hypotheses],
        "overdue": overdue_checks,
    }
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2) + "\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate surface/learnings.json")
    parser.add_argument("--force", action="store_true",
                        help="re-extract even if decision-log.md is unchanged")
    args = parser.parse_args()

    db.migrate()
    written = generate(force=args.force)
    print(f"learnings.json {'written' if written else 'unchanged (hash match)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
