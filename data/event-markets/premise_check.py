"""SPEC §1.5 — text-intersection premise check (BLOCKING, pre-build).

Measures |Charter-T 8-K companies ∩ liquid Kalshi markets|: how many companies
with material-event filings also have a LIQUID, tradeable event market whose
price could benchmark a text signal. Measurement only — no collection loop, no
orders. Kalshi only for now (Polymarket adapter not built; flagged as a gap).

Pre-named readings (SPEC §1.5): intersection >= bar -> §5 live; < bar -> §5
DORMANT (tape survives on the W3 duel screen alone). Reports events/month +
examples; the operator pins the bar.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "venues" / "kalshi"))
sys.path.insert(0, str(REPO / "feeds" / "edgar_8k"))
from adapter import fetch_markets  # noqa: E402  (Kalshi)

EDGAR_DB = REPO / "feeds" / "edgar_8k" / "filings.db"
LIQ_FLOORS = [0, 100, 1000]   # liquidity_dollars floors to report robustness
STOP = {"the", "inc", "corp", "corporation", "company", "co", "ltd", "plc",
        "holdings", "group", "trust", "fund", "capital", "partners", "llc",
        "international", "technologies", "systems", "financial", "energy"}


def core_name(company: str) -> str | None:
    """Distinctive lowercase token of a company name (e.g. 'Tesla Inc' -> tesla)."""
    if not company:
        return None
    toks = [re.sub(r"[^a-z0-9]", "", t.lower()) for t in company.split()]
    toks = [t for t in toks if t and t not in STOP and len(t) >= 4]
    return toks[0] if toks else None


def edgar_companies():
    """(core_name -> (ticker, company)) for 8-K filers that carry a ticker."""
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
    print(f"8-K archive: {len(comps)} distinct tickered companies (core names)")
    markets = fetch_markets(status="open", max_pages=800)
    print(f"Kalshi open markets fetched: {len(markets)}")

    # match Kalshi titles against 8-K company core names (word-boundary)
    patt = re.compile(r"\b(" + "|".join(re.escape(c) for c in comps) + r")\b", re.I) \
        if comps else None
    # outcome-market vs mention-market split (reviewer): a MENTION references the
    # company; an OUTCOME market resolves on a company EVENT (the real benchmark
    # for an 8-K text signal). Heuristic: event keywords near the company vs a
    # generic price-level market.
    event_kw = re.compile(
        r"\b(earnings|eps|revenue|report|guidance|acquir|merger|buyout|takeover|"
        r"launch|unveil|announc|approv|fda|recall|ceo|resign|bankrupt|delist|"
        r"dividend|split|ipo|layoff|deliver|subscribers)\b", re.I)
    hits = {}   # core_name -> list of (title, liquidity, volume, is_outcome)
    for m in markets:
        title = (m.get("title") or "")
        if not patt:
            break
        found = patt.search(title.lower())
        if not found:
            continue
        cn = found.group(1).lower()
        is_outcome = bool(event_kw.search(title))
        hits.setdefault(cn, []).append(
            (title, m.get("liquidity") or 0, m.get("volume") or 0, is_outcome))

    print("\n=== intersection by liquidity floor — MENTION vs OUTCOME markets ===")
    for floor in LIQ_FLOORS:
        men_co = {cn for cn, ms in hits.items() if any(l >= floor for _, l, _, _ in ms)}
        men_mk = sum(1 for ms in hits.values() for _, l, _, _ in ms if l >= floor)
        out_co = {cn for cn, ms in hits.items()
                  if any(l >= floor and o for _, l, _, o in ms)}
        out_mk = sum(1 for ms in hits.values() for _, l, _, o in ms if l >= floor and o)
        print(f"  floor ${floor:>4}: MENTION {len(men_co)} co / {men_mk} mkts  |  "
              f"OUTCOME {len(out_co)} co / {out_mk} mkts  (outcome = the real benchmark)")

    print("\n=== examples ([O]=outcome-market, [m]=mention-only) ===")
    shown = 0
    for cn, ms in sorted(hits.items(), key=lambda kv: -max(x[1] or 0 for x in kv[1])):
        ticker, company = comps[cn]
        best = max(ms, key=lambda x: x[1] or 0)
        tag = "O" if best[3] else "m"
        print(f"  [{tag}] {ticker:6} {company[:26]:26} liq ${best[1] or 0:>7.0f} | {best[0][:56]}")
        shown += 1
        if shown >= 20:
            break
    if not hits:
        print("  (none — no 8-K company appears in any open Kalshi market title)")
    print("\nNOTE: Kalshi only (Polymarket adapter unbuilt). Company-name match is "
          "coarse; examples are for eyeballing false positives. The bar and the "
          "§5-live/dormant reading are the operator's per SPEC §1.5.")


if __name__ == "__main__":
    raise SystemExit(main())
