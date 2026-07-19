"""Run-5 quick win #5 — the dumbest multi-week momentum, backtested.

The literature-prior slow band (1-8 week holds) was labeled
"unmeasurable in our archive" — but that predates per-variant exits.
Naive TSMOM: at each weekly decision point (Mon 00:00 UTC), if the
trailing 28-day return exceeds +10%, buy; exits tp15/sl8/336h. If even
THIS clears the fee floor gross, the slow band becomes a backtestable
r005+ lens; if it is dead, the band closes and live/shadow is the only
instrument there.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
import replay
import signals
from config import SLIPPAGE_PCT, TAKER_FEE_PCT, WATCHED_SYMBOLS

REPO_ROOT = Path(__file__).resolve().parent.parent
LOOKBACK = 288 * 28  # 28 days of 5-min bars


def tsmom(bars, params, ctx):
    last = bars[-1]
    t = datetime.fromisoformat(last.timestamp)
    if not (t.weekday() == 0 and t.hour == 0 and t.minute == 0):
        return None
    if len(bars) < LOOKBACK + 1:
        return None
    past = bars[-LOOKBACK - 1]
    if past.close <= 0:
        return None
    ret = last.close / past.close - 1.0
    th = float(params.get("threshold", 0.10))
    if th >= 0 and ret <= th:
        return None  # negative threshold = unconditional weekly buy (drift null)
    return signals.Signal(
        symbol=last.symbol, variant_name="", strategy="tsmom_probe",
        side="buy", bar_timestamp=last.timestamp,
        price_at_signal=last.close, reasoning={"ret_28d": ret})


signals.STRATEGY_REGISTRY["tsmom_probe"] = tsmom
import os
THRESH = float(os.environ.get("TSMOM_THRESHOLD", "0.10"))
variant = {"strategy": "tsmom_probe",
           "params": {"threshold": THRESH, "tp": 0.15, "sl": 0.08,
                      "time_exit_hours": 336},
           "context_keys": [], "enabled": True}
end = datetime(2026, 1, 1, tzinfo=timezone.utc)   # selection window only
start = end - timedelta(days=733)
with db.connect(REPO_ROOT / "research_bars.db") as conn:
    trades = replay.replay_variant(
        conn, "tsmom_probe_v", variant, WATCHED_SYMBOLS, start, end,
        fee_pct=TAKER_FEE_PCT, slippage_pct=SLIPPAGE_PCT,
        window_cap=LOOKBACK + 2,
    )
placed = [t for t in replay.apply_portfolio_constraints(trades) if t.accepted]
closed = [t for t in placed if t.pnl_usd is not None]
gross = [(t.pnl_usd + t.fees_usd) / (t.qty * t.entry_price) * 100 for t in closed]
net = [t.pnl_usd / (t.qty * t.entry_price) * 100 for t in closed]
wins = sum(1 for x in net if x > 0)
res = {
    "date": datetime.now(timezone.utc).date().isoformat(),
    "window": "selection only (through 2026-01-01)",
    "candidates": len(trades), "placed": len(placed), "closed": len(closed),
    "win_rate": wins / len(closed) if closed else None,
    "gross_mean_pct": sum(gross) / len(gross) if gross else None,
    "net_mean_pct": sum(net) / len(net) if net else None,
    "exit_mix": {},
}
from collections import Counter
res["exit_mix"] = dict(Counter(t.exit_reason for t in closed))
print(json.dumps(res, indent=2))
res["threshold"] = THRESH
(REPO_ROOT / "reports" / f"tsmom-probe-t{THRESH}-{res['date']}.json").write_text(
    json.dumps(res, indent=2) + "\n")
