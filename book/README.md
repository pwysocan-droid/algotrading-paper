# The Book — registry root (CONSTITUTION Art. 2, 4.4)

Timestamped underwriting registry for the trading machine. `positions.jsonl`
is the ledger: one JSON object per line
`{ts, instrument, venue, side, status, structural_worst_case_pct}`,
status in {pending, open, closed}. Candidate specs are pre-registered here
as `pre-reg-*.md`, committed BEFORE any position (2.1, 2.5). No public
publishing — the honesty is for the operator (4.4).
