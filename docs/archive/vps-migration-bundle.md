# VPS Migration Bundle — 2026-05-23

Self-contained. Three phases. ~45 minutes total.

**Phase A** (you, ~15 min): Provision the VPS.
**Phase B** (Claude Code, ~15 min): Create migration scripts.
**Phase C** (you, ~15 min): Deploy and verify.

Do them in order. Don't skip Phase A — Phase B's prompt needs the
VPS IP.

---

## Phase A — Provision the Hetzner VPS

### A1. Create the Hetzner account

If you don't have one: `console.hetzner.cloud` → sign up. Email +
password. They'll ask for billing details. Add a credit card; the
$5.83/mo charge is small.

### A2. Create a new project

In the console: "New Project" → name it `algotrading-paper`.

### A3. Create the server

In the project: "Add Server."

- **Location:** Ashburn (US East) or Nuremberg (EU). Pick the one
  closest to where Alpaca's API endpoint lives — Ashburn is fine for
  Alpaca paper.
- **Image:** Ubuntu 24.04 LTS
- **Type:** CX22 (2 vCPU, 4GB RAM, 40GB SSD) — $5.83/mo. The
  smallest sufficient size; don't oversize.
- **Networking:** IPv4 enabled (default). IPv6 enabled (default).
- **SSH keys:** Add your existing SSH public key. If you don't have
  one, generate locally first: `ssh-keygen -t ed25519 -C "your-email"`
  then paste the contents of `~/.ssh/id_ed25519.pub`. Don't use
  password auth.
- **Name:** `algotrading-cron`

Click "Create & Buy Now." Server provisions in ~30 seconds. Note
the IPv4 address that appears.

### A4. First SSH connection

```
ssh root@YOUR_VPS_IP
```

You should see Ubuntu's welcome banner. If you get a connection
refused or timeout, check that your SSH key is correct in the
Hetzner console.

### A5. Initial server setup

Run these commands on the VPS (copy/paste, one block at a time):

```
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv git sqlite3 cron

# Verify cron is running
systemctl status cron
# Should show "active (running)". Ctrl-C to exit.

# Create a non-root user for the cron work
useradd -m -s /bin/bash trader
usermod -aG sudo trader

# Copy your SSH key to the trader user
mkdir -p /home/trader/.ssh
cp /root/.ssh/authorized_keys /home/trader/.ssh/
chown -R trader:trader /home/trader/.ssh
chmod 700 /home/trader/.ssh
chmod 600 /home/trader/.ssh/authorized_keys

# Disconnect
exit
```

### A6. Reconnect as the trader user

```
ssh trader@YOUR_VPS_IP
```

You're now logged in as `trader`, not `root`. All further work
happens as this user.

### A7. Clone the repo

```
cd ~
git clone https://github.com/pwysocan-droid/algotrading-paper.git
cd algotrading-paper
```

If the repo is public, no auth needed. If you've made it private,
you'll need a personal access token or deploy key — handle
separately if so.

### A8. Set up the Python environment

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Adjust the requirements filename if you use `pyproject.toml`
instead (`pip install -e .`).

### A9. Create the .env file on the VPS

```
nano .env
```

Paste in the four credentials (the same values that are in your
local `.env`):

```
ALPACA_API_KEY=PK_your_actual_key
ALPACA_SECRET_KEY=your_actual_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ANTHROPIC_API_KEY=sk-ant-your_actual_key
```

Save (Ctrl-O, Enter, Ctrl-X). Verify:

```
cat .env
# Should show your four lines
chmod 600 .env
# Restrict read access to your user only
```

### A10. Configure git identity for bot commits

```
git config user.email "bot@algotrading-paper"
git config user.name "algotrading-paper bot"
```

### A11. Set up git push from the VPS

The VPS needs to push to GitHub. Easiest: deploy key.

On the VPS:

```
ssh-keygen -t ed25519 -C "vps-deploy-key" -f ~/.ssh/github_deploy_key -N ""
cat ~/.ssh/github_deploy_key.pub
```

Copy the public key output. On GitHub:

- Go to `github.com/pwysocan-droid/algotrading-paper/settings/keys`
- "Add deploy key"
- Title: `hetzner-cron`
- Key: paste the public key
- **Check "Allow write access"** (essential — read-only won't work)
- Click "Add key"

Back on the VPS, configure SSH to use the deploy key:

```
cat >> ~/.ssh/config <<EOF
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_deploy_key
  IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config
```

Switch the repo's remote to SSH:

```
cd ~/algotrading-paper
git remote set-url origin git@github.com:pwysocan-droid/algotrading-paper.git
```

Test the push:

```
git pull
# Should succeed without prompting for password
```

### A12. Test fetch.py manually

```
python fetch.py
```

If this succeeds (writes a new runs row, fetches some bars), the
VPS environment is ready. If it fails, debug before proceeding —
the cron will just fail repeatedly otherwise.

### A13. Note the VPS IP, then move to Phase B

You'll need the IP for the Phase B prompt. The trader user's home
directory is `/home/trader`, repo is at
`/home/trader/algotrading-paper`. Hand these details to Claude Code.

---

## Phase B — Claude Code creates the migration scripts

In Claude Code, in your local `algotrading-paper` repo:

```
Migrate the cron from GitHub Actions to a Hetzner VPS. Decision-log
entry already committed at the top of decision-log.md.

VPS details:
- Host: trader@YOUR_VPS_IP (replace with actual IP)
- Repo path on VPS: /home/trader/algotrading-paper
- .env already set up on VPS with all four credentials
- Python venv at /home/trader/algotrading-paper/.venv
- Git remote uses SSH deploy key, push works

# Work to do

## 1. Create vps/ directory with three files

vps/cron-fetch.sh — the wrapped fetch+render+commit+push script
that system cron will invoke. Must:
- Activate the venv
- cd into the repo
- git pull (to receive any operator commits)
- Run fetch.py
- Run render_index.py
- git add trader.db INDEX.md
- If anything to commit: commit with message
  "fetch run YYYY-MM-DDTHH:MM:SSZ" using actual UTC timestamp
- git push
- Log all output to /home/trader/algotrading-paper/vps/logs/cron-YYYY-MM-DD.log
  (rotate by date)
- Trap errors and write status to runs table even if other steps fail
- Exit 0 if fetch.py succeeded, even if push fails (the next run
  will retry the push)

vps/crontab.txt — the crontab entry for the trader user:
*/5 * * * * /home/trader/algotrading-paper/vps/cron-fetch.sh >> /home/trader/algotrading-paper/vps/logs/cron-master.log 2>&1

vps/README.md — installation instructions:
- How to copy these files to the VPS
- How to make cron-fetch.sh executable
- How to install the crontab entry (crontab -e, paste, save)
- How to verify cron is running (sudo systemctl status cron, tail -f
  the log)
- How to debug failures
- How to update the scripts (git pull on VPS, no other action needed)

## 2. Disable the GitHub Actions cron workflow

Edit .github/workflows/fetch-and-commit.yml:
- Comment out the `schedule:` block
- Add `workflow_dispatch:` so it can still be triggered manually
- Add a comment at the top: "Scheduled cron disabled 2026-05-23 in
  favor of Hetzner VPS cron. See decision-log entry. Workflow
  preserved for manual trigger or future re-enablement."

## 3. Update kind column logic

In fetch.py and any code that writes runs rows, ensure cron runs
from the VPS still log with kind='cron'. The kind column added in
the earlier migration should already handle this — verify and add
a test if needed.

## 4. Document the new architecture

Add a section to setup.md (between current Step 8 and Step 9)
titled "VPS cron architecture" explaining:
- Why the cron migrated (pointer to 2026-05-23 decision-log entry)
- Where the cron runs (Hetzner VPS, trader user)
- How operator's local repo stays in sync (git pull as usual)
- How to update the VPS (git pull on the VPS, or re-deploy vps/
  scripts)
- Failure modes and where to look (vps/logs/, runs table)

## 5. Commit and push each file as its own commit

Don't squash. The migration should be traceable in git history.

## Verification

- All existing tests still pass
- vps/cron-fetch.sh exists, is shell-syntactic-valid (shellcheck if
  available), and references the correct paths
- vps/crontab.txt exists with the correct path
- vps/README.md exists and is operator-readable
- .github/workflows/fetch-and-commit.yml schedule is commented out
- setup.md has the new section

Report status when done. I'll then deploy to the VPS (Phase C).
```

---

## Phase C — Deploy and verify

After Claude Code finishes and pushes:

### C1. Pull on the VPS

```
ssh trader@YOUR_VPS_IP
cd ~/algotrading-paper
git pull
```

You should see the new `vps/` directory.

### C2. Make the script executable

```
chmod +x vps/cron-fetch.sh
mkdir -p vps/logs
```

### C3. Test the script manually first

```
./vps/cron-fetch.sh
```

It should: pull, run fetch, run render, commit, push. Check the
output, check that a new commit appears on GitHub.

If anything fails here, debug before installing the cron entry —
once cron is installed, failures cascade silently.

### C4. Install the cron entry

```
crontab -e
```

Paste the contents of `vps/crontab.txt`. Save (Ctrl-O, Enter, Ctrl-X
if it's nano).

Verify:

```
crontab -l
# Should show your */5 entry
```

### C5. Watch the first few runs

```
tail -f vps/logs/cron-master.log
```

First scheduled run fires within 5 minutes. Watch ~15 minutes (~3
runs) to confirm steady-state. Then Ctrl-C to exit the tail.

### C6. Verify in the runs table

Pull locally:

```
git pull
sqlite3 trader.db "SELECT started_at, status, kind FROM runs WHERE kind='cron' ORDER BY id DESC LIMIT 10;"
```

The most recent runs should all be from the VPS, with timestamps
roughly 5 minutes apart, all status='ok'.

### C7. Confirm GitHub Actions is silent

Visit `github.com/pwysocan-droid/algotrading-paper/actions` —
fetch-and-commit should show no new runs (scheduled trigger
disabled). It should still appear in the workflow list but be
inactive.

### C8. Verify INDEX.md / surface updates

Check `pwysocan-droid.github.io/algotrading-paper/surface/` — the
"last run" timestamp should be recent (within 5 minutes), and the
cadence should be steady going forward.

### C9. After 1 hour, confirm reliability

Should see ~12 runs in the last hour. If significantly fewer,
debug. If exactly 12 (or 11-13), the migration is successful.

---

## What to do if something goes wrong

**Cron isn't firing:**
- `sudo systemctl status cron` (should be active)
- `crontab -l` (should show entry)
- Check `vps/logs/cron-master.log` for errors

**Cron fires but fetch.py fails:**
- Check `.env` is present and readable: `cat .env`
- Check venv is activated correctly in cron-fetch.sh
- Check the most recent cron-YYYY-MM-DD.log for the Python error

**Cron fires, fetch succeeds, push fails:**
- SSH key issue: `ssh -T git@github.com` should respond with "Hi
  pwysocan-droid! You've successfully authenticated"
- Repo write permission: verify deploy key has "Allow write access"

**Hetzner billing surprise:**
- CX22 is $5.83/mo. If you see something higher, double-check the
  server type (don't accidentally provision CX42 or larger).

---

## After verification: re-enable surface health visibility

The cron health element I suggested for the mobile surface (the
invocation rate / success rate ratios) is now more important — the
operator should be able to see VPS uptime as readily as code-success
rate. This is a mobile UI conversation item, not part of this
migration.

Done. The 95% uptime gate is achievable, the curriculum runs on
solid infrastructure, the cron-reliability cloud lifts.
