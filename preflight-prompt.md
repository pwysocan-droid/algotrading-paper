# Pre-Flight Prompt for Claude Code

Use this prompt before the Week 1 prompt. Its job is repo setup
only — `.gitignore` first, then `.env` template, then initial
commit, then GitHub remote setup. Claude Code never sees real
secrets in this prompt; the operator pastes them in manually
afterward.

---

## The prompt

```
Pre-flight setup for the algotrading-paper project. Do these
steps in order. Do NOT do any Week 1 build work — that's a
separate prompt.

You'll find the canonical project files already in this
directory:
- PROJECT.md
- philosophy.md
- decision-log.md
- playbook.md
- setup.md
- week-0-synthesis.md
- report-format-spec.md
- roadmap.md
- week-1-prompt.md (this is for the next session, not Week 1
  itself; just leave it where it is)

If any of these files are missing, stop and tell me which.

# Step 1 — Initialize the repo

If `.git/` doesn't exist yet, run `git init`. If it does exist,
skip this step.

Verify with `git status` — you should see all the canonical
files listed as untracked.

# Step 2 — Create .gitignore FIRST

Create `.gitignore` at the repo root with the following contents:

```
# Secrets
.env
.env.*

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.venv/
venv/
*.egg-info/

# OS
.DS_Store
Thumbs.db

# Editors
.vscode/
.idea/
*.swp
*.swo

# Build / cache
build/
dist/
.coverage
htmlcov/

# Database (Phase 1 will create local SQLite files)
*.db
*.db-journal
*.sqlite
*.sqlite3

# Reports / runs (these accumulate; commit only the canonical
# ones, not every run artifact)
runs/*.log
```

Then commit just this:

```
git add .gitignore
git commit -m "Add gitignore"
```

This MUST be done before .env exists. Do not skip the commit.

# Step 3 — Create the .env template

Create a file named `.env.template` (NOT `.env`) at the repo
root with the following contents:

```
# Copy this file to .env and fill in real values.
# .env is gitignored; .env.template is committed.

ALPACA_API_KEY=PK_replace_me
ALPACA_SECRET_KEY=replace_me
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ANTHROPIC_API_KEY=sk-ant-replace_me
```

Commit it:

```
git add .env.template
git commit -m "Add .env template"
```

The operator will manually copy this to `.env` and replace the
placeholder values with real keys after this prompt is done.
Do NOT create .env yourself.

# Step 4 — Verify gitignore is working

Create a temporary fake `.env` file with dummy contents to verify
gitignore actually ignores it:

```
echo "TEST=dummy" > .env
```

Then run:

```
git status
git check-ignore -v .env
```

Confirm:
- `.env` does NOT appear in `git status` output
- `git check-ignore -v .env` returns a line referencing
  `.gitignore` and the `.env` rule

If both checks pass, delete the temporary file:

```
rm .env
```

If either check fails, STOP and report what you saw. Don't
proceed to Step 5.

# Step 5 — Add the canonical project files

```
git add PROJECT.md philosophy.md decision-log.md playbook.md \
        setup.md week-0-synthesis.md report-format-spec.md \
        roadmap.md week-1-prompt.md
git commit -m "Initial project spec and supporting docs"
```

If any of these files are missing from the directory, stop and
report which.

# Step 6 — Show me the state

Run and report the output of:

```
git log --oneline
git status
ls -la
```

I want to see: three commits in log (gitignore, env template,
initial spec), a clean `git status`, and the directory listing
showing all the canonical files plus `.gitignore` and
`.env.template`.

# What you do NOT do in this prompt

- Do NOT create `.env` with real values.
- Do NOT generate any code (no db.py, fetch.py, etc.).
- Do NOT add a GitHub remote or push.
- Do NOT touch the wagon-watcher repo or any other directory.

The Week 1 prompt is what kicks off code generation. This
prompt is just repo setup.

After Step 6, stop and wait for me to:
1. Manually create `.env` from `.env.template` with real keys
2. Create the GitHub repo and add the remote
3. Push the initial commits
4. Add GitHub Actions secrets

Then I'll come back with the Week 1 prompt.
```

---

## What you do after Claude Code finishes this prompt

**1. Create the real `.env` from the template, manually.**

```
cp .env.template .env
```

Then open `.env` in your editor and paste in the real values from
your password manager:

```
ALPACA_API_KEY=PK1ABC...   (the actual paper key)
ALPACA_SECRET_KEY=xyz...   (the actual paper secret)
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ANTHROPIC_API_KEY=sk-ant-...   (the actual Anthropic key)
```

Save. Do NOT commit. Run `git status` one more time to verify
`.env` doesn't appear.

**2. Create the GitHub repo.**

On github.com, create a new repository named `algotrading-paper`.
Public (per setup.md). Do NOT initialize with README, .gitignore,
or license — your local repo provides everything.

**3. Add the remote and push.**

```
git remote add origin https://github.com/[your-username]/algotrading-paper.git
git branch -M main
git push -u origin main
```

After the push, verify on github.com that `.env` does NOT appear
in the file list. (It shouldn't, but checking is cheap.)

**4. Add GitHub Actions secrets.**

Settings → Secrets and variables → Actions → New repository secret.
Add four:

- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `ALPACA_BASE_URL` (value: `https://paper-api.alpaca.markets`)
- `ANTHROPIC_API_KEY`

**5. Set Anthropic usage alert.**

console.anthropic.com → Settings → Billing → set a $50 monthly
alert. Cheap and prevents surprises.

**6. Come back here and say "ready for Week 1."**

I'll confirm everything is in place, then hand you the Week 1
prompt to give to Claude Code.
