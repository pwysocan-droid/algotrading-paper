"""Predictability-ceiling study — the instrument-exemption ML measurement.

Decision-log 2026-07-18 ruling 2: generic walk-forward ML over OHLCV
features may MEASURE the maximum edge available to the rule class;
nothing here may ever be deployed. The question it answers: if a
flexible learner with full feature-engineering hindsight can't extract
a net-of-cost edge from 5-min OHLCV at any horizon, no hand-crafted
rule drawn from the same input space will — and the daily foundry's
search domain is bounded above by this number.

Selection window ONLY (through 2026-01-01); the holdout stays unburned.
Walk-forward: expanding-window fits, quarterly refits, strictly
out-of-sample predictions. Economic scoring uses the platform's full
cost model on top-decile |signal| bars.

    python scripts/ceiling_study.py [--db research_bars.db]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
from config import SLIPPAGE_PCT, TAKER_FEE_PCT, WATCHED_SYMBOLS

REPO_ROOT = Path(__file__).resolve().parent.parent
SELECTION_END = "2026-01-01T00:00:00+00:00"
HORIZONS_BARS = {"1h": 12, "3h": 36, "6h": 72, "12h": 144, "24h": 288,
                 "3d": 864, "1w": 2016, "2w": 4032}
REFIT_EVERY = 288 * 90          # quarterly
MIN_TRAIN = 288 * 120           # 4 months before first prediction
ROUND_TRIP_COST = 2 * (TAKER_FEE_PCT + SLIPPAGE_PCT)   # fraction, both legs


def load_closes(conn, symbol: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = conn.execute(
        "SELECT timestamp, close, volume, high, low FROM bars"
        " WHERE symbol = ? AND timestamp < ? ORDER BY timestamp ASC",
        (symbol, SELECTION_END),
    ).fetchall()
    ts = np.array([r["timestamp"] for r in rows])
    close = np.array([r["close"] for r in rows], dtype=float)
    vol = np.array([r["volume"] for r in rows], dtype=float)
    high = np.array([r["high"] for r in rows], dtype=float)
    low = np.array([r["low"] for r in rows], dtype=float)
    return ts, close, np.stack([vol, high, low])


def build_features(close: np.ndarray, aux: np.ndarray) -> np.ndarray:
    """~20 standard OHLCV features, all strictly backward-looking."""
    vol, high, low = aux
    logc = np.log(np.clip(close, 1e-12, None))
    r1 = np.diff(logc, prepend=logc[0])

    def lag_sum(x, n):
        c = np.cumsum(x)
        out = c - np.concatenate([np.zeros(n), c[:-n]])
        out[:n] = 0.0
        return out

    def roll_std(x, n):
        c1 = lag_sum(x, n) / n
        c2 = lag_sum(x * x, n) / n
        return np.sqrt(np.clip(c2 - c1 * c1, 0, None))

    feats = []
    for n in (1, 3, 12, 36, 144, 288):
        feats.append(lag_sum(r1, n))                     # momentum, multiple lags
    for n in (12, 72, 288):
        feats.append(roll_std(r1, n))                    # realized vol
    v_ma = lag_sum(vol, 288) / 288
    feats.append(np.where(v_ma > 0, vol / np.clip(v_ma, 1e-12, None), 1.0))  # vol ratio
    rng = np.clip(high - low, 1e-12, None)
    feats.append((close - low) / rng)                    # close position in range
    r_ma = lag_sum(rng / np.clip(close, 1e-12, None), 72) / 72
    feats.append(np.where(r_ma > 0, (rng / np.clip(close, 1e-12, None)) / np.clip(r_ma, 1e-12, None), 1.0))
    for n in (36, 288):                                  # distance from rolling mean
        ma = lag_sum(logc, n) / n
        feats.append(logc - ma)
    feats.append(np.sign(r1))                            # last-bar sign
    X = np.stack(feats, axis=1)
    return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)


def walk_forward(X, y, model_name: str) -> np.ndarray:
    """Strictly out-of-sample predictions; expanding window, quarterly refit."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import Ridge

    preds = np.full(len(y), np.nan)
    start = MIN_TRAIN
    while start < len(y):
        end = min(start + REFIT_EVERY, len(y))
        tr = slice(0, start)
        if model_name == "ridge":
            mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9
            m = Ridge(alpha=10.0)
            m.fit((X[tr] - mu) / sd, y[tr])
            preds[start:end] = m.predict((X[start:end] - mu) / sd)
        else:
            m = HistGradientBoostingRegressor(
                max_iter=150, max_depth=4, learning_rate=0.05,
                l2_regularization=1.0, random_state=17)
            m.fit(X[tr], y[tr])
            preds[start:end] = m.predict(X[start:end])
        start = end
    return preds


def score_horizon(conn, horizon: str, k: int) -> dict:
    per_model: dict = {}
    for model_name in ("ridge", "gbm"):
        all_pred, all_fwd = [], []
        for symbol in WATCHED_SYMBOLS:
            _ts, close, aux = load_closes(conn, symbol)
            if len(close) < MIN_TRAIN + k + 10:
                continue
            X = build_features(close, aux)
            logc = np.log(np.clip(close, 1e-12, None))
            fwd = np.concatenate([logc[k:] - logc[:-k], np.full(k, np.nan)])
            valid = ~np.isnan(fwd)
            # predict on decision bars only every k bars? keep all bars,
            # trades scored non-overlapping below via stride k
            pred = walk_forward(X[valid], fwd[valid], model_name)
            all_pred.append(pred)
            all_fwd.append(fwd[valid])
        pred = np.concatenate(all_pred)
        fwd = np.concatenate(all_fwd)
        ok = ~np.isnan(pred)
        pred, fwd = pred[ok], fwd[ok]
        ic = float(np.corrcoef(pred, fwd)[0, 1]) if len(pred) > 10 else None

        # economic ceiling: trade top-decile |signal| in signal direction,
        # non-overlapping stride k, full round-trip cost
        idx = np.arange(0, len(pred), k)
        p_s, f_s = pred[idx], fwd[idx]
        thresh = np.quantile(np.abs(p_s), 0.9)
        sel = np.abs(p_s) >= thresh
        gross = np.sign(p_s[sel]) * f_s[sel]
        net = gross - ROUND_TRIP_COST
        per_model[model_name] = {
            "oos_ic": ic,
            "n_trades": int(sel.sum()),
            "gross_mean_pct": float(gross.mean() * 100) if sel.sum() else None,
            "net_mean_pct": float(net.mean() * 100) if sel.sum() else None,
            "net_positive": bool(net.mean() > 0) if sel.sum() else None,
        }
        print(f"  {horizon} {model_name}: IC={ic:+.4f} n={sel.sum()} "
              f"gross={gross.mean()*100:+.3f}% net={net.mean()*100:+.3f}%")
    return per_model


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=REPO_ROOT / "research_bars.db")
    parser.add_argument("--horizons", default=None,
                        help="comma-separated subset, e.g. '3d,1w,2w'")
    args = parser.parse_args()

    todo = ([h.strip() for h in args.horizons.split(",")]
            if args.horizons else list(HORIZONS_BARS))
    results = {}
    with db.connect(args.db) as conn:
        for horizon, k in ((h, HORIZONS_BARS[h]) for h in todo):
            print(f"horizon {horizon} (k={k}):")
            results[horizon] = score_horizon(conn, horizon, k)

    date = datetime.now(timezone.utc).date().isoformat()
    out = REPO_ROOT / "reports" / f"ceiling-study-{date}.json"
    out.write_text(json.dumps({
        "date": date,
        "selection_end": SELECTION_END,
        "round_trip_cost_pct": ROUND_TRIP_COST * 100,
        "note": "instrument-exemption measurement (decision-log 2026-07-18 "
                "ruling 2); nothing here is deployable",
        "results": results,
    }, indent=2) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
