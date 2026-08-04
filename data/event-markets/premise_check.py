"""SPEC §1.5 — text-intersection premise check (BLOCKING, pre-build).

Measures the OUTCOME (governing) and MENTION intersections between the Charter-T
8-K company universe and Kalshi's CATEGORY-SCOPED series. Uses the /series
endpoint (which carries `category`; the bulk /markets list returns it null), so
sports/entertainment false positives are excluded by category — not guessed.
Liquidity proxy = a series with ≥1 two-sided-quoted open market (volume/liquidity
fields are null in the list endpoint; the bid/ask IS populated). Measurement
only — no orders, no collection loop.

Frozen pre-reg (747b3a46e): OUTCOME governs; P5a 0–3/month; P5b tens/quarter;
bar 8 OUTCOME events/quarter. This runs AFTER that freeze.
"""
from __future__ import annotations

import re
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "venues" / "kalshi"))
from adapter import fetch_series, fetch_series_markets  # noqa: E402

EDGAR_DB = REPO / "feeds" / "edgar_8k" / "filings.db"
OUTCOME_CATS = {"Companies"}   # governing column: company-specific, event-resolving
MENTION_CATS = {"Mentions"}    # phrase-said (earnings-call language) markets
STOP = {"the", "inc", "corp", "corporation", "company", "co", "ltd", "plc",
        "holdings", "group", "trust", "fund", "capital", "partners", "llc",
        "international", "technologies", "systems", "financial", "energy", "and"}


def core_name(company):
    if not company:
        return None
    toks = [re.sub(r"[^a-z0-9]", "", t.lower()) for t in company.split()]
    toks = [t for t in toks if t and t not in STOP and len(t) >= 4]
    return toks[0] if toks else None


def edgar_companies():
    con = sqlite3.connect(EDGAR_DB)
    rows = con.execute("SELECT DISTINCT ticker, company FROM filings "
                       "WHERE ticker IS NOT NULL").fetchall()
    con.close()
    out = {}
    for ticker, company in rows:
        cn = core_name(company)
        if cn:
            out.setdefault(cn, (ticker, company))
    return out


def main():
    comps = edgar_companies()
    comp_names = set(comps)
    print(f"8-K archive: {len(comps)} tickered companies (core names)", flush=True)
    series = fetch_series()
    cats = Counter(s["category"] for s in series)
    print(f"Kalshi series: {len(series)} | categories: {dict(cats.most_common(8))}",
          flush=True)
    tok = re.compile(r"[a-z0-9]+")

    for label, wanted in [("OUTCOME (GOVERNING)", OUTCOME_CATS), ("MENTION", MENTION_CATS)]:
        pool = [s for s in series if s.get("category") in wanted]
        matches = [(sorted(m)[0], s) for s in pool
                   if (m := set(tok.findall((s.get("title") or "").lower())) & comp_names)]
        liq = []
        for cn, s in matches:
            active = [x for x in fetch_series_markets(s["ticker"]) if x["two_sided"]]
            if active:
                liq.append((cn, s, len(active)))
            time.sleep(0.03)
        print(f"\n=== {label}: {len(pool)} series in category · "
              f"{len(matches)} match an 8-K company · "
              f"{len(liq)} of those have ≥1 liquid market "
              f"({sum(x[2] for x in liq)} liquid markets) ===", flush=True)
        for cn, s, na in sorted(liq, key=lambda x: -x[2])[:12]:
            print(f"    {comps[cn][0]:6} {(s.get('title') or '')[:52]:52} {na} active mkts")
        if not liq:
            print("    (none liquid)")

    print("\nNOTE: Kalshi only (Polymarket adapter unbuilt). §5 reading is on the "
          "OUTCOME (governing) LIQUID count vs the 8/quarter bar. Stock-vs-flow "
          "caveat: these are currently-open series; the events/quarter flow follows "
          "from their resolution cadence (a small stock => a small flow).")


if __name__ == "__main__":
    raise SystemExit(main())
