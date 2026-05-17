-- Disambiguate the source of each runs row so the curriculum-start anchor
-- and any future uptime / failure-rate analysis can filter to genuine
-- cron-scheduled runs (vs. manual backfills, ad-hoc fetches, or replay
-- harness invocations that also write to the runs table).
--
-- Default 'cron' covers future inserts from .github/workflows/fetch-and-commit.yml
-- without any code change there. fetch.py grows a --kind CLI flag so manual
-- invocations can set 'manual' or 'backfill' explicitly.
--
-- Existing rows at migration time get UPDATEd to 'backfill':
--   - run id 1: the 41,656-bar 30-day backfill on 2026-05-03T00:10:06Z
--     (BTC/ETH/SOL/LINK/AVAX, 2026-04-03 → 2026-05-03).
-- If any cron rows had been inserted before this migration, the UPDATE
-- WHERE clause leaves them as 'cron' (the column default). The id list
-- below is the authoritative record of what was reclassified.

ALTER TABLE runs ADD COLUMN kind TEXT NOT NULL DEFAULT 'cron';
UPDATE runs SET kind = 'backfill' WHERE id IN (1);
