"""Charter T (EDGAR 8-K) ingestion — parsing, schema contract, and gap detection.
No network. Locks the data-contract logic that must fail loudly on holes."""
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

FEED = Path(__file__).resolve().parent.parent / "feeds" / "edgar_8k"
sys.path.insert(0, str(FEED))
import adapter  # noqa: E402
import ingest  # noqa: E402


def test_parse_display_extracts_company_and_ticker():
    c, t = adapter._parse_display(["ExxonMobil Holdings Corp  (XOM)  (CIK 0002115436)"])
    assert c == "ExxonMobil Holdings Corp" and t == "XOM"
    c2, t2 = adapter._parse_display(["Some Private Filer LLC  (CIK 0001234567)"])
    assert t2 is None and "Some Private Filer" in c2
    assert adapter._parse_display([]) == (None, None)


def test_schema_failures_counts_missing_required():
    rows = [
        {"adsh": "a", "form": "8-K", "file_date": "2026-07-31"},   # ok
        {"adsh": "b", "form": "8-K"},                               # missing file_date
        {"form": "8-K", "file_date": "2026-07-31"},                # missing adsh
    ]
    assert ingest.schema_failures(rows) == 2


def _seed(db, ingested_at, status="OK", nrows=1):
    con = sqlite3.connect(db)
    con.executescript(ingest.SCHEMA)
    con.execute("INSERT OR REPLACE INTO ingest_log VALUES (?,?,?,?,?,?,?,?)",
                (ingested_at, "edgar_8k", "2026-07-28", "2026-07-31", 10, nrows, status, ""))
    con.execute("INSERT OR IGNORE INTO filings VALUES (?,?,?,?,?,?,?,?,?)",
                ("acc1", "1", "Co", "CO", "8-K", "2026-07-31", "2.02", "1234", ingested_at))
    con.commit()
    con.close()


def test_health_fresh_ok(tmp_path):
    db = tmp_path / "filings.db"
    _seed(db, datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    h = ingest.health(db=db)
    assert h["status"] == "OK" and h["total"] == 1 and h["age_days"] == 0


def test_health_flags_stale_gap(tmp_path):
    db = tmp_path / "filings.db"
    old = (datetime.now(timezone.utc) - timedelta(days=10)).replace(microsecond=0).isoformat()
    _seed(db, old)
    h = ingest.health(db=db, gap_days=2)
    assert h["status"] == "STALE" and "gap" in h["note"]


def test_health_none_when_absent(tmp_path):
    assert ingest.health(db=tmp_path / "nope.db") is None
