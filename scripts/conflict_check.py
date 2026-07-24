"""Mechanical conflict gate — CONSTITUTION Article 4.2.

The corrupt auditor cannot feel their own corruption (4.1), so the
Service's conflict declaration is machine-generated from the Book's
position ledger, never authored by judgment. This is a BLOCKING GATE:
an autopsy that touches any instrument the Book holds, has held, or has
a registered pending interest in cannot publish until this tool has
attached the verbatim declaration. A bypassed/failed gate is a
constitutional breach (4.2).

Usage (in the publish pipeline):
    python scripts/conflict_check.py --instruments BTC,ETH --autopsy <id>
Exit 0 with a "CLEAR" or "CONFLICT" declaration written to the autopsy's
pre-registration; nonzero only on tooling failure (which itself blocks).

Ledger: book/positions.jsonl — one JSON object per line:
  {"ts","instrument","venue","side","status","structural_worst_case_pct"}
status in {pending, open, closed}. All three count as conflicts —
historical and pending interests are disclosed, not just open ones.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "book" / "positions.jsonl"


def load_ledger() -> list[dict]:
    if not LEDGER.exists():
        return []
    out = []
    for line in LEDGER.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def declaration(instruments: list[str]) -> tuple[bool, str]:
    inst = {i.strip().upper() for i in instruments if i.strip()}
    hits = [p for p in load_ledger()
            if p.get("instrument", "").upper() in inst]
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if not hits:
        return False, (f"CONFLICT DECLARATION (machine-generated {ts})\n"
                       f"Instruments audited: {sorted(inst)}\n"
                       f"Book interest: NONE (no pending/open/closed position "
                       f"in any audited instrument).\nStatus: CLEAR.")
    lines = [f"CONFLICT DECLARATION (machine-generated {ts})",
             f"Instruments audited: {sorted(inst)}",
             "Book interest: DISCLOSED —"]
    for p in hits:
        lines.append(f"  - {p.get('instrument')} · {p.get('status')} · "
                     f"{p.get('side','?')} on {p.get('venue','?')} "
                     f"(opened {p.get('ts','?')[:10]})")
    lines.append("Status: CONFLICT — this declaration must appear verbatim in "
                 "the published autopsy (Article 4.2).")
    return True, "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", required=True, help="comma-separated tickers")
    ap.add_argument("--autopsy", default=None, help="autopsy id (for the record)")
    ap.add_argument("--write", type=Path, default=None,
                    help="append declaration to this pre-registration file")
    args = ap.parse_args()
    conflict, text = declaration(args.instruments.split(","))
    print(text)
    if args.write:
        with args.write.open("a") as f:
            f.write("\n\n---\n" + text + "\n")
    # exit 0 either way — the gate's job is to ATTACH the declaration, not to
    # block on conflict (disclosure, not prohibition); tooling failure is the
    # only nonzero, and it blocks publication by construction.
    return 0


if __name__ == "__main__":
    sys.exit(main())
