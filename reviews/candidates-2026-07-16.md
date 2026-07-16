# Candidate synthesis — 2026-07-16

model claude-opus-4-8 · called_from candidate_synthesis · logged to llm_calls

The LLM surfaces; the discipline decides. Every candidate below runs
the gauntlet: implemented → 6-month constrained replay → scored by
edge per constraint slot → top 2 registered live against null_baseline.

---

## 1. `liquidation_cascade_reclaim`

**Thesis.** After a violent down-spike that overshoots (forced liquidations, not information), the first 5m bar that reclaims the pre-spike level marks exhausted forced sellers and a mean snap-back exceeding 5%.

**Lens.** Descends from retail 'buy the wick / capitulation reversal' bots. This class died when applied blindly to every dip (caught falling knives), but the specific variant that waited for a *confirmed reclaim* after a statistical outlier down-move survived through 2018-2022 in crypto specifically because liquidation-driven overshoots are a structural, recurring inefficiency absent in equities. It fails in slow bleed regimes — needs the spike to be a genuine tail event, not trend.

**Entry rule.** Window: 288 bars (24h). Compute per-bar log return r_t = ln(close_t/close_{t-1}). Compute rolling std sigma of r over last 288 bars. Identify a 'cascade bar' in the last 6 bars where r_t <= -4*sigma AND the bar's (high-low)/close >= 0.02 (wide-range panic bar). Let P_pre = high of the bar immediately preceding the cascade bar. BUY on the latest bar t only if: (a) a cascade bar occurred within the prior 6 bars, (b) latest close > P_pre (reclaim), (c) latest bar volume > 1.5x the 288-bar average volume, (d) no cascade-BUY fired on this symbol in the prior 12 bars. Otherwise nothing.

**Params.** `{"lookback_bars": 288, "sigma_mult": 4.0, "min_range_pct": 0.02, "cascade_search_bars": 6, "vol_mult": 1.5, "reclaim_confirm": true}`

**Expected fire rate.** ~0.1-0.3 signals per symbol per day. 4-sigma events are rare by construction (~1-2 per symbol per day of candidate cascades, most fail the reclaim+volume filter). Across 5 symbols, ~1 signal/day total. Deliberately starves the constraint slots so each fire is high-conviction.

**Fee survival.** Post-cascade reclaims are the highest-amplitude reversals in crypto — historical snap-backs off 4-sigma liquidation wicks commonly run 3-8% within hours, comfortably clearing the +5% TP before the -3% stop and dwarfing 0.6% fees. The overshoot magnitude *is* the edge.

## 2. `btc_leads_alt_lag_capture`

**Thesis.** When BTC makes a decisive impulse move that alts have not yet matched within the same 15-minute window, the alt closes the gap — a lead-lag arbitrage visible entirely in synchronized OHLCV.

**Lens.** Classic retail 'BTC dominance / correlation lag' play. Pure lead-lag latency arbitrage was fully arbitraged away on sub-second horizons by HFT, but on 5-minute bars for mid-cap alts (SOL, LINK, AVAX) a residual catch-up persists because retail flow reprices alts more slowly than BTC. Survived as a discretionary desk pattern; only worked in backtests when people ignored that BTC's move must be *fresh* and the alt *genuinely lagging*, not already correlated-moving.

**Entry rule.** Requires BTC bars alongside the traded symbol (strategy requests BTCUSD window). Window: 36 bars. Compute BTC 3-bar (15m) return btc_ret = close_btc_t/close_btc_{t-3} - 1. Compute same-window alt return alt_ret. BUY the alt (SOL/LINK/AVAX only — not BTC/ETH) on latest bar if: (a) btc_ret >= 0.012 (BTC impulse up >=1.2% over 15m), (b) alt_ret < 0.5*btc_ret (alt captured less than half the move — the lag), (c) alt latest-bar volume > 1.2x its 36-bar avg (participation confirming, not dead), (d) BTC's latest bar close is its 6-bar high (impulse still intact, not reversing). Otherwise nothing.

**Params.** `{"window_bars": 36, "btc_lookback_bars": 3, "btc_impulse_pct": 0.012, "lag_ratio": 0.5, "alt_vol_mult": 1.2, "traded_symbols": ["SOL", "LINK", "AVAX"]}`

**Expected fire rate.** ~0.2-0.5 signals per alt per day, concentrated in high-volatility BTC sessions. Across 3 eligible alts, ~1 signal/day. Fires in clusters during trend days, silent on chop days — desirable selectivity.

**Fee survival.** Alts historically overshoot BTC's move on catch-up (beta >1.5 to BTC on impulse legs), so a 1.2% BTC move that the alt lagged typically resolves into a 2-4% alt move as it converges and overshoots — clears 0.6% fees and can reach the +5% TP on strong trend days.

## 3. `dead_zone_range_break`

**Thesis.** A tight low-volume range formed during the Asian/overnight dead-zone, broken on expanding volume as the active session opens, resolves directionally by more than 1% because compressed volatility releases.

**Lens.** Retail 'opening range breakout' / volatility-compression lineage (Toby Crabel via crypto forums). In equities the RTH open ORB degraded as everyone front-ran it; in 24/7 crypto the analog survived longer because the 'session open' (EU/US waking) is a real recurring liquidity injection after genuinely dead overnight ranges. Died in backtests when people took every range break — false breaks in mid-session chop. The dead-zone precondition is what filters it.

**Entry rule.** Window: 288 bars, and use bar timestamps (UTC). Define dead-zone as UTC 00:00-06:00. Over the most recent completed dead-zone, compute range R = (max high - min low)/min low. A valid coil requires R <= 0.015 (sub-1.5% overnight range) AND dead-zone avg volume < 0.6x the 288-bar avg volume. After 07:00 UTC, BUY on the latest bar if: (a) a valid coil existed this session, (b) latest close > dead-zone max high * 1.001 (clean upside break), (c) latest bar volume >= 2x dead-zone avg volume (session-open expansion), (d) time is between 07:00-12:00 UTC, (e) only first break per symbol per day. Otherwise nothing.

**Params.** `{"window_bars": 288, "deadzone_start_utc": 0, "deadzone_end_utc": 6, "max_coil_range": 0.015, "deadzone_vol_ratio": 0.6, "break_buffer": 0.001, "vol_expansion_mult": 2.0, "session_window_utc": [7, 12]}`

**Expected fire rate.** At most 1 per symbol per day (first-break-only, gated to a 5h window and requiring a valid overnight coil). Realistically ~0.3 per symbol per day since many nights don't coil tightly. ~1-1.5 signals/day across 5 symbols.

**Fee survival.** Volatility-compression releases expand toward the day's full range; a sub-1.5% overnight coil breaking on 2x volume historically resolves 2-5% intraday. The compression ratio is the edge — the tighter the coil, the larger the expected release relative to the 0.6% fee floor.

## 4. `volume_thrust_regime_shift`

**Thesis.** A single bar with extreme volume AND range relative to recent history marks institutional-scale repositioning that initiates a multi-hour trend, not noise — enter on the confirmation bar after the thrust.

**Lens.** Descends from retail volume-spike / 'smart money footprint' strategies. Naive volume-spike entries lost money (spikes often mark exhaustion tops). The survivor variant, documented in crypto momentum research 2019-2022, requires volume AND directional range AND a non-reversing confirmation bar — filtering exhaustion spikes from initiation spikes. Works in trending regimes, bleeds in ranges, hence the strict confirmation.

**Entry rule.** Window: 288 bars. Compute vol_z = (vol_t - mean_vol)/std_vol over 288 bars. Identify a 'thrust bar' among the last 3 bars where vol_z >= 3.0 AND the bar is up (close>open) AND (close-open)/open >= 0.008. BUY on latest bar if: (a) a thrust bar occurred in the last 3 bars, (b) latest close > thrust bar's close (confirmation, no immediate rejection), (c) latest close > 288-bar VWAP (proxy: sum(close*vol)/sum(vol)) — trend alignment, (d) latest bar not a bearish engulfing of thrust bar, (e) one entry per symbol per 12 bars. Otherwise nothing.

**Params.** `{"window_bars": 288, "vol_zscore": 3.0, "thrust_body_pct": 0.008, "thrust_search_bars": 3, "confirm_above_thrust": true, "cooldown_bars": 12}`

**Expected fire rate.** ~0.2-0.4 per symbol per day. 3-sigma volume bars occur a few times daily per symbol but most fail the up-body, VWAP-alignment, and confirmation filters. ~1-2 signals/day across 5 symbols.

**Fee survival.** Genuine initiation thrusts (vol_z>=3 with directional body above VWAP) historically precede 2-6% continuation legs as the repositioning plays out over hours, clearing fees. The VWAP+confirmation gate is specifically designed to reject the exhaustion spikes that produce sub-1% fizzles.

## 5. `weekend_illiquidity_momentum`

**Thesis.** During low-liquidity weekend sessions, sustained directional moves face less mean-reverting counterflow and thus persist further than identical weekday moves, so weekend momentum continuation clears the fee floor more reliably.

**Lens.** Retail 'weekend crypto is thin, moves run' folklore — one of the few crypto-specific regime edges with documented statistical support (weekend returns show higher autocorrelation and lower reversal than weekday in 2017-2021 studies). It decayed as weekend volume rose post-2021 institutionalization, so this is a regime bet that the replay must validate is still alive. Honest risk: this may be the candidate that's already arbitraged away.

**Entry rule.** Window: 72 bars (6h). Use timestamps: active only Saturday and Sunday UTC. Compute 12-bar (1h) return mom = close_t/close_{t-12} - 1. Compute the 72-bar realized volatility sigma_h (std of 1-bar returns * sqrt(12)). BUY on latest bar if: (a) day is Sat or Sun UTC, (b) mom >= 0.015 (>=1.5% hourly momentum), (c) mom/sigma_scaled >= 2 where sigma_scaled = std of hourly returns over 72 bars (momentum is significant vs recent vol), (d) latest 3 bars all closed above their opens (clean persistence, no wobble), (e) one entry per symbol per 12 bars. Otherwise nothing.

**Params.** `{"window_bars": 72, "mom_lookback_bars": 12, "mom_threshold": 0.015, "signif_ratio": 2.0, "persistence_bars": 3, "cooldown_bars": 12, "active_days_utc": ["Sat", "Sun"]}`

**Expected fire rate.** ~0.3-0.6 per symbol on weekend days only, zero on weekdays. Effective ~2/7 of the week active. Averages well under 1 signal/symbol/day over a full week — very slot-efficient.

**Fee survival.** The thesis is precisely that weekend moves overshoot: a significant 1.5% hourly thrust in thin conditions historically extended another 2-4% before reverting, giving room to hit +5% TP. If replay shows weekend edge has decayed to <1% net moves, this candidate is designed to fail fast and be cut.

---

## What was deliberately avoided

Left behind entirely: (1) All oscillator/band mean-reversion (RSI, Bollinger, Stochastic, MA-crossover) — retired in Phase 1, and structurally incompatible with a +5%/-3% asymmetric exit that demands directional follow-through, not fades. (2) Frequency-maximizing 'signal every bar' designs — the constraint math (99.6% signal death, 5 slots, 1h cooldown) inverts the usual fitness function, so every candidate is engineered to fire <1x/symbol/day with conviction rather than optimize hit-rate at scale. (3) Any edge requiring order-book, funding, sentiment, or cross-exchange data — bars only. (4) Small-edge/high-turnover statistical arb (the classic quant retail template) — a +0.03% gross edge is structurally dead under a 0.6% fee floor; every candidate targets moves plausibly >1% and ideally reaching the +5% TP, so the exit structure and fee floor jointly define admissibility. The unifying aggression: I optimized for *amplitude per slot* and chose crypto-structural inefficiencies (liquidation overshoots, BTC lead-lag, dead-zone compression, weekend thinness) over indicator patterns, because only structural overshoots produce the tail-sized moves these fixed exits need. The weekend candidate is included as an honest regime bet most likely to be the one that dies in replay.
