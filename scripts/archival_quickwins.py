"""Run-5 archival quick wins #7 and #3 — interrogating our own corpus.

#7: fire-rate calibration regression over the registry's gradient
    records — is the 3x-2000x miss STRUCTURED (fittable prior) or noise?
#3: the null arm's EMPIRICAL breakeven under +5/-3/24h — the "~38-40%
    breakeven" reference every win-rate comparison leans on was assumed,
    never measured.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_gauntlet import _score_candidate

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- #7: gradient regression -------------------------------------------
reg = json.loads((REPO_ROOT / "reviews/foundry/dead-ideas.json").read_text())
pts = []
for i in reg["ideas"]:
    g = i.get("gradient") or {}
    p, a = g.get("predicted_fires_per_sym_day"), g.get("actual")
    if p and a and p > 0 and a and a > 0:
        pts.append((i["name"], p, a, math.log10(a / p)))
print(f"# Fire-rate calibration ({len(pts)} gradient records)")
xs = [math.log10(p) for _, p, _a, _ in pts]
ys = [math.log10(a) for _, _p, a, _ in pts]
n = len(pts)
mx, my = sum(xs) / n, sum(ys) / n
sxx = sum((x - mx) ** 2 for x in xs)
slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else float("nan")
intercept = my - slope * mx
resid = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
rmse = (sum(r * r for r in resid) / n) ** 0.5
print(f"log10(actual) = {intercept:+.2f} + {slope:.2f} * log10(predicted)  (rmse {rmse:.2f} dex)")
mean_err = sum(e for *_, e in pts) / n
print(f"mean log-error {mean_err:+.2f} dex (i.e. actual ~= predicted x {10**mean_err:.2f})")
rare = [e for _, p, _a, e in pts if p < 0.3]
common = [e for _, p, _a, e in pts if p >= 0.3]
if rare and common:
    print(f"rare specs (<0.3/day, n={len(rare)}): mean err {sum(rare)/len(rare):+.2f} dex")
    print(f"common specs (>=0.3/day, n={len(common)}): mean err {sum(common)/len(common):+.2f} dex")

# --- #3: null empirical breakeven --------------------------------------
print("\n# Null-arm empirical breakeven (930d, +5/-3/24h, constrained)")
r = _score_candidate(("null_baseline", 930, str(REPO_ROOT / "research_bars.db")))
trades = r.get("trades", [])
closed = [t for t in trades if t.get("pnl_usd") is not None]
wins = sum(1 for t in closed if t["pnl_usd"] > 0)
print(f"placed={r['placed']} win_rate={r['win_rate']:.1%} edge/slot=${r['edge_per_slot']:.3f}")
from collections import Counter
exits = Counter(t.get("exit_reason") for t in closed)
print("exit mix:", dict(exits))
for reason in ("take_profit", "stop_loss", "time_exit"):
    sub = [t for t in closed if t.get("exit_reason") == reason]
    if sub:
        m = sum(t["pnl_usd"] for t in sub) / len(sub)
        print(f"  {reason}: n={len(sub)} mean=${m:.2f}")
out = {
    "date": datetime.now(timezone.utc).date().isoformat(),
    "fire_rate_regression": {"n": n, "slope": slope, "intercept": intercept,
                             "rmse_dex": rmse, "mean_err_dex": mean_err},
    "null_breakeven": {"placed": r["placed"], "win_rate": r["win_rate"],
                       "edge_per_slot": r["edge_per_slot"],
                       "exit_mix": dict(exits)},
}
(REPO_ROOT / "reports" / f"archival-quickwins-{out['date']}.json").write_text(
    json.dumps(out, indent=2) + "\n")
