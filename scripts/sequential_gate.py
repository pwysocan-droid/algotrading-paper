"""Sequential promotion gate — SPRT with efficacy AND futility boundaries.

Replaces (pending operator review, decision-log 2026-07-18 ruling 3)
the fixed-n gate whose measured power was ~20-25%. Wald's SPRT on a
live arm's net per-trade returns against the null arm's running mean:

  H0: arm mean − null mean <= 0        (no edge over placebo)
  H1: arm mean − null mean >= delta    (the minimum edge worth having)

After each closed trade the log-likelihood ratio moves; crossing the
upper boundary is EFFICACY (promote-review), crossing the lower is
FUTILITY (retire the arm, free the live slot early — the import from
group-sequential clinical design). Between boundaries: keep sampling.
Valid at every look, so no evidence on the slowest channel is wasted.

The OLD gate remains authoritative until the operator reviews this
script's first boundary table in the decision log — this reports, it
does not yet decide.

    python scripts/sequential_gate.py
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
from config import MAX_POSITION_USD, STRATEGY_VARIANTS

REPO_ROOT = Path(__file__).resolve().parent.parent

ALPHA = 0.05          # false-promotion rate
BETA = 0.20           # false-retirement rate (power 0.8 at delta)
DELTA_PCT = 0.9       # minimum edge over null worth having, %/trade —
                      # ≈ the cost drag (0.63%) + a real margin; yields
                      # net > ~+0.3%/trade if achieved. Reviewed, not
                      # tuned: change requires a decision-log entry.

UPPER = math.log((1 - BETA) / ALPHA)      # efficacy boundary  (+2.77)
LOWER = math.log(BETA / (1 - ALPHA))      # futility boundary  (−1.56)


def sprt_llr(diffs: list[float], delta: float, sigma: float) -> list[float]:
    """Cumulative log-likelihood ratio trajectory for H1 mean=delta vs
    H0 mean=0, normal approximation with known sigma. diffs are the
    arm's per-trade net returns minus the null benchmark mean, in %."""
    if sigma <= 0:
        return [0.0 for _ in diffs]
    out, llr = [], 0.0
    for x in diffs:
        llr += (delta * x - delta * delta / 2.0) / (sigma * sigma)
        out.append(llr)
    return out


def decide(llr: float) -> str:
    if llr >= UPPER:
        return "EFFICACY — promote-review"
    if llr <= LOWER:
        return "FUTILITY — retire, free the slot"
    return "continue"


def arm_returns(conn, name: str) -> list[float]:
    rows = conn.execute(
        """
        SELECT pnl_usd FROM trades
         WHERE variant_name = ? AND status = 'closed' AND pnl_usd IS NOT NULL
         ORDER BY exit_time ASC
        """,
        (name,),
    ).fetchall()
    return [r["pnl_usd"] / MAX_POSITION_USD * 100.0 for r in rows]


def expected_max_n(sigma: float, delta: float) -> int:
    """Rough fixed-design equivalent n for context (the SPRT usually
    stops far earlier)."""
    z_a, z_b = 1.645, 0.842
    return max(1, int(math.ceil(((z_a + z_b) * sigma / delta) ** 2)))


def main() -> int:
    argparse.ArgumentParser().parse_args()
    now = datetime.now(timezone.utc)
    lines = [
        f"# Sequential gate — {now.date().isoformat()}",
        "",
        f"SPRT vs null arm · delta={DELTA_PCT}%/trade · alpha={ALPHA} "
        f"beta={BETA} · boundaries +{UPPER:.2f} / {LOWER:.2f}",
        "",
        "| arm | n | mean vs null (%/tr) | LLR | state |",
        "| --- | --- | --- | --- | --- |",
    ]
    with db.connect() as conn:
        null_r = arm_returns(conn, "null_baseline")
        null_mean = sum(null_r) / len(null_r) if null_r else 0.0
        pool = null_r or [0.0]
        pm = sum(pool) / len(pool)
        sigma = (sum((x - pm) ** 2 for x in pool) / max(1, len(pool) - 1)) ** 0.5 or 3.0
        for name, v in STRATEGY_VARIANTS.items():
            if not v.get("enabled") or name == "null_baseline":
                continue
            r = arm_returns(conn, name)
            diffs = [x - null_mean for x in r]
            traj = sprt_llr(diffs, DELTA_PCT, sigma)
            llr = traj[-1] if traj else 0.0
            mean_d = (sum(diffs) / len(diffs)) if diffs else 0.0
            lines.append(
                f"| {name} | {len(r)} | {mean_d:+.2f} | {llr:+.2f} | {decide(llr)} |"
            )
    lines += [
        "",
        f"null arm: n={len(null_r)}, mean={null_mean:+.2f}%/trade, "
        f"sigma={sigma:.2f}% · fixed-design equivalent n≈"
        f"{expected_max_n(sigma, DELTA_PCT)}/arm (SPRT usually stops earlier)",
        "",
        "The legacy fixed-n gate remains authoritative until the operator "
        "reviews this table (decision-log 2026-07-18 ruling 3).",
        "",
    ]
    out = REPO_ROOT / "reports" / f"sequential-gate-{now.date().isoformat()}.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
