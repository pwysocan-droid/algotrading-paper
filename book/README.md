# The Book — registry root (CONSTITUTION Art. 2, 4.4)

Public, timestamped underwriting registry. `positions.jsonl` is the
single source of truth the mechanical conflict gate (scripts/conflict_check.py,
Art. 4.2) reads. One JSON object per line:
`{ts, instrument, venue, side, status, structural_worst_case_pct}` with
status in {pending, open, closed}. Pre-registrations (candidate specs) live
here as `pre-reg-*.md`, committed BEFORE any position (2.1, 2.5).
