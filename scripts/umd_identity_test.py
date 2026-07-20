"""E2 round-zero — identity test: is the measured object actually momentum?

Two cheap decisive checks (decision-log 2026-07-20 referee): the +0.26
full-sample correlation caps the crash-signature's force, so grade them
together, not separately.

  1. MIMIC UMD. Rebuild a value-weighted long-short 2x3 momentum spread
     (2-12 formation, 30/70 breakpoints, coarse size split, dollar
     volume as the size/weight proxy — no true market cap available) on
     the same 59 months. If corr(mimic, French UMD) jumps to ~0.6-0.8,
     the benign construction+calendar explanation is confirmed and the
     crash signature regains full weight. If it stays ~0.3 under a
     matched construction, something structural is wrong — caught on
     day zero, before any real spec runs.
  2. CONDITIONAL correlation. The crash claim lives in tail months; a
     full-sample corr is dominated by calm ones. Correlate the original
     long-only tilt vs UMD on the high-|UMD| months vs the calm months.
     Strong tail + weak calm co-movement SUPPORTS the verdict (same
     beast in storms).
"""
from __future__ import annotations

import bisect
import io
import json
import re
import sqlite3
import sys
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "equities.db"
M, TOPN, DECILE, HAIRCUT, LOOKBACK = 21, 500, 0.10, 0.30, 252
FRENCH = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/"
          "ftp/F-F_Momentum_Factor_CSV.zip")


def _pct(sorted_vals, q):
    return sorted_vals[min(len(sorted_vals) - 1, int(len(sorted_vals) * q))]


def series() -> tuple[dict, dict]:
    """(tilt_by_month, umd_mimic_by_month), both in %/month."""
    conn = sqlite3.connect(DB)
    data: dict = {}
    for sym, day, close, vol in conn.execute(
            "SELECT symbol, day, close, volume FROM daily_bars ORDER BY symbol, day"):
        d = data.setdefault(sym, ([], [], []))
        d[0].append(day); d[1].append(close); d[2].append(vol)
    data = {s: v for s, v in data.items() if len(v[0]) >= LOOKBACK + 25}
    gdays = sorted({d for v in data.values() for d in v[0]})
    tilt, mimic = {}, {}
    for D in gdays[LOOKBACK::M]:
        cutoff = (date.fromisoformat(D) - timedelta(days=7)).isoformat()
        rows = []
        for sym, (days, closes, vols) in data.items():
            j = bisect.bisect_right(days, D) - 1
            if j < LOOKBACK or days[j] < cutoff or closes[j - LOOKBACK] <= 0 or closes[j] <= 0:
                continue
            dv = sum(closes[j - k] * vols[j - k] for k in range(60))
            mom = closes[j - 21] / closes[j - LOOKBACK] - 1.0
            fwd = (closes[j + 21] / closes[j] - 1.0) if j + 21 < len(days) \
                else (closes[-1] * (1 - HAIRCUT)) / closes[j] - 1.0
            rows.append((dv, mom, fwd))
        if len(rows) < 100:
            continue
        rows.sort(key=lambda t: -t[0])
        univ = rows[:TOPN]
        # --- original long-only tilt (top-decile EW minus universe EW)
        bench = sum(t[2] for t in univ) / len(univ)
        by_mom = sorted(univ, key=lambda t: t[1])
        k = max(1, int(len(univ) * DECILE))
        tilt[D[:7]] = (sum(t[2] for t in by_mom[-k:]) / k - bench) * 100.0
        # --- UMD mimic: VW long-short 2x3 (big/small x high/low), 30/70
        dv_med = sorted(t[0] for t in univ)[len(univ) // 2]
        moms = sorted(t[1] for t in univ)
        p30, p70 = _pct(moms, 0.30), _pct(moms, 0.70)

        def vw(group):
            s = sum(t[0] for t in group)
            return sum(t[0] * t[2] for t in group) / s if s else None
        legs = {}
        for size, sel in (("big", lambda t: t[0] >= dv_med),
                          ("small", lambda t: t[0] < dv_med)):
            g = [t for t in univ if sel(t)]
            hi = [t for t in g if t[1] >= p70]
            lo = [t for t in g if t[1] <= p30]
            legs[size + "H"], legs[size + "L"] = vw(hi), vw(lo)
        if None not in legs.values():
            mimic[D[:7]] = (0.5 * (legs["bigH"] + legs["smallH"])
                            - 0.5 * (legs["bigL"] + legs["smallL"])) * 100.0
    return tilt, mimic


def french_umd() -> dict:
    raw = urllib.request.urlopen(FRENCH, timeout=60).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    txt = z.read(z.namelist()[0]).decode("latin-1")
    out = {}
    for line in txt.splitlines():
        m = re.match(r"^\s*(\d{6}),\s*(-?\d+\.\d+)\s*$", line)
        if m:
            out[f"{m.group(1)[:4]}-{m.group(1)[4:]}"] = float(m.group(2))
    return out


def corr(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (sx * sy) if sx and sy else None


def main() -> int:
    tilt, mimic = series()
    umd = french_umd()

    # 1. mimic vs French, full overlap
    ov_m = sorted(set(mimic) & set(umd))
    r_mimic = corr([mimic[m] for m in ov_m], [umd[m] for m in ov_m])
    # baseline: original tilt vs French, full
    ov_t = sorted(set(tilt) & set(umd))
    r_tilt_full = corr([tilt[m] for m in ov_t], [umd[m] for m in ov_t])

    # 2. conditional: storm (top 20% |UMD|) vs calm
    ranked = sorted(ov_t, key=lambda m: -abs(umd[m]))
    ns = max(3, int(len(ranked) * 0.20))
    storm, calm = set(ranked[:ns]), set(ranked[ns:])
    r_storm = corr([tilt[m] for m in ov_t if m in storm],
                   [umd[m] for m in ov_t if m in storm])
    r_calm = corr([tilt[m] for m in ov_t if m in calm],
                  [umd[m] for m in ov_t if m in calm])

    print(f"1. UMD-mimic (VW long-short 2x3) vs French UMD: r={r_mimic:+.2f} "
          f"(n={len(ov_m)})  [~0.6-0.8 => construction explains the gap]")
    print(f"   original tilt vs French, full: r={r_tilt_full:+.2f}")
    print(f"2. tilt vs UMD  storm months (top20% |UMD|, n={ns}): r={r_storm:+.2f}"
          f"  ·  calm months: r={r_calm:+.2f}")
    print("   [strong storm + weak calm SUPPORTS the crash-signature verdict]")

    date_s = datetime.now(timezone.utc).date().isoformat()
    (REPO / "reports" / f"umd-identity-{date_s}.json").write_text(json.dumps({
        "date": date_s,
        "mimic_vs_french_r": None if r_mimic is None else round(r_mimic, 3),
        "tilt_vs_french_full_r": None if r_tilt_full is None else round(r_tilt_full, 3),
        "tilt_vs_umd_storm_r": None if r_storm is None else round(r_storm, 3),
        "tilt_vs_umd_calm_r": None if r_calm is None else round(r_calm, 3),
        "storm_n": ns, "overlap_n": len(ov_t)}, indent=2) + "\n")
    print("wrote report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
