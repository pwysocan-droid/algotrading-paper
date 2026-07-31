# Charter T archive — birth certificate

- **Source:** SEC EDGAR 8-K filing metadata (efts.sec.gov full-text search).
- **Collection start:** 2026-07-31 (UTC). The precise moment is the first row of
  `ingest_log` in the (gitignored, VPS-local) `filings.db`.

Every Charter T sub-hypothesis inherits this as its **"forward-only from" line**:
no 8-K dated before 2026-07-31 may serve as an in-sample signal — the archive
begins here; only filings ingested on/after this date are forward-only evidence.

Raw `filings.db` is gitignored (local, single-writer). Data-contract health
(schema / row-count / gap) is surfaced daily in the digest. Discipline for any
sub-hypothesis: `book/pre-reg-charter-T.md`.
