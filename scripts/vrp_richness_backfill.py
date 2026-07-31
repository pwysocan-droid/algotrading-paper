"""Backfill the REAL richness distribution from Alpaca historical option bars
(Feb 2024 -> now). Calibration ONLY — how often the entry gate would have been
met — NOT a P&L backtest and NOT a tail-frequency estimate (CONSTITUTION 1.3,
2.3, 1.4). Uses real traded closes (real skew), unlike the flat-VIX proxy.

Reconstructs, for each trading day, the exact spread propose() would pick
(1-realized-SD-OTM short strike, width, ~35-DTE Friday) and reads the real
option closes to get credit/width. mid = close(short)-close(long); we also
report a crossing-haircut version, since the live gate sells bid / buys ask.

Run on the VPS (entitled ALPACA_LIVE_* keys). Writes reports/vrp-richness-backfill.json.
"""
from __future__ import annotations
import json, math, os, statistics, time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests
from dotenv import load_dotenv

REPO = Path(__file__).resolve().parent.parent
load_dotenv(str(REPO / ".env"))
DATA = "https://data.alpaca.markets"
H = {"APCA-API-KEY-ID": os.environ.get("ALPACA_LIVE_KEY_ID", ""),
     "APCA-API-SECRET-KEY": os.environ.get("ALPACA_LIVE_SECRET", "")}

UNDERLYINGS = os.environ.get("BACKFILL_SYMS", "SPY,QQQ,IWM,DIA,GLD,TLT,EEM").split(",")
WIDTH = {"SPY": 5, "QQQ": 5, "IWM": 3, "DIA": 5, "GLD": 5, "TLT": 2, "EEM": 1}
DTE_TARGET = 35
RICH_MIN = 0.20
HAIRCUT_PER_LEG = 0.03      # ~$0.03/leg crossing cost; live sells bid / buys ask
SD_MULT = float(os.environ.get("BACKFILL_SD", "1.0"))   # strike distance in realized SDs
START = os.environ.get("BACKFILL_START", "2024-02-05")  # Alpaca options history start


def stock_bars(sym, start, end):
    r = requests.get(f"{DATA}/v2/stocks/{sym}/bars",
                     params={"timeframe": "1Day", "start": start, "end": end,
                             "limit": 10000, "feed": "iex", "adjustment": "all"},
                     headers=H, timeout=30)
    r.raise_for_status()
    return [(b["t"][:10], b["c"]) for b in (r.json().get("bars") or [])]


def realized_vol(closes):
    rets = [math.log(closes[i] / closes[i-1]) for i in range(1, len(closes)) if closes[i-1] > 0]
    rr = rets[-20:]
    return statistics.pstdev(rr) * math.sqrt(252) if len(rr) > 5 else None


def friday_expiry(d: date) -> date:
    t = d + timedelta(days=DTE_TARGET)
    while t.weekday() != 4:
        t += timedelta(days=1)
    return t


def occ(sym, expiry: date, strike, cp="P"):
    return f"{sym}{expiry:%y%m%d}{cp}{int(round(strike*1000)):08d}"


def option_closes_on(day: str, symbols: list[str]) -> dict:
    """Daily close per option symbol on `day` (one batched call)."""
    r = requests.get(f"{DATA}/v1beta1/options/bars",
                     params={"symbols": ",".join(symbols), "timeframe": "1Day",
                             "start": day, "end": day, "limit": 100},
                     headers=H, timeout=25)
    if not r.ok:
        return {}
    out = {}
    for s, bars in (r.json().get("bars") or {}).items():
        if bars:
            out[s] = bars[0]["c"]
    return out


def main():
    end = datetime.now(timezone.utc).date().isoformat()
    result = {}
    for sym in UNDERLYINGS:
        W = WIDTH[sym]
        series = stock_bars(sym, START, end)
        closes = [c for _, c in series]
        dates = [d for d, _ in series]
        rows = []
        for i in range(21, len(series)):
            d = date.fromisoformat(dates[i])
            spot = closes[i]
            rv = realized_vol(closes[:i+1])
            if not rv:
                continue
            expiry = friday_expiry(d)
            dte = (expiry - d).days
            one_sd = SD_MULT * spot * rv * math.sqrt(dte / 252.0)
            short_k = round((spot - one_sd) / W) * W
            long_k = short_k - W
            os_, ol_ = occ(sym, expiry, short_k), occ(sym, expiry, long_k)
            cl = option_closes_on(dates[i], [os_, ol_])
            if os_ not in cl or ol_ not in cl:
                continue                        # no trade that day on a leg — skip
            credit = cl[os_] - cl[ol_]
            rich_mid = credit / W
            rich_hc = (credit - 2 * HAIRCUT_PER_LEG) / W
            rows.append({"date": dates[i], "spot": round(spot, 2), "rv": round(rv, 3),
                         "short_k": short_k, "long_k": long_k, "credit": round(credit, 2),
                         "rich_mid": round(rich_mid, 3), "rich_hc": round(rich_hc, 3)})
            time.sleep(0.05)
        n = len(rows)
        if not n:
            result[sym] = {"n": 0}
            continue
        rm = sorted(r["rich_mid"] for r in rows)
        hit_mid = sum(1 for r in rows if r["rich_mid"] >= RICH_MIN) / n
        hit_hc = sum(1 for r in rows if r["rich_hc"] >= RICH_MIN) / n
        pct = lambda p: rm[min(n-1, int(n*p/100))]
        result[sym] = {"n": n, "hit_mid": round(hit_mid, 3), "hit_hc": round(hit_hc, 3),
                       "p25": pct(25), "p50": pct(50), "p75": pct(75), "p90": pct(90),
                       "max": rm[-1], "rows": rows}
        print(f"{sym}: n={n}  clears20%(mid)={hit_mid:.1%}  clears20%(haircut)={hit_hc:.1%}"
              f"  median richness={pct(50):.1%}  p90={pct(90):.1%}  max={rm[-1]:.1%}")

    tag = f"{SD_MULT:g}sd".replace(".", "_")
    out = REPO / "reports" / f"vrp-richness-backfill-{tag}.json"
    out.write_text(json.dumps({"generated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                               "window": f"{START}..{end}", "gate": RICH_MIN, "sd_mult": SD_MULT,
                               "method": "real Alpaca option daily closes; mid = short_close-long_close; "
                                         "haircut = 2 x $0.03/leg crossing",
                               "by_underlying": result}, indent=1) + "\n")
    print(f"\nwrote {out.name}")


if __name__ == "__main__":
    raise SystemExit(main())
