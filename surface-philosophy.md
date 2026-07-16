# Surface Philosophy — algotrading-paper

What the mobile/desktop live surface is, what it owes to its
predecessors, and what bar each design decision has to clear before it
lands.

This file is the equivalent of `philosophy.md` for the project itself —
written so that in week 6 of Phase 1, when the temptation arrives to
add a P&L sparkline or a notification badge or a settings panel,
something exists to push back with.

The surface is the architectural sibling of `INDEX.md`. Both regenerate
from the same underlying data. INDEX is the *document surface*; this is
the *living surface*. They are peers, not alternatives.

---

## The animating principle

> **Function-driven poetic solutions.**

Each visual element does one job in the world *and* one job in the
mind. If it does only the first, it's plumbing. If it does only the
second, it's decoration. The whole surface is built from elements that
do both.

The pulsing dot in v0 was decoration: it said "I am alive" but it
didn't tell you *when* the next heartbeat was, *how* the system was
performing, or *what was different* about right now versus a minute
ago. It was a status light. A status light is plumbing dressed up as
poetry.

The SBB Mondaine paddle is the opposite. It sweeps for the cron
interval — a real measurement, mapped to a real angle. It pauses for
the run duration — the held breath is the work happening. It releases
when the run completes — release is the contract being honored.
Three real-world states, three visible gestures. The function *is* the
poetry. The poetry *is* the function. The paddle works because it
refuses to choose between them.

This is the bar. Every element on the surface has to clear it.

---

## Inheritance — the four parents

The surface descends from four design lineages. Each one solved a
problem the project also has, and each one solved it without
ornament.

### 1. SBB · timetable as public utility

Hans Hartmann and Josef Müller-Brockmann's mid-20th-century work on
the Swiss Federal Railways' signage and schedule systems wasn't a
style. It was an **information consistency protocol.** Every station
in Switzerland obeys the same grid, so a traveler in Zürich and a
traveler in Lugano read the same information shape at the same speed.

What the project takes from SBB is not Helvetica (it doesn't use
Helvetica), not the red (used sparingly), and not the iconic Mondaine
clock face (the surface is *missing* its face). What the project takes
is **the discipline of treating information as infrastructure.** A
timetable doesn't tell you stories about trains. It tells you when
trains are. The accumulation rows don't tell you stories about data.
They tell you what has been accumulated. The departures logic in
`pending` doesn't editorialize about decisions. It lists what's
waiting and when it's due.

### 2. ECAL · typography that disappears into its load

The post-Karl-Gerstner generation working out of ECAL Lausanne — Aurèle
Sack, Maximilian Schachtner, the broader contemporary Swiss practice —
pushes typography toward calibration so precise that the reader stops
seeing it as typography. The text isn't "set"; it just *is*. The same
move applies here. The surface has no decorative type. Inter does the
human work. JetBrains Mono does the numeric work. They don't switch
weights for emphasis; emphasis comes from *position* and *spacing*,
the way it does in a well-set book page.

When a future reader of this document thinks "the surface needs more
visual interest" — that's the moment to remember that *visual
interest* is what the surface deliberately does not provide. The
interest is the *information*. The typography is the conveyance.

### 3. Tufte · respect for the reader's attention

The cardinal sin in Tufte's *Visual Display of Quantitative
Information* is the *data-ink ratio* problem: visual elements that
consume reader attention without conveying information. Cards consume
attention (their borders, their padding, their drop shadows all
demand cognitive cycles) and convey only the information "I am a
thing." Tabular rows consume only the attention required to read the
numbers in them.

The v0 had cards in the `growing` zone. v1 doesn't. The data is the
same; the attention cost is lower. Tufte's discipline is the test:
*can I remove this without losing information?* If yes, remove it.

### 4. Playfair · time-and-quantity as spatial relationship

William Playfair's 1786 *Commercial and Political Atlas* invented the
line chart and the bar chart in the same book, because he was trying
to show British trade flows to politicians who didn't have time to
read tables. He took *quantities over time* — an abstract relationship
— and turned it into *positions on a page* — a spatial one.

The sparklines in `accumulating` are direct descendants of Playfair.
The timetable is a Playfair construct (date is a spatial position,
event is the content at that position). The paddle clock is a Playfair
construct at the smallest possible scale: time-until-next-event as an
*angle*. Whenever the surface shows a quantity, it tries to show it
*spatially* before it shows it as a number.

---

## The three axes

The project is animated by three things, and the surface visualizes
the relationships between them.

### Time

Cron interval (5 min). Sweep window (4m 50s). Hold window (~10s,
variable). Cycle position (the paddle angle). Time-to-next-event
(`pending` "when" column). Days-elapsed and days-remaining (`state`
and `timetable`). 24-hour delta (`accumulating` deltas).

Time is *not* a clock-face in the human-readable sense (no "19:24
UTC" as a feature). Time is *intervals between commitments*. The
timestamp in the masthead is provenance, not function.

### Information

What has accumulated (`accumulating`). What has been decided (the
`decisions` count and, by proxy, the decision log itself). What the
state of the experiment is (`state` rows).

Information is *the project remembering itself*. The accumulation
rows are not "stats." They are the **project's memory becoming
visible.**

### Human behavior

What the human is being asked to do next (`pending`). What cognitive
bias is most likely to fire today (Kahneman block). What discipline
the operator has committed to (the footer phrase: *the experiencing
self runs · the remembering self decides*).

Human behavior is the **axis the project does not control.** The
surface's job, on this axis, is to make the operator's coming
decisions *visible to themselves before they make them*. That is what
the Kahneman block is doing. That is what `pending` is doing. The
goal is not to nudge the operator toward a decision; the goal is to
make the operator *see* the decision they are about to make.

---

## What the surface is NOT

These framings exist because each is a temptation the surface will
face as it lives.

- **Not a trading dashboard.** No P&L. No equity curve. No win rate.
  Those belong in the weekly A/B reports, where the discipline of the
  100-trade minimum can be enforced. Putting them on an ambient
  surface defeats the discipline by making them *glanceable* — which
  is the cognitive distortion the surface should *prevent*, not
  reinforce.

- **Not a notification system.** No badges. No "you have 3 pending."
  The surface is *consulted*, not pushed. The operator decides when to
  look. If the operator never looks, the surface costs nothing.

- **Not a control panel.** No buttons. No knobs. No "enable/disable
  variant" toggles. The surface is read-only. Writes happen via the
  decision log, via git commits, via deliberate offline acts. The
  surface is the *outcome* of those acts becoming visible — not the
  origin of them.

- **Not real-time.** The data refreshes on the cron's cadence (5
  minutes), not on a WebSocket. There is no `connected` indicator.
  There is no race against the market. The whole metaphor of the
  paddle is that *time has a cadence* and the surface obeys it.

- **Not a public dashboard.** Public-readable, yes (the repo is
  public). But the audience is the operator. The audience is the
  operator at 11pm on a Thursday wondering whether the cron has been
  running for the last 4 hours. The surface is designed for *that
  person*, not for portfolio reviewers, not for prospective employers,
  not for Twitter screenshots.

- **Not a place for project commentary.** The Kahneman block is the
  only philosophical element, and it appears only when triggered. It
  does not contain quotes-of-the-day, weather, the operator's mood,
  or aphorisms about markets. The footer phrase is the *single*
  persistent piece of non-data text. One sentence. Earned by being
  the only one.

---

## The three tiers — what each does

The surface is organized in three tiers of visual weight, not by
"section" but by **what the eye reaches first when scanning under
load.**

### Tier 1 — vital signs

The masthead, the headless paddle, the last-run/next-run pair, and
the four-row `state` block. These are the page's *headline*. They
answer: *Is the system breathing? Where is it in the cycle? What's
true about the experiment right now?*

These elements use the largest type. They have the most negative
space around them. They are visually committed to before any other
zone.

### Tier 2 — open work

The `pending` block. These are the items that require human
attention, ordered with the most-urgent gate at the top. Tier 2 has
its own grid (thing / when / kind) and its own visual weight — less
than Tier 1, but more than the ambient zones below.

The "when" column uses lighter color for `open` items (no clock
running) and full-weight color for time-bounded items (`10d`, `5d`).
This is a function-driven hierarchy: *open* literally means *not
on the timetable*; the visual treatment matches the semantic.

### Tier 3 — ambient context

The `accumulating` table, the `timetable`, and the Kahneman block.
These are the surface's *background music*. They reward looking but
do not demand it. The Kahneman block is in this tier deliberately —
even at its most useful, it should not visually outweigh the items
in `pending` that are asking for actual decisions.

---

## Specific elements — function-and-poetry pairings

What each non-obvious element is doing on both axes. New elements
have to be defensible on both before they're added.

### The headless paddle

*Function.* Visualizes cron cycle position. Sweeps over the
4m50s-ish sweep window, holds at 12 for the ~10s execution window,
releases when the run completes. The hold-duration *is* the run
duration; a long hold means the run is taking longer than usual,
which is itself a signal. The paddle's position at any moment is the
answer to "when is the next thing happening."

*Poetry.* A clock with no face is asking the viewer to read *the
gesture of the hand*, not *the time*. Which is what the project is
doing: asking the operator to read *the rhythm of accumulation*, not
*the numbers on the dashboard*. The missing face is the conceptual
move. The paddle is in SBB red because — like the Mondaine — the red
is reserved for the moving part: *the part of the system that is
currently working.*

### The sparklines

*Function.* Show the 24-hour shape of each accumulation. A flat line
means no change; a climb means accumulation is happening. The visual
shape is read in 200ms; the count is read in 800ms; the delta is
read in 500ms. The sparkline is the *first* element the eye returns
to on second glance.

*Poetry.* Sparklines descend directly from Playfair via Tufte.
They're the smallest possible Playfair: a quantity-over-time as a
single line of block characters. The fact that they're rendered in
Unicode block elements (▁▂▃▄▅▆▇█) rather than SVG is a discipline:
**they cost zero rendering complexity and zero design budget.** They
work in plain text, in markdown, in terminals, in emails.

### The canonical row grammar

**Every row on this surface that pairs a quantity with a label uses
the same column structure:**

    name (left)  →  number (center)  →  delta (right)  →  sparkline (far right)

The eye scans left-to-right and learns this once. It reads:
*what is this · how much of it · how is it changing · what's the
shape of the change.* Applied consistently across `state` and
`accumulating`. Vitals is exempt (the paddle clock is its
sparkline). Pending is exempt (days-remaining is a straight
diagonal, not a shape — if pending earns a graphic, it would be a
filling bar, not a sparkline). Timetable is exempt (the list as a
whole is the time-graphic).

The grammar is **mono throughout**, with one typographic register:
- *Number* is the largest element. Same size in every row (18px),
  except the gate-bearing number which gets 26px — the only break
  in scale on the surface.
- *Delta* is small italic, in teal when the delta is positive, in
  ghost-faint when zero, in faint italic for textual notes.
- *Sparkline* is one line of block characters. Teal-dim when the
  series is growing; ghost-faint when the series is empty.

**Teal is reserved for accumulation.** When the project is
accumulating value — a positive delta, a climbing sparkline, an
urgent countdown approaching a gate, the "now" marker in the
timetable — the color teal appears. When no real change is
happening, the row is gray. The discipline: teal occurrences should
be rare enough that seeing one means something.

### The pending "when" column

*Function.* Tells the operator how many days until each item is due,
or `open` if no clock applies.

*Poetry.* The same column used by every transit system on earth. A
departures board in any major train station has this column in
exactly this position (right-aligned, smaller than the destination,
with a unit suffix). The familiarity is doing work: the operator
does not have to learn how to read this surface, because they have
been reading this column shape their entire life.

### The Kahneman block

*Function.* Surfaces a cognitive bias relevant to the operator's
current situation. The trigger comes from project state (day index,
phase, week-within-curriculum, proximity to gate). The body is a
named bias plus its specific implication for the current moment.

*Poetry.* The block is set in the same vocabulary as everything
else on the surface — hairline borders, ECAL-quiet type, no
decorative weight — because **the discipline of the project is to
take cognitive biases as seriously as data points.** A flashing
warning would say "this is special, pay attention." Same-weight
typography says "this is true the same way the other data is true."

### The footer phrase

*Function.* Reminds the operator of the project's two-self
discipline: the *experiencing* self executes the runs; the
*remembering* self makes the decisions in the decision log. The
surface is for the experiencing self; the decision log is for the
remembering self. The phrase is the bridge.

*Poetry.* The single italic line at the bottom of every page. Inherits
the closing-marginalia tradition of the wagon-watcher project, but
inverts it: in wagon-watcher the marginalia was provenance; here it's
*premise.*

---

## Tests for proposed additions

When a new element is proposed for the surface, it has to pass all
five of these before it's added.

1. **Does it visualize a measurement that exists?** No "engagement
   indicators," no "trader sentiment," no metrics fabricated to fill
   a slot. The measurement has to be a real column in a real table.

2. **Does it answer a question the operator actually asks?** Not "a
   question someone might ask" or "a question I asked once." A
   question the operator *currently* asks, *frequently*. If the
   operator doesn't ask the question, the surface shouldn't answer
   it.

3. **Does it do both jobs — function and poetry?** A new element
   that's only useful is plumbing (move to INDEX.md). A new element
   that's only beautiful is decoration (do not add). Both, or
   neither.

4. **Is it quiet enough to live next to the other elements?** If it
   needs accent color, bold weight, or decorative chrome to "land,"
   it isn't calibrated. Calibrate down until it can live in the
   neighborhood. If that's not possible, it doesn't belong.

5. **Will it still make sense at 3am in week 6 when the operator is
   half-asleep?** The surface's job is to be legible *under reduced
   attention*. If the element requires the operator to be sharp to
   read correctly, it fails its purpose.

---

## What to re-read this for

- When tempted to add a P&L sparkline → *Not a trading dashboard.*
- When tempted to add notifications → *Not a notification system.*
- When tempted to add toggles → *Not a control panel.*
- When tempted to add a "quote of the day" → *One sentence. Earned
  by being the only one.*
- When tempted to make the Kahneman block "stand out more" → *Same-
  weight typography says: this is true the same way the other data is
  true.*
- When tempted to put the surface on a public dashboard → *The
  audience is the operator at 11pm on a Thursday.*
- When tempted to make it real-time → *Time has a cadence. The
  surface obeys it.*

The discipline is that **the surface gets less, not more, as the
project matures.** Mature systems have fewer parts that do more work.
The v0 had six zones; v1 has the same information distributed across
four tiers with sharper hierarchy. v2, if there is one, should have
fewer visible elements, not more.

If a future revision adds a zone, it has to *also remove one.* The
surface holds at a maximum complexity; new function displaces old.
That's how it stays scannable in 3 seconds in year two.
