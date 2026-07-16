"""A/B comparator — the gate-2 instrument.

Compares two variants' closed live-paper trades (per-trade net return %)
with Welch's unequal-variance t-test. Phase 2 gate 2 and phase1-review.md
§ 5 both key on this: a promotion is valid only if the candidate beats
its baseline at p < 0.05 over 100+ trades. The null_baseline placebo is
the default B side — a candidate that can't beat random entries under
identical constraints has no edge.

Statistical honesty (philosophy.md "knowledge failure" is the worst
failure): below MIN_TRADES_PER_ARM per side, the verdict is INSUFFICIENT
regardless of how good the numbers look — small-sample confidence is the
documented trap. The p-value uses the normal approximation to the t
distribution, which is sound at the gate's required sample sizes (100+)
and conservative-enough above ~30; below that the verdict is
INSUFFICIENT anyway, so the approximation never decides anything alone.

Usage:
    python compare.py --a some_candidate --b null_baseline
    python compare.py --a x --b y --out reports/ab/2026-W29.md
"""

from __future__ import annotations

import argparse
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import db

MIN_TRADES_PER_ARM = 100
SIGNIFICANCE_LEVEL = 0.05


@dataclass
class ArmStats:
    variant: str
    n: int
    mean_pct: float
    std_pct: float
    total_pnl_usd: float


@dataclass
class ComparisonResult:
    a: ArmStats
    b: ArmStats
    t_stat: float | None
    p_value: float | None
    verdict: str  # 'A_WINS' | 'B_WINS' | 'NO_DIFFERENCE' | 'INSUFFICIENT'
    detail: str


def load_arm(conn: sqlite3.Connection, variant: str) -> tuple[ArmStats, list[float]]:
    rows = conn.execute(
        """
        SELECT pnl_pct, pnl_usd FROM trades
         WHERE variant_name = ? AND status = 'closed' AND pnl_pct IS NOT NULL
        """,
        (variant,),
    ).fetchall()
    pcts = [r["pnl_pct"] for r in rows]
    n = len(pcts)
    mean = sum(pcts) / n if n else 0.0
    var = sum((x - mean) ** 2 for x in pcts) / (n - 1) if n > 1 else 0.0
    total = sum(r["pnl_usd"] for r in rows if r["pnl_usd"] is not None)
    return ArmStats(variant, n, mean, math.sqrt(var), total), pcts


def welch_t(a: list[float], b: list[float]) -> tuple[float, float]:
    """Welch's t statistic and two-sided p (normal approximation).

    Requires len >= 2 per side and at least one nonzero variance;
    callers gate on MIN_TRADES_PER_ARM long before those bounds bind.
    """
    na, nb = len(a), len(b)
    ma, mb = sum(a) / na, sum(b) / nb
    va = sum((x - ma) ** 2 for x in a) / (na - 1)
    vb = sum((x - mb) ** 2 for x in b) / (nb - 1)
    se = math.sqrt(va / na + vb / nb)
    if se == 0.0:
        # identical constant samples — no evidence of difference
        return 0.0, 1.0
    t = (ma - mb) / se
    # two-sided p via the normal approximation: erfc(|t|/sqrt(2))
    p = math.erfc(abs(t) / math.sqrt(2))
    return t, p


def compare(
    variant_a: str, variant_b: str, db_path: Path | None = None
) -> ComparisonResult:
    with db.connect(db_path) as conn:
        arm_a, pcts_a = load_arm(conn, variant_a)
        arm_b, pcts_b = load_arm(conn, variant_b)

    if arm_a.n < MIN_TRADES_PER_ARM or arm_b.n < MIN_TRADES_PER_ARM:
        return ComparisonResult(
            a=arm_a, b=arm_b, t_stat=None, p_value=None,
            verdict="INSUFFICIENT",
            detail=(
                f"gate requires {MIN_TRADES_PER_ARM}+ closed trades per arm; "
                f"have {arm_a.variant}={arm_a.n}, {arm_b.variant}={arm_b.n}. "
                f"Any performance claim at this sample size is statistically "
                f"unreliable — the correct response is 'wait for more data'."
            ),
        )

    t, p = welch_t(pcts_a, pcts_b)
    if p >= SIGNIFICANCE_LEVEL:
        verdict = "NO_DIFFERENCE"
        detail = (
            f"p={p:.4f} >= {SIGNIFICANCE_LEVEL}: the observed difference in "
            f"mean per-trade return is consistent with noise."
        )
    elif arm_a.mean_pct > arm_b.mean_pct:
        verdict = "A_WINS"
        detail = f"{arm_a.variant} beats {arm_b.variant} at p={p:.4f}."
    else:
        verdict = "B_WINS"
        detail = f"{arm_b.variant} beats {arm_a.variant} at p={p:.4f}."

    return ComparisonResult(a=arm_a, b=arm_b, t_stat=t, p_value=p,
                            verdict=verdict, detail=detail)


def render_report(result: ComparisonResult, now: datetime | None = None) -> str:
    ts = now or datetime.now(timezone.utc)
    em = "—"

    def fmt(v, pattern="{:.4f}"):
        return pattern.format(v) if v is not None else em

    lines = [
        "# algotrading-paper / A/B comparison",
        "",
        f"{result.a.variant} vs {result.b.variant}  ·  closed live-paper trades",
        "",
        ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "",
        f"**Verdict: {result.verdict}**",
        "",
        result.detail,
        "",
        "| Arm | n | mean pnl % | std pnl % | total P&L |",
        "| --- | --- | --- | --- | --- |",
        f"| `{result.a.variant}` | {result.a.n} | {result.a.mean_pct:+.4f}% "
        f"| {result.a.std_pct:.4f}% | ${result.a.total_pnl_usd:,.2f} |",
        f"| `{result.b.variant}` | {result.b.n} | {result.b.mean_pct:+.4f}% "
        f"| {result.b.std_pct:.4f}% | ${result.b.total_pnl_usd:,.2f} |",
        "",
        f"Welch t = {fmt(result.t_stat)}  ·  two-sided p = {fmt(result.p_value)}  ·  "
        f"gate: p < {SIGNIFICANCE_LEVEL} with {MIN_TRADES_PER_ARM}+ trades per arm",
        "",
        "---",
        "",
        "generated by compare.py v0.1.0",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="A/B comparison of two variants' closed trades")
    parser.add_argument("--a", required=True, help="candidate variant name")
    parser.add_argument("--b", default="null_baseline", help="baseline variant (default: null_baseline)")
    parser.add_argument("--out", type=Path, default=None, help="optional markdown report path")
    args = parser.parse_args()

    db.migrate()
    result = compare(args.a, args.b)
    report = render_report(result)
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
