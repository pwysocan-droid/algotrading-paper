"""E2 round zero — the positive control: cross-sectional 12-1 momentum.

Long-only top-decile tilt over a point-in-time liquid universe, monthly
rebalance, measured as EXCESS over the equal-weight-universe benchmark
(the drift null). This is the known-true effect (Jegadeesh-Titman 1993);
if the equity pipeline can't detect it on survivorship-corrected data,
the pipeline is broken, not the market (decision-log 2026-07-20 E2).

Pass bar (pre-registered): pooled annualized long-only excess inside or
above ~2-4%/yr over benchmark, sign right, at the significance ~10yr of
monthly obs affords. Survivorship-corrected archive, -30% involuntary
delisting haircut, universe by trailing-60d dollar volume.

    python scripts/equity_round_zero.py
"""
from __future__ import annotations

import bisect
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sqlite3

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "equities.db"
M, TOPN, DECILE, HAIRCUT, LOOKBACK = 21, 500, 0.10, 0.30, 252
SUBWINDOWS = {"2016-2019": ("2016-01-01", "2020-01-01"),
              "2020-2021": ("2020-01-01", "2022-01-01"),
              "2022-2023": ("2022-01-01", "2024-01-01"),
              "2024-2026": ("2024-01-01", "2026-07-01")}


def mean_se(xs):
    n = len(xs)
    if n < 2:
        return None, None, n
    m = sum(xs) / n
    se = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5
    return m, se, n


def main() -> int:
    conn = sqlite3.connect(DB)
    data: dict = {}
    for sym, day, close, vol in conn.execute(
            "SELECT symbol, day, close, volume FROM daily_bars ORDER BY symbol, day"):
        d = data.setdefault(sym, ([], [], []))
        d[0].append(day); d[1].append(close); d[2].append(vol)
    data = {s: v for s, v in data.items() if len(v[0]) >= LOOKBACK + 25}
    print(f"{len(data)} symbols usable (corrected archive)")
    gdays = sorted({d for v in data.values() for d in v[0]})
    anchors = gdays[LOOKBACK::M]

    excess_by_month = {}   # day -> excess pct
    for D in anchors:
        cutoff = (date.fromisoformat(D) - timedelta(days=7)).isoformat()
        rows = []          # (mom, fwd)
        for sym, (days, closes, vols) in data.items():
            j = bisect.bisect_right(days, D) - 1
            if j < LOOKBACK or days[j] < cutoff:
                continue
            if closes[j - LOOKBACK] <= 0 or closes[j] <= 0:
                continue
            dv = sum(closes[j - k] * vols[j - k] for k in range(60))
            mom = closes[j - 21] / closes[j - LOOKBACK] - 1.0   # 12-1
            fwd = (closes[j + 21] / closes[j] - 1.0) if j + 21 < len(days) \
                else (closes[-1] * (1 - HAIRCUT)) / closes[j] - 1.0
            rows.append((dv, mom, fwd))
        if len(rows) < 100:
            continue
        rows.sort(key=lambda t: -t[0])
        univ = rows[:TOPN]                       # point-in-time liquid set
        bench = sum(t[2] for t in univ) / len(univ)
        univ.sort(key=lambda t: t[1])
        k = max(1, int(len(univ) * DECILE))
        top = sum(t[2] for t in univ[-k:]) / k   # long-only top-decile
        excess_by_month[D] = (top - bench) * 100.0

    all_ex = list(excess_by_month.values())
    m, se, n = mean_se(all_ex)
    ann = m * 12 if m is not None else None
    print(f"\nPOOLED long-only excess over benchmark: {m:+.3f}%/mo "
          f"(t={m/se:+.2f}, n={n}) → {ann:+.1f}%/yr" if m else "insufficient")
    per = {}
    for w, (a, b) in SUBWINDOWS.items():
        xs = [v for d, v in excess_by_month.items() if a <= d < b]
        wm, wse, wn = mean_se(xs)
        per[w] = {"excess_mo_pct": None if wm is None else round(wm, 3),
                  "t": None if (wm is None or not wse) else round(wm / wse, 2),
                  "ann_pct": None if wm is None else round(wm * 12, 1), "n": wn}
        if wm is not None:
            print(f"  {w}: {wm*12:+.1f}%/yr (t={wm/wse:+.2f}, n={wn})")

    band = (2.0, 4.0)
    detected = bool(ann is not None and ann > 0 and (m / se) > 1.0)
    verdict = ("DETECTED — pipeline validated" if detected
               else "NOT detected — pipeline suspect OR effect absent post-costs")
    print(f"\npre-registered band {band}%/yr · verdict: {verdict}")
    date_s = datetime.now(timezone.utc).date().isoformat()
    (REPO / "reports" / f"equity-round-zero-{date_s}.json").write_text(json.dumps({
        "date": date_s, "effect": "cross-sectional 12-1 momentum, long-only tilt",
        "survivorship_corrected": True, "delisting_haircut": HAIRCUT,
        "pooled": {"excess_mo_pct": None if m is None else round(m, 3),
                   "t": None if (m is None or not se) else round(m / se, 2),
                   "ann_pct": None if ann is None else round(ann, 1), "n": n},
        "by_window": per, "prereg_band_pct_yr": band, "detected": detected,
        "verdict": verdict}, indent=2) + "\n")
    print("wrote report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
