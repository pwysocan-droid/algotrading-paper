# Setup — algotrading-paper

How to prepare the infrastructure before Claude Code starts building.
This file is the equivalent of the wagon-watcher's `RECON.md` — it
documents the manual setup steps the human owner does before any
code is written.

Time required: 30–60 minutes once.

This file was updated post-reframe (2026-04-26 entry on Claude as
epistemological backbone). Two things changed from the original:
the Anthropic API key moved from Week 7 to pre-flight, and the
canonical file list grew from five to eight.

---

## What needs to exist before code is written

1. An Alpaca paper-trading account
2. An Anthropic API key (moved up by the reframe — was originally
   Week 7)
3. API credentials for both, stored locally (`.env`) and in GitHub
   Actions secrets
4. A new GitHub repository with the right structure
5. The eight canonical project files committed to the repo

If any are missing when Claude Code starts, the build will stall
during Week 1.

---

## Step 1 — Create the Alpaca paper-trading account

1. Go to https://app.alpaca.markets/signup
2. Sign up for an account. Email + password. No KYC required for
   paper trading.
3. After login, switch to the **paper-trading dashboard**:
   `https://app.alpaca.markets/paper/dashboard/overview`
4. Confirm the default starting balance is $100,000 (it should be
   automatic).
5. Navigate to API Keys section
   (`https://app.alpaca.markets/paper/dashboard/overview` → "API
   Keys" in the sidebar)
6. Generate a new key pair. **Save both the key and the secret
   immediately** — the secret will only be shown once.

The paper account is permanent. Even if untouched for months it
won't expire. The $100,000 default balance is more than the
project will ever use; the execution layer enforces $1,000 of
effective exposure regardless.

---

## Step 2 — Generate the Anthropic API key

The reframe moved Claude API integration from Week 7 to Week 1, so
this is now pre-flight rather than deferred.

1. Go to https://console.anthropic.com/
2. Sign in or create an account
3. Settings → API Keys → Create Key
4. **Save the key immediately** — it's shown only once
5. Settings → Billing → set a $50 monthly usage alert

Budget expectation post-reframe: ~$10/wk during Weeks 0–2,
~$15-25/wk Weeks 3–8. The $50 alert is a safety floor, not an
expected cost.

---

## Step 3 — Create the local directory

```bash
# On your machine, in your usual code directory
mkdir algotrading-paper
cd algotrading-paper
git init
```

Don't push anything yet. The local repo gets set up first, then
GitHub gets created and pushed to once the project files and
gitignore are in place.

---

## Step 4 — Drop the eight canonical project files

The five original files plus three added during Week 0:

```
algotrading-paper/
├── PROJECT.md             (the build spec — Claude Code reads this)
├── philosophy.md          (success criteria, animating disciplines)
├── decision-log.md        (decisions made — newest on top)
├── playbook.md            (response procedures for specific situations)
├── setup.md               (this file)
├── week-0-synthesis.md    (Week 0 deliverable: criteria, candidates, audit)
├── report-format-spec.md  (markdown report formats: INDEX, v1/v2 patterns)
└── roadmap.md             (navigational outline + to-do, derived)
```

Plus one input file used by the next session:

```
└── week-1-prompt.md       (the prompt to give Claude Code for Week 1)
```

Note: the claude.ai project knowledge files (philosophy,
decision-log, playbook, etc.) live in BOTH places — the claude.ai
project (so I have them during conversations) and the repo (so
they're version-controlled). When one is updated, update the
other.

The simplest workflow: claude.ai project is the source of truth
during planning conversations. After a session, paste the updated
files into the repo and commit. Once Claude Code is actively
building, the repo becomes the source of truth and the claude.ai
project knowledge gets refreshed by re-uploading from the repo.

---

## Step 5 — Run the pre-flight prompt in Claude Code

Once the eight canonical files plus `week-1-prompt.md` are in the
local directory, open Claude Code in that directory:

```bash
cd algotrading-paper
claude
```

Or open Claude Code and point it at the directory through the UI.

Use the prompt in `preflight-prompt.md` (kept in the repo for
reference, regenerated from claude.ai if needed). The prompt
tells Claude Code to:

1. Initialize the git repo (if not already done)
2. Create `.gitignore` first, with the right entries, and commit
   it before any `.env` file exists
3. Create `.env.template` (a placeholder file) and commit it
4. Verify the gitignore is working using a temporary fake `.env`
   file with dummy contents (deleted after verification)
5. Add the eight canonical project files plus `week-1-prompt.md`
   in an initial-spec commit
6. Stop and report state

Claude Code never sees real API keys in this prompt. The discipline
is: Claude Code does the structural work; the operator handles
secrets. Read `preflight-prompt.md` before pasting it; understand
what Claude Code will do.

---

## Step 6 — Manually create the real `.env`

After Claude Code finishes the pre-flight prompt, the real `.env`
gets created locally — manually, never by Claude Code.

```bash
cp .env.template .env
```

Open `.env` in an editor and replace the placeholder values with
the real keys from password manager:

```
ALPACA_API_KEY=PK1ABC...           (the actual paper key)
ALPACA_SECRET_KEY=xyz...           (the actual paper secret)
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ANTHROPIC_API_KEY=sk-ant-...       (the actual Anthropic key)
```

Save. Do NOT commit. Run `git status` one more time to verify
`.env` doesn't appear:

```bash
git status
```

`.env` should not show up anywhere. If it does, the gitignore is
broken; fix before doing anything else.

This is the single most important step in setup. Committing the
Alpaca or Anthropic secret to a public repo would expose the
credentials. Paper trades are simulated so the financial damage
is bounded for Alpaca, but the account would still be hijacked.
For Anthropic, an exposed key gets used by bots within hours and
the bill is real.

---

## Step 7 — Create the GitHub repository

On github.com:

1. Create a new repository named `algotrading-paper`
2. Choose **public** unless there's a reason for private. Public
   repos let claude.ai `web_fetch` the digest files for
   conversations. None of the data is sensitive — paper trades
   aren't private.
3. Don't initialize with a README, .gitignore, or license; the
   local repo provides everything.

Connect the local repo to the remote and push:

```bash
git remote add origin https://github.com/[your-username]/algotrading-paper.git
git branch -M main
git push -u origin main
```

After the push, **verify on github.com that `.env` does NOT appear
in the file list**. Browse the repo's files; if `.env` is there,
stop and rotate keys immediately. Should not happen if Step 6
was done correctly, but checking is cheap.

---

## Step 8 — Add GitHub Actions secrets

In the GitHub repo: Settings → Secrets and variables → Actions →
New repository secret.

Add four secrets:

- `ALPACA_API_KEY` — same value as in `.env`
- `ALPACA_SECRET_KEY` — same value as in `.env`
- `ALPACA_BASE_URL` — `https://paper-api.alpaca.markets`
- `ANTHROPIC_API_KEY` — same value as in `.env`

These are encrypted at rest and only exposed to GitHub Actions
workflows. They never appear in the public repo or in workflow
logs (GitHub redacts them automatically).

When Phase 2 begins, two secrets get added (`ALPACA_LIVE_API_KEY`,
`ALPACA_LIVE_SECRET_KEY`) and `ALPACA_BASE_URL` gets flipped to
the live URL. That's the one-line config change that earns Phase 2
status. Don't add the live credentials until Phase 2 is gated and
approved.

---

## Cron commit-back pattern

Added 2026-05-17 alongside the decision-log entry that committed the
Phase 1 storage approach (Option A — SQLite-in-repo).

The cron workflow `.github/workflows/fetch-and-commit.yml` runs every
5 minutes. Each run does the full cycle in a single commit:

1. `fetch.py` writes new bars and a `runs` row to `trader.db`
2. `render_index.py` regenerates `INDEX.md` from the current DB state
3. The workflow stages `trader.db` + `INDEX.md`, commits, and pushes
   back to `main`

Consequences to expect:

- **Commit volume.** ~8,064 cron commits per 4 weeks. After Phase 1,
  the git history will be dominated by `fetch run YYYY-MM-DDTHH:MM:SSZ`
  entries. This is auditable, expected, and accepted per decision-log
  2026-05-17. `git log --invert-grep --grep='^fetch run'` filters them
  out when reviewing operator activity.

- **Repo bloat.** ~800MB over Phase 1, well under GitHub's ~5GB
  warning threshold. v2 likely migrates to a remote Postgres
  (Supabase/Neon/Railway via `DATABASE_URL`) and drops the in-repo DB.

- **Operator workflow.** `git pull` before running anything local
  (replay, render_index manually, etc.) so your local `trader.db`
  stays in sync with the cron's writes. If the operator commits
  during a cron run, the cron retries the push 3 times with
  `git pull --rebase` between attempts; if all retries fail, the
  data is safe — the next cron run picks up where this one left off.

- **Failure visibility.** A failed `fetch.py` (Alpaca outage, rate
  limit, network) still writes a `runs` row with `status='failed'`
  and `error_text`. The workflow's `continue-on-error: true` on the
  fetch step means INDEX.md regenerates and the commit happens even
  on failure — so uptime is visible immediately in the four-stat
  band rather than hidden by a missing commit.

- **Anchor side effect.** The curriculum-start anchor in
  `render_index.py` (`get_curriculum_start`) uses the first
  `runs` row with `status='ok'`. The first successful cron run
  starts the 8-week countdown. Re-deploying or wiping `trader.db`
  resets the anchor — don't do this without committing the
  rationale to `decision-log.md` first.

To temporarily pause the cron without removing it, disable the
workflow on github.com: Actions → fetch-and-commit → ··· →
Disable workflow. Re-enable the same way. The decision to pause
gets a `decision-log.md` entry per the project's standing
discipline.

---

## VPS cron architecture

Superseded the GitHub Actions cron on 2026-05-23. See the decision-log
entry of that date for the full reasoning; the short version: GitHub's
free-tier `*/5` schedule delivered ~4% of expected invocations, which
made the Phase 2 95%-uptime gate unachievable. The cron moved to a
Hetzner CX22 VPS ($5.83/mo).

**Where it runs.** A Hetzner CX22 VPS, Ubuntu 24.04, under the
non-root `trader` user. The repo is cloned at
`/home/trader/algotrading-paper`; system cron invokes
`vps/cron-fetch.sh` every 5 minutes. The `.env` lives on the VPS
(same four credentials as local), `chmod 600`. The VPS pushes to
GitHub via a write-enabled deploy key.

**What runs.** `vps/cron-fetch.sh` does the full pipeline:
`git pull` → `fetch.py --minutes=90` → `render_index.py` →
`scripts/generate_surface.py` → commit (`trader.db`, `INDEX.md`,
`surface/surface.json`, `surface/punch_list.json`,
`surface/index.html`) → push. Identical surface output to the old
GitHub Actions job; it just fires reliably now.

**How the operator's local repo stays in sync.** Same as before —
`git pull` before doing any local work. The VPS commits as
`algotrading-paper bot`; `git log --invert-grep --grep='^fetch run'`
filters cron commits out when reviewing operator activity.

**How to update the VPS.** `git pull` on the VPS, or just wait — the
cron does a `git pull --rebase` at the start of every run, so code
changes land within one cycle automatically. Full install / debug
steps are in `vps/README.md`.

**Failure modes and where to look.**
- VPS down → no new `fetch run` commits; the live surface's
  `cron stale` indicator fires after 90 min. Check the Hetzner
  console.
- Cron fires but `fetch.py` fails → a `runs` row with
  `status='failed'` and `error_text`; the Python traceback is in
  `vps/logs/cron-YYYY-MM-DD.log` on the VPS.
- Push fails → data is safe (committed locally on the VPS), retried
  next run; check the GitHub deploy key has write access.

**GitHub Actions fallback.** `.github/workflows/fetch-and-commit.yml`
still exists with its `schedule:` commented out; it's
`workflow_dispatch`-able for a manual one-off or as a temporary
fallback during VPS downtime.

---

## Step 9 — Begin Week 1

Once Steps 1–8 are complete, the repo is ready for the Week 1
build. The Week 1 prompt is in `week-1-prompt.md` (already in the
repo from Step 4).

Open Claude Code in the repo (if not already open from the
pre-flight) and paste the prompt from `week-1-prompt.md` (the
section between the triple-backtick fences).

Claude Code will:

1. Read the eight canonical project files
2. Reply with a one-paragraph scope confirmation summarizing what
   Week 1 IS and what it is NOT
3. Wait for confirmation before writing any code

If the scope confirmation is correct, give the go-ahead. If it
adds scope, drops scope, or misframes any of the conventions
(em-dash empty states, four-stat band, `§` section markers),
correct before letting it build.

---

## Verification checklist

Before declaring setup complete, confirm:

- [ ] Alpaca paper-trading dashboard shows $100,000 balance
- [ ] Alpaca API key + secret are saved in a password manager
      (not just `.env`)
- [ ] Anthropic API key is generated and saved in a password
      manager
- [ ] Anthropic console has a $50 monthly usage alert set
- [ ] Local `.env` exists and contains all four credential values
- [ ] `.gitignore` includes `.env` and `.env.*`, verified by
      `git status` not showing `.env`
- [ ] GitHub Actions secrets contain `ALPACA_API_KEY`,
      `ALPACA_SECRET_KEY`, `ALPACA_BASE_URL`, `ANTHROPIC_API_KEY`
- [ ] All eight canonical project files (PROJECT.md,
      philosophy.md, decision-log.md, playbook.md, setup.md,
      week-0-synthesis.md, report-format-spec.md, roadmap.md)
      are in the repo
- [ ] `week-1-prompt.md` is in the repo
- [ ] Initial commits pushed to GitHub successfully
- [ ] `.env` does NOT appear in the GitHub file listing
- [ ] Claude Code can read `PROJECT.md` from the repo

If any item is unchecked, the build will hit a wall partway
through Week 1. Better to fix it now than mid-build.

---

## What NOT to do during setup

- **Don't commit `.env`** to git, even briefly. If it happens
  accidentally, rotate both Alpaca and Anthropic keys immediately
  rather than trying to scrub git history.
- **Don't fund the live Alpaca account yet.** Phase 2 is gated by
  Phase 1 outcomes; live funding is deferred.
- **Don't skip the GitHub Actions secrets.** If credentials are
  only in `.env`, the cron will fail when GitHub runs the
  workflow. Both stores are required.
- **Don't share the API keys** in claude.ai conversations,
  Claude Code, or anywhere else outside `.env` and GitHub
  secrets. If a key is pasted anywhere else by accident, rotate
  it.
- **Don't let Claude Code touch real `.env` values.** The
  pre-flight discipline is that Claude Code creates
  `.env.template` and verifies gitignore with a dummy file; the
  operator manually creates `.env` with real keys. This division
  is the structural mitigation against accidental key leakage.
- **Don't customize the Alpaca account** beyond the basics. The
  defaults (cash account, USD denominated, all standard
  settings, 2x default margin which the execution layer ignores)
  are what the project assumes. Customization introduces
  variables that complicate debugging later.
