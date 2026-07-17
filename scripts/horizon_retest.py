"""Horizon re-test: the registry's near-misses under multi-day exits.
Every prior verdict assumed +5%/-3%/24h. The horizon lever changes the
cost arithmetic ~10x; gross-positive ideas deserve re-trial."""
import sys, json
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from datetime import datetime, timezone
from scripts.run_gauntlet import _score_candidate
from config import STRATEGY_VARIANTS
import scripts.run_gauntlet as rg

# near-misses + best gross performers, re-parameterized for 2-5 day horizons
RETESTS = {
    "weekend_momentum_5d":  ("weekend_illiquidity_momentum", {"tp": 0.12, "sl": 0.05, "time_exit_hours": 120}),
    "omori_3d":             ("omori_aftershock_ladder",      {"tp": 0.10, "sl": 0.04, "time_exit_hours": 72}),
    "vol_thrust_3d":        ("volume_thrust_regime_shift",   {"tp": 0.10, "sl": 0.04, "time_exit_hours": 72}),
    "regime_gate_5d":       ("drawdown_regime_contrarian_gate", {"tp": 0.12, "sl": 0.05, "time_exit_hours": 120}),
    "deadzone_3d":          ("dead_zone_range_break",        {"tp": 0.10, "sl": 0.04, "time_exit_hours": 72}),
}
results = []
for new_name, (base, exit_params) in RETESTS.items():
    v = dict(STRATEGY_VARIANTS[base]); v = json.loads(json.dumps(v))
    v["params"] = {**v["params"], **exit_params}
    STRATEGY_VARIANTS[new_name] = {**v, "enabled": False}
    r = _score_candidate((new_name, 930, "./research_bars.db"))
    r["base"] = base; r["exits"] = exit_params
    results.append(r)
    eps = "-" if not r["placed"] else f"${r['total_pnl']/r['placed']:.3f}"
    print(f"{new_name}: placed={r['placed']} pnl=${r['total_pnl']:,.2f} edge/slot={eps} win={r['win_rate']}")
out = "./reports/horizon-retest-2026-07-17.json"
json.dump({"date": "2026-07-17", "days": 930, "note": "multi-day exit re-trial of registry near-misses", "results": results}, open(out, "w"), indent=2)
print("wrote", out)
