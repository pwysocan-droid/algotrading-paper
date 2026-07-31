"""SEC EDGAR full-text-search adapter — Charter T forward-only collection.

COLLECTION ONLY. Fetches published 8-K filing *metadata* from the public
efts.sec.gov API (SEC asks for a descriptive User-Agent). This module must never
gain hypothesis logic, signal computation, or trading code — the Charter T
pre-reg (book/pre-reg-charter-T.md) authorizes ingestion and nothing else.
"""
from __future__ import annotations

import re

import requests

BASE = "https://efts.sec.gov/LATEST/search-index"
UA = {"User-Agent": "algotrading-paper research (pwysocan@gmail.com)"}


def _parse_display(names):
    """['ExxonMobil ... (XOM) (CIK 000...)'] -> ('ExxonMobil ...', 'XOM')."""
    if not names:
        return None, None
    s = names[0]
    m = re.search(r"\(([A-Z][A-Z.\-]{0,5})\)\s*\(CIK", s)
    ticker = m.group(1) if m else None
    company = s.split("(")[0].strip() or None
    return company, ticker


def fetch_8k(startdt, enddt, max_pages=60, session=None):
    """8-K filings in [startdt, enddt] (YYYY-MM-DD). Paginates efts (100/page)."""
    s = session or requests.Session()
    out = []
    for pg in range(max_pages):
        r = s.get(BASE, params={"forms": "8-K", "startdt": startdt,
                                "enddt": enddt, "from": pg * 100},
                  headers=UA, timeout=25)
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])
        if not hits:
            break
        for h in hits:
            src = h.get("_source", {})
            company, ticker = _parse_display(src.get("display_names"))
            items = src.get("items")
            out.append({
                "adsh": src.get("adsh") or h.get("_id", "").split(":")[0],
                "cik": (src.get("ciks") or [None])[0],
                "company": company, "ticker": ticker,
                "form": src.get("form"), "file_date": src.get("file_date"),
                "items": ";".join(items) if isinstance(items, list) else items,
                "sic": (src.get("sics") or [None])[0],
            })
        if len(hits) < 100:
            break
    return out
