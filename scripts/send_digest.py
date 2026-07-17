"""Email the newest digest — VPS-side SMTP delivery.

The claude.ai Gmail connector turned out to be draft-only (2026-07-17:
test emails landed as unsent drafts), so delivery lives here instead:
the machine that renders the digest sends it, right after
generate_rounds.py in cron-skeptic.sh. Sends via Gmail SMTP with an
App Password from the environment:

    GMAIL_APP_PASSWORD  (required — app password, not the account password)
    GMAIL_ADDRESS       (optional, default pwysocan@gmail.com; both the
                         sender and the recipient — self-sent mail)

Staleness doubles as the heartbeat: if the newest digest is older than
yesterday the email says STALE instead of silently skipping — an
inbox with neither a digest nor a warning means the VPS itself is down.
Exit 0 with a log line when creds are absent, so the cron chain never
breaks on an unconfigured box.
"""

from __future__ import annotations

import os
import re
import smtplib
import sys
from datetime import date, datetime, timedelta, timezone
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent


def newest_digest(reports: Path) -> tuple[date, Path] | None:
    best: tuple[date, Path] | None = None
    for p in reports.glob("digest-*.md"):
        m = re.fullmatch(r"digest-(\d{4}-\d{2}-\d{2})\.md", p.name)
        if not m:
            continue
        d = date.fromisoformat(m.group(1))
        if best is None or d > best[0]:
            best = (d, p)
    return best


def main() -> int:
    password = os.environ.get("GMAIL_APP_PASSWORD")
    address = os.environ.get("GMAIL_ADDRESS", "pwysocan@gmail.com")
    if not password:
        print("send_digest: GMAIL_APP_PASSWORD not set — skipping (not an error)")
        return 0

    today = datetime.now(timezone.utc).date()
    found = newest_digest(REPO_ROOT / "reports")
    if found is None:
        subject = "algotrading-paper digest STALE"
        body = ("No digest files found in reports/ at all — the VPS nightly "
                "pipeline is broken. Check cron on the VPS; OPERATOR.md has "
                "the triggers.")
    else:
        d, path = found
        if d >= today - timedelta(days=1):
            subject = f"algotrading-paper digest {d.isoformat()}"
            body = path.read_text()
        else:
            subject = "algotrading-paper digest STALE"
            body = (f"Newest digest is {d.isoformat()} — older than yesterday. "
                    "The VPS nightly pipeline may be down. Check cron on the "
                    "VPS; OPERATOR.md has the triggers.")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = address
    msg["To"] = address

    # Port 587 + STARTTLS, not 465/SSL: Hetzner blocks outbound 465
    # from this box (measured 2026-07-17) but leaves 587 open.
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(address, password)
        smtp.sendmail(address, [address], msg.as_string())
    print(f"send_digest: sent {subject!r} to {address}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
