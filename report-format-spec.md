# Report Format Spec — algotrading-paper

How the markdown reports produced by `replay.py`, the weekly status
reports, the A/B and recommendation reports, and the project's
index page should look. Inherits the wagon-watcher's design
language and discipline; adapts the information architecture for
this project's multi-variant, temporal-comparison shape.

This spec is referenced by the Week 1 opening prompt to Claude
Code. It supersedes any defaults Claude Code might pick on its
own.

The two wagon-watcher surfaces serve as references:

- **v1** (`wagon-watcher.vercel.app`) — snapshot inventory pattern
- **v2** (`wagon-watcher.vercel.app/v2`) — temporal movers ticker

Algotrading-paper uses both. **v1-style** for snapshot reports
(`replay.py` output, `week-N-status.md`, `INDEX.md`). **v2-style**
for temporal reports (weekly A/B, walk-forward recommendations,
monthly pattern surfacing).

---

## Core principle: trend-aware data, not analytical prose

Routine reports (anything in `reports/`, `recommendations/`, plus
`INDEX.md`) present **data** with **trend context**, not analytical
prose. Sparklines, deltas, period-over-period comparisons, and
regime markers are the analysis layer. The data is self-describing
through density and trend-awareness; explanatory prose belongs in
`reviews/` (cluster-4 methodologies 4G and 4H), not in routine
reports.

The one exception: `INDEX.md` includes a "Reading order" section
with brief navigational prose explaining which surface to read in
which situation. This is *navigational* meta-analysis, not data
analysis, and it's contained to a single section.

The reasoning, in short: routine reports get auto-generated. Auto-
generated analytical prose drifts toward hedged generic filler
within weeks. Better to make the data carry the analysis through
trend-aware presentation, and isolate genuine analytical work to
the dedicated review surfaces where a human is in the room.

---

## Design system inheritance (unchanged)

- **Typography:** Inter for any rendered surfaces; JetBrains Mono
  or IBM Plex Mono for all numeric data and identifiers.
- **No Helvetica.** Anywhere.
- **SBB Red `#EB0000`** is the only signal color. Used sparingly,
  only for genuinely anomalous things — a failed run, a breached
  position limit, a P&L outlier, a flagged variant. Never for
  decoration.
- **Information density over visual comfort.** Reports are read
  by the operator under stress. Tables are dense; whitespace
  serves scannability, not aesthetics.
- **Markdown source-of-truth.** All reports are markdown files in
  the repo. GitHub renders them natively. A styled HTML surface
  is a deferred decision (Week 2 review per the roadmap); for now
  the markdown plus GitHub's default rendering is the operator
  surface.

---

## Adapted patterns from wagon-watcher

These translate directly. Adopt faithfully unless this spec gives
a specific reason to diverge.

**1. Header block.** Project name with slash-separated subtitle
(`algotrading-paper / replay`, `algotrading-paper / week-3 status`,
`algotrading-paper / a-b · weekly`). One-line context (the
report's specific subject). A timestamp in UTC. A count summary.
Two prominent inline links — one to a related raw artifact, one
to a sibling surface (typically `INDEX.md`).

**2. Em-dashes as empty-state placeholders.** When a value isn't
present yet, render as `—`, not `0`, not `null`, not "loading,"
not "n/a." Em-dash means "the slot exists, the value is not yet
present." Zero is a real value (zero trades, $0.00 P&L) and gets
rendered as `0` or `$0.00`. The distinction is load-bearing.

**3. The `§` section marker.** Section headers use `§` as the
anchor character: `§ 02 — Per-variant performance · last 30 days`.
The `§` is semantic and visual. Middot `·` separates the section
number, the title, and any modifier clause.

**4. The four-stat summary band.** Just below the header, a
four-cell summary block — label-and-value, value heavier than
label. Stats vary by report type but the pattern is identical to
wagon-watcher's "National pool / Within criteria / Median asking
/ Tier 1 alerts" band.

**5. Canonical-identifier-as-link.** Wagon-watcher uses VIN as
the link target. Algotrading-paper uses **trade ID** the same way:

```
[`#0142`](https://app.alpaca.markets/paper/orders/0142)
```

For variant-level rows, the variant name is the canonical
identifier (no link target — variants don't have an external URL
— but rendered in the same monospace style):

```
`bollinger_default`
```

**6. Superscript classification.** Wagon-watcher uses `¹` `ˢ`
`ˡ`. Algotrading-paper uses superscripts for variant status:

- `ᵖ` — phase-qualified (cleared for Phase 2 if reached)
- `ⁿ` — newly promoted (last 7 days)
- `ʳ` — under recommendation review

These appear immediately after the variant name in tables.

**7. Reading-the-row legend.** v2-style reports include a small
legend below the main table explaining notation. v1-style reports
skip this; the columns are self-describing.

**8. Plain-text data-source footer.** At the very bottom, the
provenance URL plus a GitHub link — small type, low visual
priority, no decoration.

---

## Adapted patterns — diverged

**Empty-state full rendering.** Wagon-watcher's empty state is
brief. Algotrading-paper's empty state is *constant* during
Weeks 1–2 and during quiet market periods. The empty state is
therefore a **fully-formed report that happens to have zero rows**
— same header, same four-stat band (with em-dashes), same dominant
table (with column headers visible and an explicit "0 variants
registered" or "0 trades in period" cell where rows would be),
same footer. The flags section explicitly states why the report
is empty (e.g., "No strategy variants are registered. This is
expected for Week 1.") only on `INDEX.md`; on routine reports,
explain in the §04 Notes section if needed.

**Anomalies-and-flags section.** Wagon-watcher doesn't have a
dedicated flags section. Algotrading-paper does — the system is
autonomous within strict limits and the operator needs to see
breaches immediately. The section sits above the dominant table
when populated, below it (collapsed to one line) when empty.

---

## Information architecture

Reading order, top to bottom, for any report:

1. **Header block** (v1 and v2)
2. **Four-stat summary band** (v1 and v2)
3. **Anomalies and flags** — above the table when populated;
   collapsed below the table when empty
4. **The dominant table** — variants × metrics
5. **Sub-tables and cross-cuts** — section by section, each with
   `§` marker
6. **Reading-the-row legend** (v2 only)
7. **Marginalia footer** — code version, data-source URL, GitHub
   link

---

## INDEX.md — project hub page (v1 pattern)

Lives at the repo root. Regenerated automatically by
`render_index.py` after any artifact commit. Always reflects the
latest state of every surface kind.

Sections:

1. **Header block** — project name, current phase + week,
   timestamp, two top links (latest replay, weekly status)
2. **Four-stat band** — project-level heartbeat: system uptime
   (last 4w), trades this week, Phase 2 gates passed (out of 3),
   days to phase 1 review
3. **Flags** — project-level flags only; routine report flags
   stay in the report
4. **§ Surfaces table** — every kind of report, with: surface
   name, latest filename, generated date, status. Every row
   linked to the latest of that kind
5. **§ Reading order** — short prose explaining which surface to
   read in which situation. Five paragraphs, fixed structure
   (replay → status → recommendations → patterns → philosophy)
6. **§ Foundational documents** — inline link list to the
   read-at-week-4-when-lost files: `PROJECT.md`, `philosophy.md`,
   `decision-log.md`, `playbook.md`, `roadmap.md`,
   `week-0-synthesis.md`, `setup.md`
7. **Marginalia footer**

The four stats on INDEX are project-level and different from any
single report's four-stat band:

| Position | Label | Value source |
| --- | --- | --- |
| 1 | system uptime | runs table, last 4w |
| 2 | trades this week | trades table, ISO week |
| 3 | phase 2 gates passed | gate-check function, 0–3 |
| 4 | days to phase 1 review | calendar arithmetic |

When a surface kind has no instance yet, its row uses em-dashes
with a status note explaining when the first instance is expected
(e.g., "not yet · Week 4"). This pattern repeats during the
curriculum.

---

## v1 pattern — snapshot reports

For: `replay.py` output, `week-N-status.md`, `phase1-review.md`,
`phase2-review.md`, `INDEX.md`.

Header example (replay):

```
algotrading-paper / replay

Variant — null  ·  Period — 2026-04-02 → 2026-05-02 (30d)

2026-05-02 16:06:29 UTC

0 trades

[run log →](runs/2026-05-02T160629.log)  ·  [↗ index](INDEX.md)
```

Four-stat band example (Week 1 replay, empty state):

```
Variants registered

—

0 enabled

Trades in period

0

paper

P&L

$0.00

—%

System uptime

100%

last 4w
```

Note the em-dash for "Variants registered" (no variants yet) vs.
the explicit `0` for "Trades in period" (zero is a real value).

Dominant table example (Week 1, empty state):

```
§ 01 — Per-variant performance · last 30 days

| Variant | n | 30d sparkline | P&L | Pct | Sharpe | Max DD | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| no variants registered | — | — | — | — | — | — | — |
```

Dominant table example (mid-curriculum, populated):

```
§ 01 — Per-variant performance · last 30 days

| Variant | n | 30d sparkline | P&L | Pct | Sharpe | Max DD | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `bollinger_default`ᵖ | 287 | ▄▅▆▇█▇▆▇ | +$112.40 | +11.2% | 1.34 | -4.8% | ok |
| `macross_default`ᵖ | 142 | ▆▅▄▃▂▁▂▃ | -$38.20 | -3.8% | -0.21 | -7.1% | ok |
| `bollinger_v2_tuned`ⁿ | 91 | ▁▂▃▅▆▇█▇ | +$67.80 | +6.8% | 1.62 | -2.3% | ok |
| `bollinger_fg_contra`ʳ | 14 | ▃▂▁ | -$4.20 | -0.4% | — | -1.1% | n_too_low |
```

Common subsequent sections on the replay report:

- `§ 02 — Bars in period · by symbol` — health-check on the data
  layer; shows bar count, first/last timestamps, gap count per
  symbol
- `§ 03 — Run summary` — phase-by-phase status of the run
  (fetch / signals / execute / analytics) with duration and notes
- `§ 04 — Notes` — only present when there's a specific reason
  (Week 1 empty-state explanation, regime-change observation,
  data-quality issue). Default to absent.

---

## v2 pattern — temporal reports

For: weekly A/B reports (`reports/ab/YYYY-WW.md`), walk-forward
recommendations (`recommendations/YYYY-MM-DD.md`), monthly pattern
surfacing (`reviews/YYYY-MM-patterns.md`).

The v2 ticker innovates on v1 with:

**A period toggle.** Wagon-watcher v2 has `Today / 7d / 30d /
All`. Algotrading-paper's A/B reports use `7d / 30d / All` (no
"Today" — too few trades to make a daily-Δ meaningful).
Recommendations reports use `since-promotion / 30d / All`.

**Movers framing.** Sort by `abs(Δ)` so most-changed rows sit
at top, regardless of sign. A/B reports sort by `abs(Sharpe Δ vs
predecessor)`. Recommendations reports sort by `abs(backtest P&L
Δ vs live)`.

**Sparkline column on every row.** Per-variant 30d P&L curve
rendered with `▁▂▃▄▅▆▇█` characters in monospace. Phone-readable,
no images.

Header example (weekly A/B):

```
algotrading-paper / a-b · weekly

Week 18 (2026-04-26 → 2026-05-02)  ·  4 variants live

2026-05-02 17:00:00 UTC

[↗ replay](reports/2026-05-02-replay.md)  ·  [↗ recommendations](recommendations/2026-05-02.md)
```

Four-stat band example:

```
Variants live

4

3 phase-qualified

Promotions this week

1

`bollinger_v2_tuned`

Movers (abs Δ Sharpe)

3

over 0.20

Significance hits

1

p<0.05 over 100+
```

Dominant table example:

```
§ Movers · sorted by abs(Δ Sharpe vs predecessor) DESC

7d  30d  All

| Variant | n | 30d sparkline | P&L | Sharpe | Δ Sharpe | p |
| --- | --- | --- | --- | --- | --- | --- |
| `bollinger_v2_tuned`ⁿ | 91 | ▁▂▃▅▆▇█▇ | +$67.80 | 1.62 | +0.28 | 0.04 |
| `macross_default`ᵖ | 142 | ▆▅▄▃▂▁▂▃ | -$38.20 | -0.21 | -0.55 | 0.18 |
| `bollinger_fg_contra`ʳ | 14 | ▃▂▁ | -$4.20 | — | — | n_low |
| `bollinger_default`ᵖ | 287 | ▄▅▆▇█▇▆▇ | +$112.40 | 1.34 | — | base |
```

Reading-the-row legend (always present on v2 reports):

```
### Reading the row

ᵖ phase-qualified (cleared for Phase 2 if reached)
ⁿ newly promoted (last 7 days)
ʳ under recommendation review

n  trade count in period (lower = noisier estimate)
sparkline  30d P&L curve, normalized per row
Δ Sharpe  vs registered predecessor; "base" if no predecessor
p  significance of A/B comparison; "n_low" if fewer than 30 trades

Sub-30-trade rows are shown for completeness; treat their Sharpe and Δ as unreliable.
```

---

## Anomalies and flags section

Above the dominant table when any of:

- A run failed in the period
- A position-limit check rejected an order (logged in `decisions`
  with action='rejected')
- A variant breached the playbook §1 drawdown threshold
- A walk-forward recommendation triggered the playbook §2
  too-good-to-be-true heuristics
- A context source has been failing for >24h
- The Phase 2 paper-vs-real variance has exceeded 30% (Phase 2
  only; warning level before the 50% exit trigger)

Format:

```
🔴 § Flags · 2 active

▸ Run failed at 2026-05-02T14:00 — Alpaca returned 503; retry succeeded at T14:05

▸ `bollinger_fg_contra` 30d drawdown -12.4% (threshold -10%) — playbook §1
  drawdown investigation pending
```

Each flag is a single line, prefixed with `▸`. The 🔴 in the
section header is the SBB-red signal indicator. When the section
is empty, it's collapsed to a single line:

```
§ Flags · none
```

placed below the dominant table.

---

## Trade ID rendering — full detail

In tables, trade IDs are the link target:

```
[`#0142`](https://app.alpaca.markets/paper/orders/0142)
```

In prose, same format:

> The signal at 14:32 produced trade [`#0142`], which exited at
> +5.1% via the take-profit trigger.

For multi-trade references, list them: `#0142 #0143 #0145`.
Don't summarize as "3 trades" without IDs visible —
identifiability is the point.

For proposed-but-not-placed trades (in walk-forward
recommendation reports), use the placeholder: `[#proposed]`.
Same monospace, no link target.

---

## Numeric formatting summary

| Type | Format | Example | Empty state |
| --- | --- | --- | --- |
| Currency | `$N,NNN.NN` | `$1,247.34` | `—` |
| Percentage | `±N.NN%` | `+5.23%` | `—` |
| Ratio | `N.NN` | `1.34`, `-0.21` | `—` |
| Count | `N` | `347`, `0` | `—` |
| ISO timestamp | `YYYY-MM-DDTHH:MM:SSZ` | `2026-05-02T16:06:29Z` | `—` |
| Human time | `Mmm DD, HH:MM UTC` | `May 02, 16:06 UTC` | `—` |
| Sparkline | 8-char unicode | `▁▂▃▄▅▆▇█` | (omit column) |
| Variant name | `` `name` `` | `` `bollinger_default` `` | `—` |
| Trade ID | `` [`#NNNN`](url) `` | `` [`#0142`](...) `` | `[#proposed]` |

Right-align numeric columns. Left-align identifier columns. Zero
is a real value (`0`, `$0.00`, `0.0%`). Em-dash is "value not yet
present." Get this distinction right — it's the load-bearing
piece of the empty-state convention.

---

## Marginalia footer

Always present. Always at the bottom. Plain text, low visual
priority, no decoration.

```
---

paper-api.alpaca.markets/v2/orders  ·  generated by replay.py v0.1.3

[github.com/pwysocan-droid/algotrading-paper](https://github.com/pwysocan-droid/algotrading-paper)
```

The data-source URL is the canonical provenance. The version
string allows reports from different code versions to be compared.
The GitHub link is the surface anchor.

---

## Implementation note: render module

A small report-renderer module (`render.py` or similar) that takes
a structured input (dict-like) and emits the markdown report saves
duplicate formatting code across `replay.py`, `render_index.py`,
and the weekly outputs that come online in Week 4. Whether to
extract this in Week 1 or wait until Week 4 (when the A/B report
appears) is Claude Code's call. The spec is consistent either way.

The render module should expose:

- `render_v1_report(data: dict) -> str` for snapshot reports
- `render_v2_report(data: dict) -> str` for temporal reports
- `render_index(state: dict) -> str` for the project hub page
- Utilities for the four-stat band, the flags section, the
  numeric formatting, and the trade ID linking

---

## What this spec does NOT cover

- **Notification/alerting surfaces.** Deferred until Week 2's live
  cron lands; designed at that point.
- **Styled HTML rendering surface.** Deferred decision per the
  roadmap; markdown + GitHub default rendering is the Week 1
  baseline. The HTML preview files in `/mnt/user-data/outputs/`
  serve as visual reference for the design direction if/when
  the HTML surface gets built.
- **Phase-review documents.** `phase1-review.md` and
  `phase2-review.md` are decision documents with their own
  structure, not routine reports.
- **Decision-log entries.** Have their own format established in
  `decision-log.md`.
- **Adversarial-review files.** `reviews/YYYY-WW-friday.md` are
  prose, not data reports. Different format, separate spec when
  needed.

The spec covers `INDEX.md`, `replay.py` output, `week-N-status.md`,
the weekly A/B reports (`reports/ab/`), the recommendation reports
(`recommendations/`), and the monthly pattern-surfacing reviews
(`reviews/YYYY-MM-patterns.md`).

---

## Build instruction for Week 1

Claude Code's Week 1 deliverables include three artifacts that
follow this spec:

1. **`replay.py` output** — produces `reports/YYYY-MM-DD-replay.md`
   in v1 pattern. Empty-state Week 1 version uses em-dashes
   throughout the four-stat band where appropriate, explicit `0`
   where zero is a real value.

2. **`week-1-status.md`** — produced manually or by a small script
   at end of Week 1. v1 pattern. Reports what was built, what
   tests pass, what's deferred.

3. **`INDEX.md`** — produced by `render_index.py`. v1 pattern with
   project-level four-stat band. Regenerated after any artifact
   commit.

Implementation note: building the render module (above) early
saves duplicate work later. Building it as the *last* Week 1
deliverable, refactored from the inline rendering in `replay.py`
once the format is concrete, is also defensible.

The empty-state must be a fully-formed report — same header,
same four-stat band (with em-dashes for not-yet-present values
and explicit zeros for real-zero values), same dominant table
(with explicit "no variants registered" placeholder rows), same
footer. *Not* a placeholder report saying "no data yet."
