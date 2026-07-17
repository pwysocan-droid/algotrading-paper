"""The idea foundry — recurring multi-lens synthesis, forbidden from the past.

The phase the curriculum was pointing at (decision-log 2026-07-16 foundry
entry): the canon was tested first ON PURPOSE, its failures are documented
in reviews/foundry/dead-ideas.json, and from here the project iterates
aggressively — many ideas, many points of view, machine-falsified — while
the live roster stays boringly disciplined at 3 arms.

Each round: 5 ideas, each from a DIFFERENT assigned lens, none descending
from a dead lineage in the registry, each engaging the failure lessons
explicitly. Specs land in reviews/foundry/round-N.{json,md}; the gauntlet
falsifies them; results feed back into the registry so no round repeats a
death. Wild in the lab, boring in production.

Run on the VPS: python scripts/idea_foundry.py
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
FOUNDRY_DIR = REPO_ROOT / "reviews" / "foundry"
REGISTRY_PATH = FOUNDRY_DIR / "dead-ideas.json"

# The rotating points of view. Each round assigns one idea per lens —
# perspective diversity is the mechanism that escapes the canon's basin.
LENSES = [
    ("information_theory",
     "Information-theoretic structure in the bar stream itself: "
     "compressibility, entropy of return sequences, surprise relative to "
     "recent distribution, regime novelty detection. The bars as a signal "
     "to decode, not a chart to read."),
    ("cross_domain_import",
     "A mechanism imported from OUTSIDE finance — epidemiology (contagion "
     "dynamics), queueing theory, seismology (aftershock statistics, "
     "Omori's law), ecology (predator-prey cycles), hydrology (dam-burst "
     "dynamics). Name the source field and map the mechanism honestly."),
    ("microstructure_from_ohlcv",
     "Order-flow structure inferred from OHLCV alone: what wick/body/"
     "volume geometry reveals about absorbed supply, failed auctions, "
     "one-sided books. Microstructure without the order book."),
    ("behavioral_calendar",
     "Human and institutional rhythm: round-number magnetism, stop-hunt "
     "geometry, month-end/options-expiry flows, time-of-day fatigue "
     "patterns — but NOT the already-dead weekend/dead-zone lineages."),
    ("meta_self_referential",
     "Strategies about the system itself: condition on the placebo arm's "
     "recent outcomes, on the constraint layer's rejection rate, on the "
     "portfolio's own drawdown state, on cross-arm divergence. The system "
     "observing itself as a signal source."),
    ("multi_day_horizon",
     "Escape the fee floor by outrunning it: theses that resolve over 2-7 "
     "DAYS targeting 8-20% moves, where 0.6% costs are a rounding error. "
     "Per-variant exits are now supported — declare tp/sl/time_exit_hours "
     "in params (e.g. tp 0.12, sl 0.05, time_exit_hours 120). Fewer, "
     "bigger, slower: regime persistence, multi-day accumulation "
     "structures, post-shock drift over days not bars."),
    ("cost_engineering",
     "Attack the denominator: ideas whose ENTRY MECHANICS inherently "
     "reduce cost or improve fills — entries at levels where price comes "
     "to you (limit-friendly: pullback-to-level entries rather than "
     "chasing), ultra-selective single-fire theses (one great fill beats "
     "five mediocre ones per slot), entries during spread-tight high-"
     "liquidity windows only."),
    ("gate_engine_pairing",
     "The proven gradient: the self-referential regime gate (null-arm "
     "win rate + stop-out cluster, context_keys=['system_state']) scored "
     "the best numbers ever tested — the GATE works, its old engine "
     "didn't. Propose a strong standalone engine explicitly designed to "
     "be gated by it: what entry signal is most amplified by 'random "
     "entries are currently failing = the regime is directional'?"),
]


class FoundryIdea(BaseModel):
    name: str = Field(description="snake_case variant name")
    lens: str = Field(description="The assigned lens this idea answers to")
    mechanism: str = Field(description="The causal mechanism, in one paragraph — WHY this structure exists and WHY it is not already arbitraged away at 5-min retail scale")
    lineage_check: str = Field(description="Honest statement of the nearest dead lineage in the registry and why this idea is NOT a descendant of it")
    entry_rule: str = Field(description="Precise, implementable entry rule using only OHLCV bars (plus btc_bars context if declared). Exact conditions, lookbacks, thresholds.")
    params: dict = Field(description="Named numeric parameters with defaults")
    expected_fire_rate: str = Field(description="Expected signals/symbol/day with reasoning")
    fee_survival: str = Field(description="Why expected move per event exceeds ~1%, engaging the fee-floor lesson")
    kill_criterion: str = Field(description="What gauntlet result kills this idea decisively")


class FoundryRound(BaseModel):
    ideas: list[FoundryIdea] = Field(description="One idea per assigned lens, in lens order")
    round_thesis: str = Field(description="One paragraph: what this round explores that no prior round did")


FOUNDRY_SYSTEM = """\
You are the idea foundry of a paper-trading research project in its
aggressive-iteration phase. The textbook canon and the documented retail
structural plays were tested first, deliberately, and died on the record
— their epitaphs are in your prompt. Your job is what comes after the
canon: ideas that did not exist in this context before. Every idea must
be falsifiable, implementable from OHLCV bars, and honest about its
mechanism. Wildness is required; hand-waving is not. An idea that dies
cleanly in the gauntlet is a success; an idea that resembles a registry
epitaph is a failure of imagination.\
"""


def _next_round_number() -> int:
    existing = sorted(FOUNDRY_DIR.glob("round-*.json"))
    if not existing:
        return 1
    last = existing[-1].stem.split("-")[1]
    return int(last) + 1


def build_prompt(registry: dict) -> str:
    lessons = "\n".join(f"- {l}" for l in registry["failure_lessons"])
    epitaphs = "\n".join(
        f"- {i['name']} ({i['lineage']}): {i['verdict']}"
        + (f" — {i['epitaph']}" if i.get("epitaph") else "")
        for i in registry["ideas"]
    )
    lens_block = "\n".join(
        f"{n + 1}. lens `{key}`: {desc}" for n, (key, desc) in enumerate(LENSES)
    )
    return (
        f"Produce this round of the foundry: exactly {len(LENSES)} strategy "
        "ideas for 5-minute OHLCV crypto bars (BTC, ETH, SOL, LINK, AVAX vs "
        "USD), one idea per assigned lens below, in order.\n\n"
        "THE FAILURE LESSONS (every idea must engage these):\n"
        f"{lessons}\n\n"
        "THE DEAD-IDEAS REGISTRY (no idea may descend from a dead lineage; "
        "your lineage_check must name the nearest death and differentiate):\n"
        f"{epitaphs}\n\n"
        "THE FIVE LENSES FOR THIS ROUND:\n"
        f"{lens_block}\n\n"
        "Platform constraints: $200/trade, $1,000 ceiling, 5 slots, "
        "1h/symbol cooldown, bars only; exits DEFAULT to +5%/-3%/24h but "
        "are now per-variant tunable via params tp/sl/time_exit_hours "
        "(plus a BTC-bars context feed if an idea declares it). Fitness is "
        "edge per constraint slot. Each idea needs a kill_criterion — the "
        "gauntlet number that would falsify it decisively."
    )


def run_round(client=None, now: datetime | None = None) -> Path:
    ts = now or datetime.now(timezone.utc)
    registry = json.loads(REGISTRY_PATH.read_text())
    round_n = _next_round_number()

    if client is None:
        from claude_client import ClaudeClient, model_for_role

        client = ClaudeClient(model=model_for_role("synthesis"))
    result = client.complete_structured(
        prompt=build_prompt(registry),
        schema_cls=FoundryRound,
        called_from="idea_foundry",
        system=FOUNDRY_SYSTEM,
        max_tokens=8192,
    )
    round_data: FoundryRound = result.parsed

    json_path = FOUNDRY_DIR / f"round-{round_n:03d}.json"
    json_path.write_text(json.dumps(
        {"round": round_n, "generated_at": ts.isoformat(),
         "model": result.model, **round_data.model_dump()},
        indent=2) + "\n")

    md = [
        f"# Idea foundry — round {round_n:03d}",
        "",
        f"{ts.date().isoformat()} · model {result.model} · called_from idea_foundry · logged to llm_calls",
        "",
        f"**Round thesis.** {round_data.round_thesis}",
        "",
        "---",
        "",
    ]
    for i, idea in enumerate(round_data.ideas, 1):
        md += [
            f"## {i}. `{idea.name}`  ·  lens: {idea.lens}",
            "",
            f"**Mechanism.** {idea.mechanism}",
            "",
            f"**Lineage check.** {idea.lineage_check}",
            "",
            f"**Entry rule.** {idea.entry_rule}",
            "",
            f"**Params.** `{json.dumps(idea.params)}`",
            "",
            f"**Fire rate.** {idea.expected_fire_rate}",
            "",
            f"**Fee survival.** {idea.fee_survival}",
            "",
            f"**Kill criterion.** {idea.kill_criterion}",
            "",
        ]
    md_path = FOUNDRY_DIR / f"round-{round_n:03d}.md"
    md_path.write_text("\n".join(md))
    return md_path


def main() -> int:
    db.migrate()
    path = run_round()
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
