# Sim-to-live calibration — 2026-07-24

Window: 2026-07-16T21:00:00+00:00 → 2026-07-24T03:34:02.949798+00:00 · identical bars, costs, and constraints on both sides. Divergence here means the factory's verdicts on candidates deserve less trust.

| variant | side | placed | closed | wins | P&L | stop/tp/time |
| --- | --- | --- | --- | --- | --- | --- |
| null_baseline | live | 43 | 38 | 16 | $-62.37 | 7/1/30 |
| null_baseline | sim | 41 | 41 | 17 | $-53.20 | 6/1/34 |
| volume_thrust_regime_shift | live | 0 | 0 | 0 | $0.00 | 0/0/0 |
| volume_thrust_regime_shift | sim | 1 | 1 | 0 | $-0.46 | 0/0/1 |
| weekend_illiquidity_momentum | live | 0 | 0 | 0 | $0.00 | 0/0/0 |
| weekend_illiquidity_momentum | sim | 0 | 0 | 0 | $0.00 | 0/0/0 |

Small windows are noisy — divergence matters once closed counts reach ~30/side. Deterministic variants should match near-exactly; see parity_check.py for the per-signal version.
