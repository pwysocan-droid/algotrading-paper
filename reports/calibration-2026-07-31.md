# Sim-to-live calibration — 2026-07-31

Window: 2026-07-16T21:00:00+00:00 → 2026-07-31T03:34:04.009149+00:00 · identical bars, costs, and constraints on both sides. Divergence here means the factory's verdicts on candidates deserve less trust.

| variant | side | placed | closed | wins | P&L | stop/tp/time |
| --- | --- | --- | --- | --- | --- | --- |
| null_baseline | live | 79 | 74 | 32 | $-101.28 | 10/1/63 |
| null_baseline | sim | 79 | 78 | 32 | $-97.59 | 8/1/69 |
| volume_thrust_regime_shift | live | 0 | 0 | 0 | $0.00 | 0/0/0 |
| volume_thrust_regime_shift | sim | 1 | 1 | 0 | $-0.46 | 0/0/1 |
| weekend_illiquidity_momentum | live | 0 | 0 | 0 | $0.00 | 0/0/0 |
| weekend_illiquidity_momentum | sim | 4 | 4 | 1 | $-1.41 | 0/1/3 |

Small windows are noisy — divergence matters once closed counts reach ~30/side. Deterministic variants should match near-exactly; see parity_check.py for the per-signal version.
