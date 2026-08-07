# Sim-to-live calibration — 2026-08-07

Window: 2026-07-16T21:00:00+00:00 → 2026-08-07T03:34:02.996975+00:00 · identical bars, costs, and constraints on both sides. Divergence here means the factory's verdicts on candidates deserve less trust.

| variant | side | placed | closed | wins | P&L | stop/tp/time |
| --- | --- | --- | --- | --- | --- | --- |
| null_baseline | live | 117 | 112 | 42 | $-165.93 | 17/4/91 |
| null_baseline | sim | 115 | 114 | 43 | $-133.69 | 11/4/99 |
| volume_thrust_regime_shift | live | 1 | 1 | 0 | $-7.08 | 1/0/0 |
| volume_thrust_regime_shift | sim | 2 | 2 | 0 | $-5.22 | 0/0/2 |
| weekend_illiquidity_momentum | live | 0 | 0 | 0 | $0.00 | 0/0/0 |
| weekend_illiquidity_momentum | sim | 8 | 8 | 2 | $-3.40 | 1/2/5 |

Small windows are noisy — divergence matters once closed counts reach ~30/side. Deterministic variants should match near-exactly; see parity_check.py for the per-signal version.
