# VPS cron — installation & operation

The project's 5-minute cron runs here on a Hetzner CX22 VPS, not on
GitHub Actions. See decision-log entry 2026-05-23 for why (GitHub
free-tier `*/5` cron delivered ~4% of expected invocations; the 95%
uptime gate was unachievable on it).

This directory holds the cron machinery:

| File | Purpose |
| --- | --- |
| `cron-fetch.sh` | The pipeline system cron invokes every 5 min |
| `crontab.txt` | The crontab line for the `trader` user |
| `logs/` | Per-day (`cron-YYYY-MM-DD.log`) + master (`cron-master.log`) logs |

## What `cron-fetch.sh` does

Full surface pipeline, matching what the old GitHub Actions workflow
ran (this is the important part — it's not just `fetch.py`):

1. `git pull --rebase` — receive operator commits
2. `fetch.py --minutes=90` — write bars + a `runs` row (`kind='cron'`)
3. `render_index.py` — regenerate `INDEX.md`
4. `scripts/generate_surface.py` — regenerate `surface/surface.json`
   and `surface/punch_list.json` (and cache-bust `surface/index.html`)
5. commit `trader.db` + `INDEX.md` + the two surface JSONs +
   `surface/index.html`, then push (with pull-rebase retry)

Steps 3–4 run even when `fetch.py` fails, so the surface reflects the
failure honestly. The script exits non-zero only when `fetch.py`
itself failed (a failed push is recoverable next run).

## First-time install (on the VPS, as `trader`)

```bash
cd ~/algotrading-paper
git pull                          # receive the vps/ directory
chmod +x vps/cron-fetch.sh
mkdir -p vps/logs

# Test once manually before installing the cron entry:
./vps/cron-fetch.sh
# Expect: pull → fetch → render → generate → commit → push.
# Confirm a new commit appears on GitHub before continuing.

# Install the schedule:
crontab -e
# paste the line from vps/crontab.txt, save
crontab -l                        # verify the */5 entry is present
```

## Verify it's running

```bash
sudo systemctl status cron        # should be active (running)
tail -f vps/logs/cron-master.log  # watch ~15 min for ~3 runs
```

In the runs table (locally, after `git pull`):

```bash
sqlite3 trader.db \
  "SELECT started_at, status, kind FROM runs WHERE kind='cron' ORDER BY id DESC LIMIT 10;"
```

Recent rows should be ~5 min apart, all `status='ok'`.

## Updating the scripts

The VPS tracks `main`. To pick up changes to `cron-fetch.sh` or any
project code, just `git pull` on the VPS — the next cron run uses the
updated files. No other action needed. (The cron itself does a
`git pull` at the start of every run, so updates land automatically
within one cycle.)

## Debugging

**Cron isn't firing:**
- `sudo systemctl status cron` — must be active
- `crontab -l` — must show the `*/5` entry
- `vps/logs/cron-master.log` — last lines show the most recent attempt

**Cron fires, `fetch.py` fails:**
- `cat .env` — all four credentials present and readable (`chmod 600`)
- `vps/logs/cron-YYYY-MM-DD.log` — the Python traceback
- The `runs` table will have a `status='failed'` row with `error_text`

**Cron fires, fetch ok, push fails:**
- `ssh -T git@github.com` — expect "Hi pwysocan-droid! You've
  successfully authenticated"
- Confirm the GitHub deploy key has **Allow write access**
- The data is safe — committed locally; the next run retries the push

## Relationship to GitHub Actions

`.github/workflows/fetch-and-commit.yml` still exists but its
`schedule:` trigger is disabled (commented out). It remains
`workflow_dispatch`-able for a manual one-off fetch or if the VPS ever
needs to be bypassed. Re-enabling the GitHub schedule is a matter of
uncommenting the `schedule:` block — but per decision-log 2026-05-23,
that platform can't clear the uptime gate, so don't, except as a
temporary fallback during VPS downtime.
