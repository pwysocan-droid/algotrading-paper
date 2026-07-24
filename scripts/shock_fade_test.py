"""D1 — shock-fade event-driven contrarian probe (new-directions.md).

The measured lead: sign-aligned forward returns after 3%/3x-vol shock
bars run −3 to −4% (fragility re-analysis #2, n=53). So FADING the shock
(enter opposite) should capture a positive move. This tests it as a real
spec: contrarian entry the bar AFTER a qualifying shock, multi-day hold
with tp/sl, VOLATILITY-WIDENED entry cost (shocks = bad fills), against
the control arm the fragility audit demanded — the SAME fade on large
bars that are NOT volume shocks (if the volume/forced-flow condition is
the mechanism, the shock arm must beat the placebo). Regime-split;
selection window only (holdout preserved).

Kill (pre-registered, new-directions D1): net expectancy ≤ 0 after
vol-widened costs, OR shock-fade indistinguishable from the placebo.

    python scripts/shock_fade_test.py
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import db
from config import WATCHED_SYMBOLS

REPO = Path(__file__).resolve().parent.parent
SELECTION_END = "2026-01-01T00:00:00+00:00"
SHOCK_RET, SHOCK_VOL, VOL_WIN = 0.03, 3.0, 100
TP, SL, HOLD_BARS = 0.08, 0.05, 1440        # 8%/5% / 120h (5-min bars)
COOLDOWN = 288                               # 1 day between fades per symbol
FEE, SLIP_NORM, SLIP_SHOCK = 0.0025, 0.0005, 0.0015   # entry slip 3x on shocks
REGIMES = {"2023H2": ("2023-07", "2024-01"), "2024H1": ("2024-01", "2024-07"),
           "2024H2": ("2024-07", "2025-01"), "2025H1": ("2025-01", "2025-07"),
           "2025H2": ("2025-07", "2026-01")}


def load(conn, sym):
    rows = conn.execute(
        "SELECT timestamp, open, high, low, close, volume FROM bars"
        " WHERE symbol=? AND timestamp<? ORDER BY timestamp ASC",
        (sym, SELECTION_END)).fetchall()
    return rows


def sim_exit(bars, i0, side, entry):
    """Walk forward from bar i0; return net-of-nothing exit price+reason."""
    if side == "long":
        tp, sl = entry * (1 + TP), entry * (1 - SL)
    else:
        tp, sl = entry * (1 - TP), entry * (1 + SL)
    for k in range(i0, min(i0 + HOLD_BARS, len(bars))):
        hi, lo, cl = bars[k]["high"], bars[k]["low"], bars[k]["close"]
        if side == "long":
            if lo <= sl: return sl, "sl"
            if hi >= tp: return tp, "tp"
        else:
            if hi >= sl: return sl, "sl"
            if lo <= tp: return tp, "tp"
    return bars[min(i0 + HOLD_BARS, len(bars) - 1)]["close"], "time"


def net_pct(side, entry, exit_px, shock_entry):
    slip_in = SLIP_SHOCK if shock_entry else SLIP_NORM
    e = entry * (1 + slip_in) if side == "long" else entry * (1 - slip_in)
    x = exit_px * (1 - SLIP_NORM) if side == "long" else exit_px * (1 + SLIP_NORM)
    gross = (x / e - 1) if side == "long" else (e / x - 1)
    return (gross - 2 * FEE) * 100.0


def run(conn, require_volume: bool):
    """require_volume True = shock-fade; False = placebo (large bar, NOT a vol shock)."""
    per_regime = {r: [] for r in REGIMES}
    for sym in WATCHED_SYMBOLS:
        rows = load(conn, sym)
        last_fire = -10 ** 9
        for i in range(VOL_WIN, len(rows) - 2):
            o, c, v = rows[i]["open"], rows[i]["close"], rows[i]["volume"]
            if o <= 0:
                continue
            move = c / o - 1.0
            if abs(move) <= SHOCK_RET:
                continue
            med = statistics.median(rows[t]["volume"] for t in range(i - VOL_WIN, i))
            is_shock = med > 0 and v > SHOCK_VOL * med
            if require_volume and not is_shock:
                continue
            if (not require_volume) and is_shock:
                continue          # placebo = large bar that is NOT a vol shock
            if i - last_fire < COOLDOWN:
                continue
            last_fire = i
            side = "short" if move > 0 else "long"       # FADE the move
            entry = rows[i + 1]["open"]
            fwd = [{"high": r["high"], "low": r["low"], "close": r["close"]}
                   for r in rows[i + 2:]]
            if not fwd:
                continue
            exit_px, _ = sim_exit(fwd, 0, side, entry)
            npct = net_pct(side, entry, exit_px, shock_entry=require_volume)
            ym = rows[i]["timestamp"][:7]
            for rname, (a, b) in REGIMES.items():
                if a <= ym < b:
                    per_regime[rname].append(npct); break
    return per_regime


def summarize(name, per_regime):
    alln = [x for r in per_regime for x in per_regime[r]]
    n = len(alln)
    m = statistics.mean(alln) if n else None
    se = statistics.pstdev(alln) / n ** 0.5 if n > 1 else None
    win = sum(1 for x in alln if x > 0) / n if n else None
    print(f"{name}: n={n} net={m:+.3f}%/tr t={(m/se if m and se else 0):+.2f} "
          f"win={win:.0%}" if n else f"{name}: no fires")
    reg = {r: (round(statistics.mean(v), 2) if len(v) > 1 else None, len(v))
           for r, v in per_regime.items()}
    print("   regimes:", {r: reg[r] for r in REGIMES})
    return {"n": n, "net_pct": None if m is None else round(m, 3),
            "t": None if (m is None or not se) else round(m / se, 2),
            "win": None if win is None else round(win, 3),
            "by_regime": {r: reg[r][0] for r in REGIMES}}


def main() -> int:
    with db.connect(REPO / "research_bars.db") as conn:
        shock = run(conn, require_volume=True)
        placebo = run(conn, require_volume=False)
    print("\n== D1 shock-fade (vol-widened costs, selection window) ==")
    s = summarize("shock-fade ", shock)
    p = summarize("placebo(lg)", placebo)
    edge = (s["net_pct"] or 0) - (p["net_pct"] or 0)
    verdict = ("SURVIVES probe" if (s["net_pct"] and s["net_pct"] > 0
               and edge > 0) else "KILLED")
    print(f"\nshock-minus-placebo = {edge:+.3f}%/tr · verdict: {verdict} "
          f"(kill: net<=0 OR not > placebo)")
    out = {"date": datetime.now(timezone.utc).date().isoformat(),
           "shock_fade": s, "placebo_large_bar": p,
           "shock_minus_placebo_pct": round(edge, 3), "verdict": verdict}
    (REPO / "reports" / f"shock-fade-{out['date']}.json").write_text(
        json.dumps(out, indent=2) + "\n")
    print("wrote report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
