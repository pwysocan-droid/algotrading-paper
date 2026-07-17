"""Nightly shadow-replay parity — the engine's tripwire.

Recomputes, from the bars table alone, every signal each enabled
deterministic variant SHOULD have emitted over the trailing window, and
compares against what the live loop actually persisted. All current
strategies are pure functions of bars, so:

  - a live signal the shadow can't reproduce  -> ENGINE BUG (hard fail)
  - a shadow signal missing from live         -> usually a skipped cron
    cycle (two bars landing between ticks means the earlier one is never
    'latest'); reported as info, not failure

Variants declaring context_keys are skipped (their context is stateful);
they get validated by the weekly calibration report instead.

Writes reports/parity-YYYY-MM-DD.md only on hard mismatch. Run nightly
by cron-skeptic.sh; exit code 0 unless an engine bug is found.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
import signals as sig_mod
from config import STRATEGY_VARIANTS, WATCHED_SYMBOLS

REPO_ROOT = Path(__file__).resolve().parent.parent
WINDOW_HOURS = 24
BARS_CONTEXT = 400  # matches load_recent_bars / replay window_cap


def shadow_signals(conn, variant_name: str, variant: dict, since_iso: str) -> set:
    fn = sig_mod.get_strategy_fn(variant["strategy"])
    params = variant.get("params", {})
    out = set()
    for symbol in WATCHED_SYMBOLS:
        rows = conn.execute(
            "SELECT symbol, timestamp, open, high, low, close, volume FROM bars"
            " WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?",
            (symbol, BARS_CONTEXT + 288),
        ).fetchall()
        bars = [sig_mod.BarRow(**dict(r)) for r in rows][::-1]
        for i in range(len(bars)):
            if bars[i].timestamp < since_iso:
                continue
            window = bars[max(0, i + 1 - BARS_CONTEXT): i + 1]
            s = fn(window, params, {})
            if s is not None:
                out.add((symbol, bars[i].timestamp, s.side))
    return out


def main() -> int:
    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=WINDOW_HOURS)).isoformat()
    hard_failures: list[str] = []
    info: list[str] = []

    with db.connect() as conn:
        for name, variant in STRATEGY_VARIANTS.items():
            if not variant.get("enabled") or variant.get("context_keys"):
                continue
            live = {
                (r["symbol"], r["bar_timestamp"], r["side"])
                for r in conn.execute(
                    "SELECT symbol, bar_timestamp, side FROM signals"
                    " WHERE variant_name = ? AND bar_timestamp >= ?",
                    (name, since),
                )
            }
            shadow = shadow_signals(conn, name, variant, since)
            ghost = live - shadow      # live emitted, shadow can't reproduce → bug
            skipped = shadow - live    # shadow found, live missed → likely cycle skip
            if ghost:
                hard_failures.append(f"{name}: {len(ghost)} live signals NOT reproducible: {sorted(ghost)[:5]}")
            if skipped:
                info.append(f"{name}: {len(skipped)} shadow signals absent from live (cycle timing)")
            print(f"{name}: live={len(live)} shadow={len(shadow)} ghost={len(ghost)} skipped={len(skipped)}")

    if hard_failures:
        report = REPO_ROOT / "reports" / f"parity-{now.date().isoformat()}.md"
        report.write_text(
            f"# PARITY FAILURE — {now.isoformat()}\n\n"
            "Live signals the deterministic shadow replay cannot reproduce —\n"
            "this is an engine bug, not market noise. Distrust gauntlet\n"
            "verdicts until resolved.\n\n"
            + "\n".join(f"- {f}" for f in hard_failures)
            + ("\n\nInfo:\n" + "\n".join(f"- {i}" for i in info) if info else "")
            + "\n"
        )
        print(f"PARITY FAILURE — wrote {report}")
        return 1
    print("parity ok" + (f" ({'; '.join(info)})" if info else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
