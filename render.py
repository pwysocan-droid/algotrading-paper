"""Markdown report renderer — v1 (snapshot) pattern.

Implements the format conventions in report-format-spec.md:
  - em-dash empty states (— means slot exists, value not yet present;
    0 / $0.00 means zero is a real value)
  - four-stat summary band immediately under the header
  - § section markers with · separator

Exports for Week 1:
  - render_v1_report(data) — for replay.py and week-N-status.md
  - render_index(state)   — for INDEX.md

render_v2_report (temporal pattern) is deferred to Week 4 when the first
weekly A/B report appears.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

EMDASH = "—"
RENDER_VERSION = "0.1.0"

GITHUB_REPO_URL = "https://github.com/pwysocan-droid/algotrading-paper"
ALPACA_PAPER_ORDERS_URL = "https://app.alpaca.markets/paper/orders"
ALPACA_PROVENANCE = "paper-api.alpaca.markets/v2/orders"


def format_currency(value: float | None) -> str:
    if value is None:
        return EMDASH
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def format_pct(value: float | None) -> str:
    if value is None:
        return EMDASH
    sign = "+" if value > 0 else ("-" if value < 0 else "")
    return f"{sign}{abs(value):.2f}%"


def format_ratio(value: float | None) -> str:
    if value is None:
        return EMDASH
    return f"{value:.2f}"


def format_count(value: int | None) -> str:
    if value is None:
        return EMDASH
    return f"{value:,}"


def format_iso_ts(value: datetime | None) -> str:
    if value is None:
        return EMDASH
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_human_time(value: datetime | None) -> str:
    if value is None:
        return EMDASH
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%b %d, %H:%M UTC")


def format_variant_name(name: str | None) -> str:
    if not name:
        return EMDASH
    return f"`{name}`"


def format_trade_id(
    trade_id: int | str | None,
    base_url: str = ALPACA_PAPER_ORDERS_URL,
    proposed: bool = False,
) -> str:
    if proposed:
        return "[#proposed]"
    if trade_id is None:
        return EMDASH
    if isinstance(trade_id, int):
        rendered = f"#{trade_id:04d}"
    else:
        rendered = f"#{trade_id}"
    return f"[`{rendered}`]({base_url}/{trade_id})"


_SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"


def format_sparkline(values: list[float] | None) -> str:
    if not values:
        return EMDASH
    lo = min(values)
    hi = max(values)
    if hi == lo:
        return _SPARKLINE_CHARS[len(_SPARKLINE_CHARS) // 2] * len(values)
    span = hi - lo
    out = []
    for v in values:
        idx = int(round((v - lo) / span * (len(_SPARKLINE_CHARS) - 1)))
        out.append(_SPARKLINE_CHARS[idx])
    return "".join(out)


@dataclass
class Stat:
    label: str
    value: str  # already-formatted (caller chooses currency/count/etc.)
    sublabel: str = EMDASH


@dataclass
class HeaderBlock:
    title: str  # e.g., "algotrading-paper / replay"
    subtitle: str  # e.g., "Variant — null  ·  Period — 2026-04-02 → 2026-05-02 (30d)"
    timestamp: datetime
    count_summary: str  # e.g., "0 trades"
    links: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class TableSpec:
    columns: list[str]
    rows: list[list[str]]
    empty_row_message: str = "no data in period"
    section_marker: str = "§ 01 — Data"


def render_header_block(header: HeaderBlock) -> str:
    lines = [f"# {header.title}", ""]
    lines.append(header.subtitle)
    lines.append("")
    lines.append(format_iso_ts(header.timestamp))
    lines.append("")
    lines.append(header.count_summary)
    if header.links:
        lines.append("")
        lines.append("  ·  ".join(f"[{label}]({url})" for label, url in header.links))
    return "\n".join(lines)


def render_four_stat_band(stats: list[Stat]) -> str:
    if len(stats) != 4:
        raise ValueError(f"four-stat band requires exactly 4 stats, got {len(stats)}")
    header = "| " + " | ".join(s.label for s in stats) + " |"
    align = "| " + " | ".join(":---" for _ in stats) + " |"
    values = "| " + " | ".join(f"**{s.value}**" for s in stats) + " |"
    sublabels = "| " + " | ".join(s.sublabel for s in stats) + " |"
    return "\n".join([header, align, values, sublabels])


def render_flags_section(flags: list[str], collapsed_when_empty: bool = True) -> str:
    if not flags:
        return "§ Flags · none"
    header = f"🔴 § Flags · {len(flags)} active"
    body = "\n\n".join(f"▸ {flag}" for flag in flags)
    return f"{header}\n\n{body}"


def render_table(spec: TableSpec) -> str:
    lines = [f"## {spec.section_marker}", ""]
    if not spec.rows:
        empty_row = [spec.empty_row_message] + [EMDASH] * (len(spec.columns) - 1)
        rows = [empty_row]
    else:
        rows = spec.rows
    header = "| " + " | ".join(spec.columns) + " |"
    align = "| " + " | ".join("---" for _ in spec.columns) + " |"
    lines.append(header)
    lines.append(align)
    for row in rows:
        if len(row) != len(spec.columns):
            raise ValueError(
                f"row has {len(row)} cells, expected {len(spec.columns)}: {row!r}"
            )
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_marginalia_footer(
    provenance_url: str = ALPACA_PROVENANCE,
    generator: str | None = None,
    repo_url: str = GITHUB_REPO_URL,
) -> str:
    gen = generator or f"render.py v{RENDER_VERSION}"
    repo_label = repo_url.removeprefix("https://").removeprefix("http://")
    lines = [
        "---",
        "",
        f"{provenance_url}  ·  generated by {gen}",
        "",
        f"[{repo_label}]({repo_url})",
    ]
    return "\n".join(lines)


def render_v1_report(data: dict[str, Any]) -> str:
    """Render a v1-pattern (snapshot) markdown report.

    `data` shape (all keys optional unless noted; missing keys render as
    em-dashes or empty-state placeholders):
      - title (required): "algotrading-paper / replay"
      - subtitle (required): "Variant — null  ·  Period — ..."
      - timestamp (required, datetime)
      - count_summary (required): "0 trades"
      - links: [(label, url), ...]
      - stats (required): list of 4 Stat objects
      - flags: list of flag strings (default empty → collapsed below table)
      - dominant_table (required): TableSpec
      - sub_tables: list of TableSpec
      - notes: str (renders as § 04 — Notes section, optional)
      - generator: override generator string in footer
      - provenance_url: override provenance string in footer
    """
    required = ("title", "subtitle", "timestamp", "count_summary", "stats", "dominant_table")
    for key in required:
        if key not in data:
            raise ValueError(f"render_v1_report: missing required key {key!r}")

    header = HeaderBlock(
        title=data["title"],
        subtitle=data["subtitle"],
        timestamp=data["timestamp"],
        count_summary=data["count_summary"],
        links=data.get("links", []),
    )
    flags: list[str] = data.get("flags", [])

    sections: list[str] = []
    sections.append(render_header_block(header))
    sections.append(render_four_stat_band(data["stats"]))

    if flags:
        sections.append(render_flags_section(flags))

    sections.append(render_table(data["dominant_table"]))

    for sub in data.get("sub_tables", []):
        sections.append(render_table(sub))

    if data.get("notes"):
        sections.append("## § 04 — Notes\n\n" + data["notes"])

    if not flags:
        sections.append(render_flags_section([]))

    sections.append(
        render_marginalia_footer(
            provenance_url=data.get("provenance_url", ALPACA_PROVENANCE),
            generator=data.get("generator"),
        )
    )

    return "\n\n".join(sections) + "\n"


def render_index(state: dict[str, Any]) -> str:
    """Render INDEX.md for the project root.

    `state` shape:
      - phase (required): "Phase 1" | "Phase 2" | "Phase 1 — Week 0" etc.
      - week (required, int or str)
      - timestamp (required, datetime)
      - latest_links (required): [(label, url), ...] up to 2
      - stats (required): list of 4 Stat objects (project-level four-stat band)
      - flags: list of flag strings (project-level only)
      - surfaces (required): list of dicts:
            {"surface": str, "filename": str | None,
             "generated": datetime | None, "status": str}
      - reading_order (required): list of (surface_label, prose_para) tuples — 5 paragraphs
      - foundational_docs (required): list of (label, path) tuples
    """
    required = ("phase", "week", "timestamp", "stats", "surfaces", "reading_order",
                "foundational_docs")
    for key in required:
        if key not in state:
            raise ValueError(f"render_index: missing required key {key!r}")

    sections: list[str] = []

    title = "algotrading-paper"
    subtitle_parts = [str(state["phase"]), f"Week {state['week']}"]
    subtitle = "  ·  ".join(subtitle_parts)

    header = HeaderBlock(
        title=title,
        subtitle=subtitle,
        timestamp=state["timestamp"],
        count_summary=f"{len(state['surfaces'])} surfaces tracked",
        links=state.get("latest_links", []),
    )
    sections.append(render_header_block(header))
    sections.append(render_four_stat_band(state["stats"]))

    flags: list[str] = state.get("flags", [])
    if flags:
        sections.append(render_flags_section(flags))

    surface_rows: list[list[str]] = []
    for s in state["surfaces"]:
        filename = s.get("filename") or EMDASH
        generated = s.get("generated")
        gen_str = format_iso_ts(generated) if generated else EMDASH
        status = s.get("status", EMDASH)
        if filename != EMDASH:
            filename_cell = f"[{filename}]({filename})"
        else:
            filename_cell = EMDASH
        surface_rows.append([s["surface"], filename_cell, gen_str, status])

    sections.append(
        render_table(
            TableSpec(
                section_marker="§ 01 — Surfaces",
                columns=["Surface", "Latest", "Generated", "Status"],
                rows=surface_rows,
                empty_row_message="no surfaces yet",
            )
        )
    )

    reading_lines = ["## § 02 — Reading order", ""]
    for label, prose in state["reading_order"]:
        reading_lines.append(f"**{label}** — {prose}")
        reading_lines.append("")
    sections.append("\n".join(reading_lines).rstrip())

    foundational_lines = ["## § 03 — Foundational documents", ""]
    for label, path in state["foundational_docs"]:
        foundational_lines.append(f"- [{label}]({path})")
    sections.append("\n".join(foundational_lines))

    if not flags:
        sections.append(render_flags_section([]))

    sections.append(
        render_marginalia_footer(
            provenance_url=state.get("provenance_url", ALPACA_PROVENANCE),
            generator=state.get("generator", f"render_index.py v{RENDER_VERSION}"),
        )
    )

    return "\n\n".join(sections) + "\n"
