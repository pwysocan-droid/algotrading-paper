"""Append new EDGAR 8-K filings to a LOCAL gitignored DB, with data contracts.

Forward-only (dedup by accession `adsh`), single-writer, own DB file — raw data
is NEVER committed (disk-bloat lesson). Data contracts (schema / row-count /
gap) are recorded every run and surfaced loudly in the daily digest, because a
forward-only archive with silent holes is unusable and unfixable after the fact
(the max_pages lesson, applied prospectively).
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from adapter import fetch_8k  # noqa: E402

DB = HERE / "filings.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS filings(
  adsh TEXT PRIMARY KEY, cik TEXT, company TEXT, ticker TEXT,
  form TEXT, file_date TEXT, items TEXT, sic TEXT, ingested_at TEXT);
CREATE TABLE IF NOT EXISTS ingest_log(
  ingested_at TEXT PRIMARY KEY, source TEXT, window_start TEXT, window_end TEXT,
  fetched INTEGER, new_rows INTEGER, status TEXT, note TEXT);
"""
REQUIRED = ("adsh", "form", "file_date")


def schema_failures(rows):
    return sum(1 for r in rows if not all(r.get(k) for k in REQUIRED))


def ingest(days_back=3, db=DB):
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days_back)

    def log(fetched, new, status, note):
        con.execute("INSERT OR REPLACE INTO ingest_log VALUES (?,?,?,?,?,?,?,?)",
                    (ts, "edgar_8k", start.isoformat(), end.isoformat(),
                     fetched, new, status, note))
        con.commit()

    try:
        rows = fetch_8k(start.isoformat(), end.isoformat())
    except Exception as exc:  # noqa: BLE001
        log(0, 0, "FAIL", f"fetch error: {type(exc).__name__}")
        con.close()
        raise

    bad = schema_failures(rows)
    new = 0
    for r in rows:
        if not all(r.get(k) for k in REQUIRED):
            continue
        new += con.execute(
            "INSERT OR IGNORE INTO filings VALUES (?,?,?,?,?,?,?,?,?)",
            (r["adsh"], r.get("cik"), r.get("company"), r.get("ticker"),
             r["form"], r["file_date"], r.get("items"), r.get("sic"), ts)).rowcount

    if bad:
        status, note = "FAIL", f"{bad}/{len(rows)} rows failed schema check"
    elif not rows:
        status, note = "FAIL", "0 rows fetched (weekday window — source outage?)"
    else:
        status, note = "OK", ""
    log(len(rows), new, status, note)
    con.close()
    return {"fetched": len(rows), "new": new, "status": status, "note": note}


def health(db=DB, gap_days=2):
    """Data-contract health for the digest: last ingest, totals, gap detection.
    Returns None if the archive doesn't exist yet."""
    if not Path(db).exists():
        return None
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        last = con.execute(
            "SELECT * FROM ingest_log ORDER BY ingested_at DESC LIMIT 1").fetchone()
        total = con.execute("SELECT count(*) FROM filings").fetchone()[0]
        maxd = con.execute("SELECT max(file_date) FROM filings").fetchone()[0]
    except sqlite3.OperationalError:
        con.close()
        return None
    con.close()
    if not last:
        return {"status": "NO_INGEST", "total": total}
    last_day = last["ingested_at"][:10]
    age = (datetime.now(timezone.utc).date()
           - datetime.fromisoformat(last_day).date()).days
    contract = last["status"]
    if contract == "OK" and age > gap_days:
        contract, note = "STALE", f"no ingest in {age}d (gap>{gap_days})"
    else:
        note = last["note"]
    return {"status": contract, "total": total, "new_last": last["new_rows"],
            "last_ingest": last_day, "max_file_date": maxd, "age_days": age,
            "note": note}


if __name__ == "__main__":
    print("edgar_8k ingest:", ingest())
