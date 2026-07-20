"""E2 round-zero validation against the gold standard — Ken French UMD.

Recomputes the pipeline's monthly long-only-tilt excess series and
correlates it with Ken French's UMD momentum factor (1927-present, CRSP
delisting-handled) over the overlap. High correlation validates our
portfolio CONSTRUCTION independent of magnitude; the long French series
places 2021-26 within the 99-year momentum distribution. Free download,
no LLM cost (decision-log 2026-07-20 round-zero amendments).
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
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "equities.db"
M, TOPN, DECILE, HAIRCUT, LOOKBACK = 21, 500, 0.10, 0.30, 252
FRENCH = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/"
          "ftp/F-F_Momentum_Factor_CSV.zip")


def pipeline_monthly() -> dict[str, float]:
    """{ 'YYYY-MM': excess_pct } — the tilt-over-benchmark series."""
    conn = sqlite3.connect(DB)
    data: dict = {}
    for sym, day, close, vol in conn.execute(
            "SELECT symbol, day, close, volume FROM daily_bars ORDER BY symbol, day"):
        d = data.setdefault(sym, ([], [], []))
        d[0].append(day); d[1].append(close); d[2].append(vol)
    data = {s: v for s, v in data.items() if len(v[0]) >= LOOKBACK + 25}
    gdays = sorted({d for v in data.values() for d in v[0]})
    out = {}
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
        bench = sum(t[2] for t in univ) / len(univ)
        univ.sort(key=lambda t: t[1])
        k = max(1, int(len(univ) * DECILE))
        top = sum(t[2] for t in univ[-k:]) / k
        out[D[:7]] = (top - bench) * 100.0
    return out


def french_umd() -> dict[str, float]:
    raw = urllib.request.urlopen(FRENCH, timeout=60).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    txt = z.read(z.namelist()[0]).decode("latin-1")
    out = {}
    for line in txt.splitlines():
        m = re.match(r"^\s*(\d{6})\s+(-?\d+\.\d+)\s*$", line)
        if m:
            ym = f"{m.group(1)[:4]}-{m.group(1)[4:]}"
            out[ym] = float(m.group(2))
    return out


def corr(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (sx * sy) if sx and sy else None


def main() -> int:
    pipe = pipeline_monthly()
    umd = french_umd()
    overlap = sorted(set(pipe) & set(umd))
    xs = [pipe[m] for m in overlap]
    ys = [umd[m] for m in overlap]
    r = corr(xs, ys) if len(overlap) > 3 else None
    print(f"overlap {len(overlap)} months; corr(pipeline excess, French UMD) = "
          f"{r:+.2f}" if r is not None else "insufficient overlap")

    hist = list(umd.values())
    hm = sum(hist) / len(hist)
    hsd = (sum((x - hm) ** 2 for x in hist) / (len(hist) - 1)) ** 0.5
    recent = [umd[m] for m in umd if m >= "2021-01"]
    rm = sum(recent) / len(recent)
    z = (rm - hm) / (hsd / len(recent) ** 0.5)
    print(f"French UMD: full-history {hm:+.2f}%/mo (n={len(hist)}, 1927+); "
          f"2021-26 {rm:+.2f}%/mo (z={z:+.2f} vs history)")

    date_s = datetime.now(timezone.utc).date().isoformat()
    (REPO / "reports" / f"umd-crosscheck-{date_s}.json").write_text(json.dumps({
        "date": date_s, "overlap_months": len(overlap),
        "corr_pipeline_vs_french_umd": None if r is None else round(r, 3),
        "french_umd_full_mean_mo": round(hm, 3),
        "french_umd_2021_26_mean_mo": round(rm, 3), "recent_z": round(z, 2),
        "reading": "corr>~0.5 validates construction vs the CRSP gold standard; "
                   "|z|<2 means 2021-26 is within the 99-year momentum distribution"
    }, indent=2) + "\n")
    print("wrote report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
