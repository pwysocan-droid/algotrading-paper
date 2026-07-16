"""LLM candidate synthesis — the aggression half of the thesis, run once.

Phase 1b term 2 (phase1-review.md § 5) and the 2026-07-02 retirement
entry's "what replaces them". Claude proposes strategy candidates through
the audited client (llm_calls, synthesis-role model, structured output);
the specs land in a JSON + markdown pair for the operator and for the
implementer. Implementation, backtesting, and registration happen in
code review afterwards — the LLM surfaces, the discipline decides
(decision-log 2026-04-26: Claude never decides what trades, and the
A/B gate decides what gets promoted).

The prompt encodes what Phase 1 actually learned, so the search
optimizes the right objective:
  - constraints dominate: cooldown caps 24 trades/symbol/day; 99.6% of
    frequent signals die — selectivity beats frequency
  - fees are ~0.6%/round-trip on $200; an edge must clear that
  - only OHLCV bars exist (no external data until Layer 2)
  - exits are fixed: +5% target / -3% stop / 24h time exit
  - the historical retail-algo lens: what actually survived for retail
    algorithmic traders through the 2010s-2020s, not textbook canon

Run on the VPS: python scripts/synthesize_candidates.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel, Field

import db

REPO_ROOT = Path(__file__).resolve().parent.parent


class CandidateSpec(BaseModel):
    name: str = Field(description="snake_case variant name, e.g. 'vol_breakout_confirmed'")
    thesis: str = Field(description="One-sentence falsifiable thesis for why this has edge")
    lens: str = Field(description="The historical retail-algo evidence: what class of retail strategies this descends from and how that class actually fared in the 2010s-2020s")
    entry_rule: str = Field(description="Precise, implementable entry rule using only OHLCV bars — exact conditions, lookbacks, thresholds. Someone must code this without asking questions.")
    params: dict = Field(description="Named numeric parameters with default values")
    expected_fire_rate: str = Field(description="Expected signals per symbol per day, with reasoning — selectivity beats frequency")
    fee_survival: str = Field(description="Why the expected move per trade clears the ~0.6% round-trip cost")


class SynthesisResult(BaseModel):
    candidates: list[CandidateSpec] = Field(description="Exactly 5 candidates, ordered by conviction")
    what_was_deliberately_avoided: str = Field(
        description="Categories of conventional wisdom left behind, and why"
    )


SYNTHESIS_SYSTEM = """\
You are the epistemological backbone of a paper-trading research project
doing its one candidate-synthesis pass. Be radically unconventional in
what you surface — leave behind whole categories of conventional wisdom
— but every candidate must be precisely implementable and falsifiable.
This is 'epistemological aggression with methodological rigor': the
aggression is yours, the rigor is the gauntlet your candidates will run
(6-month replay under real constraints and fees, then live A/B against
a random-entry placebo at p<0.05 over 100+ trades). Textbook indicators
(Bollinger, MA-crossover) were already tested and retired: every variant
with a real sample lost money net of fees. Do not resurface them.\
"""

SYNTHESIS_PROMPT = """\
Propose exactly 5 strategy candidates for 5-minute OHLCV crypto bars
(BTC, ETH, SOL, LINK, AVAX vs USD, Alpaca paper).

Hard facts from Phase 1 (your search must optimize for these):

1. CONSTRAINTS DOMINATE. Portfolio limits: $200/trade, $1,000 total,
   5 concurrent positions, 1h per-symbol cooldown. In backtest, 99.6%
   of a frequent strategy's signals died on these constraints. The
   fitness function is edge per constraint slot, not signal frequency.
   A candidate that fires twice a day with conviction beats one that
   fires every bar.
2. FEES ARE THE FLOOR. ~0.6% round-trip (0.5% taker fees + slippage)
   on $200 positions. Textbook mean-reversion produced +0.03% gross
   per trade — fees made it -0.18% net. Expected move per trade must
   plausibly exceed ~1%.
3. EXITS ARE FIXED. +5% take-profit, -3% stop, 24h time exit,
   checked every 5 minutes. Your entry must make sense with exactly
   these exits — no custom exit logic is available.
4. ONLY BARS EXIST. OHLCV history per symbol, nothing else — no order
   books, no funding rates, no sentiment, no cross-exchange data. A
   strategy function receives the last ~200 bars (and can request the
   window it needs) and returns buy/sell/nothing for the latest bar.
5. THE HISTORICAL LENS. Apply what is actually documented about
   retail algorithmic trading through the 2010s-2020s: which classes
   of retail strategies survived (and under what regime), which were
   arbitraged away, and which only ever worked in backtests. Name the
   lineage for each candidate honestly.

Crypto-specific structure worth mining: 24/7 sessions with known
dead-zones, liquidation cascades and their aftermath, weekend/weekday
regime differences, volatility clustering, cross-asset lead-lag from
BTC dominance. All of these are visible in OHLCV alone.

Be aggressive about what you surface; be honest in expected_fire_rate
and fee_survival — candidates die in replay, not in the pitch.\
"""


def run_synthesis(client=None, now: datetime | None = None) -> Path:
    ts = now or datetime.now(timezone.utc)
    date_str = ts.date().isoformat()

    if client is None:
        from claude_client import ClaudeClient, model_for_role

        client = ClaudeClient(model=model_for_role("synthesis"))
    result = client.complete_structured(
        prompt=SYNTHESIS_PROMPT,
        schema_cls=SynthesisResult,
        called_from="candidate_synthesis",
        system=SYNTHESIS_SYSTEM,
        max_tokens=8192,
    )
    synthesis: SynthesisResult = result.parsed

    out_dir = REPO_ROOT / "reviews"
    json_path = out_dir / f"candidates-{date_str}.json"
    json_path.write_text(json.dumps(synthesis.model_dump(), indent=2) + "\n")

    md_lines = [
        f"# Candidate synthesis — {date_str}",
        "",
        f"model {result.model} · called_from candidate_synthesis · logged to llm_calls",
        "",
        "The LLM surfaces; the discipline decides. Every candidate below runs",
        "the gauntlet: implemented → 6-month constrained replay → scored by",
        "edge per constraint slot → top 2 registered live against null_baseline.",
        "",
        "---",
        "",
    ]
    for i, c in enumerate(synthesis.candidates, 1):
        md_lines += [
            f"## {i}. `{c.name}`",
            "",
            f"**Thesis.** {c.thesis}",
            "",
            f"**Lens.** {c.lens}",
            "",
            f"**Entry rule.** {c.entry_rule}",
            "",
            f"**Params.** `{json.dumps(c.params)}`",
            "",
            f"**Expected fire rate.** {c.expected_fire_rate}",
            "",
            f"**Fee survival.** {c.fee_survival}",
            "",
        ]
    md_lines += [
        "---",
        "",
        "## What was deliberately avoided",
        "",
        synthesis.what_was_deliberately_avoided,
        "",
    ]
    md_path = out_dir / f"candidates-{date_str}.md"
    md_path.write_text("\n".join(md_lines))
    return md_path


def main() -> int:
    db.migrate()
    path = run_synthesis()
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
