"""SEC EDGAR full-text-search adapter — Charter T forward-only collection.

COLLECTION ONLY. Fetches published 8-K filing *metadata* from the public
efts.sec.gov API (SEC asks for a descriptive User-Agent). This module must never
gain hypothesis logic, signal computation, or trading code — the Charter T
pre-reg (book/pre-reg-charter-T.md) authorizes ingestion and nothing else.
"""
from __future__ import annotations

import re
import time

import requests

# EDGAR occasionally returns a momentary 429/5xx or times out (~1-2x/week). Retry
# those with capped backoff so a blip doesn't fail the day's ingest; a permanent
# 4xx raises immediately, and a sustained outage still surfaces as FAIL after the
# retries are spent (the data contract must still catch a real outage).
_TRANSIENT = {429, 500, 502, 503, 504}


def _get(s, params, retries=4):
    for attempt in range(retries + 1):
        try:
            r = s.get(BASE, params=params, headers=UA, timeout=25)
        except (requests.ConnectionError, requests.Timeout):
            if attempt < retries:
                time.sleep(min(2 ** attempt, 8)); continue
            raise
        if r.status_code in _TRANSIENT and attempt < retries:
            time.sleep(min(2 ** attempt, 8)); continue
        r.raise_for_status()
        return r

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
        r = _get(s, {"forms": "8-K", "startdt": startdt, "enddt": enddt, "from": pg * 100})
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
