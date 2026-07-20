"""E1' — point-in-time, survivorship-corrected equity sky re-score.

Rebuilds the cross-sectional signal WITHOUT look-ahead: at each monthly
formation date the investable set is ranked by trailing-60-day dollar
volume from bars <= that date (liquidity screen, decision-log 2026-07-20),
delisted names included, mid-hold delistings exited at last close −30%
(Shumway involuntary convention). Reports per-window AND pooled t, beside
the survivor-biased equity-sky-check for comparison.
"""
from __future__ import annotations

import bisect
import json
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "equities.db"
WINDOWS = {
    "2016-2019": ("2016-01-01", "2020-01-01"),
    "2020-2021": ("2020-01-01", "2022-01-01"),
    "2022": ("2022-01-01", "2023-01-01"),
    "2023": ("2023-01-01", "2024-01-01"),
    "2024-2026": ("2024-01-01", "2026-07-01"),
}
M, TOPN, HAIRCUT = 21, 500, 0.30


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
    data = {s: v for s, v in data.items() if len(v[0]) >= 170}
    print(f"{len(data)} symbols with usable history (survivorship-corrected)")
    global_days = sorted({d for v in data.values() for d in v[0]})

    out, pooled_cs, pooled_dir = {}, [], []
    for wname, (a, b) in WINDOWS.items():
        anchors = [d for d in global_days if a <= d < b][::M]
        if len(anchors) < 8:
            out[wname] = {"note": "insufficient anchors"}
            continue
        spreads, dir_rets = [], []
        for D in anchors[7:]:
            cutoff = (date.fromisoformat(D) - timedelta(days=7)).isoformat()
            scored = []
            for sym, (days, closes, vols) in data.items():
                j = bisect.bisect_right(days, D) - 1
                if j < 147 or days[j] < cutoff:      # not trading at D -> excluded
                    continue
                if closes[j - 147] <= 0 or closes[j] <= 0:
                    continue
                dv = sum(closes[j - k] * vols[j - k] for k in range(60))
                mom = closes[j - 21] / closes[j - 147] - 1.0
                if j + 21 < len(days):
                    fwd = closes[j + 21] / closes[j] - 1.0
                else:                                 # delisted mid-hold
                    fwd = (closes[-1] * (1 - HAIRCUT)) / closes[j] - 1.0
                scored.append((dv, mom, fwd))
            if len(scored) < 100:
                continue
            scored.sort(key=lambda t: -t[0])
            top = scored[:TOPN]
            top.sort(key=lambda t: t[1])
            dec = max(1, len(top) // 10)
            lo = sum(t[2] for t in top[:dec]) / dec
            hi = sum(t[2] for t in top[-dec:]) / dec
            spreads.append((hi - lo) * 100)
            dir_rets += [(1.0 if t[1] > 0 else -1.0) * t[2] * 100 for t in top]
        m_cs, se_cs, n_cs = mean_se(spreads)
        m_dir, se_dir, n_dir = mean_se(dir_rets)
        pooled_cs += spreads
        out[wname] = {
            "cs_6_1_spread_pct_mo": None if m_cs is None else round(m_cs, 2),
            "cs_se": None if se_cs is None else round(se_cs, 2),
            "cs_t": None if (m_cs is None or not se_cs) else round(m_cs / se_cs, 2),
            "n_months": n_cs,
            "directional_mean_pct": None if m_dir is None else round(m_dir, 3),
        }
        if m_cs is not None:
            print(f"{wname}: CS 6-1 {m_cs:+.2f}%±{se_cs:.2f}/mo "
                  f"(t={m_cs/se_cs:+.2f}, n={n_cs})")

    pm, pse, pn = mean_se(pooled_cs)
    pooled = {"cs_spread_pct_mo": None if pm is None else round(pm, 2),
              "se": None if pse is None else round(pse, 2),
              "t": None if (pm is None or not pse) else round(pm / pse, 2),
              "n_months": pn}
    if pm is not None:
        print(f"\nPOOLED CS 6-1: {pm:+.2f}%±{pse:.2f}/mo · t={pm/pse:+.2f} · n={pn}")

    date_s = datetime.now(timezone.utc).date().isoformat()
    (REPO / "reports" / f"equity-sky-pit-{date_s}.json").write_text(json.dumps({
        "date": date_s, "survivorship_corrected": True,
        "delisting_haircut": HAIRCUT, "universe": "trailing-60d $vol top %d" % TOPN,
        "windows": out, "pooled_cross_sectional": pooled}, indent=2) + "\n")
    print("wrote report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
