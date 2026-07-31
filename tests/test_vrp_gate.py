"""Book gate v2 (CONSTITUTION 2.9) — the trailing-percentile + floor logic that
governs whether a real paper spread is written. Locked so a refactor can't
silently change the gate."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import vrp_harvester as v  # noqa: E402


def test_trailing_pctl_reads_seed_and_shadow(tmp_path, monkeypatch):
    # synthetic backfill seed: 100 rising richness values for SPY
    seed = {"by_underlying": {"SPY": {"rows": [
        {"date": f"2025-01-{i:02d}" if i < 32 else f"2025-02-{i-31:02d}",
         "rich_hc": round(0.01 * i, 4)} for i in range(1, 101)]}}}
    bf = tmp_path / "bf.json"
    bf.write_text(json.dumps(seed))
    sh = tmp_path / "shadow.jsonl"
    sh.write_text("")  # no forward obs yet
    monkeypatch.setattr(v, "BACKFILL_1SD", bf)
    monkeypatch.setattr(v, "SHADOW", sh)
    monkeypatch.setattr(v, "GATE_PCTL", 90)
    monkeypatch.setattr(v, "GATE_WINDOW", 252)
    thr = v.trailing_pctl("SPY")
    # p90 of 0.01..1.00 ≈ 0.90-0.91 range
    assert 0.88 <= thr <= 0.92


def test_trailing_pctl_none_below_min_history(tmp_path, monkeypatch):
    bf = tmp_path / "bf.json"
    bf.write_text(json.dumps({"by_underlying": {"SPY": {"rows": [
        {"date": f"2025-01-{i:02d}", "rich_hc": 0.1} for i in range(1, 10)]}}}))
    sh = tmp_path / "shadow.jsonl"
    sh.write_text("")
    monkeypatch.setattr(v, "BACKFILL_1SD", bf)
    monkeypatch.setattr(v, "SHADOW", sh)
    assert v.trailing_pctl("SPY") is None  # <30 obs → no percentile claim


def test_fire_rate_counts_only_1sd_with_decision(tmp_path, monkeypatch):
    sh = tmp_path / "shadow.jsonl"
    rows = [
        {"arm": "1sd", "gate_pass": True},
        {"arm": "1sd", "gate_pass": False},
        {"arm": "1sd", "gate_pass": False},
        {"arm": "0.5sd", "gate_pass": None},   # control arm — excluded
        {"arm": "1sd", "gate_pass": None},     # no decision — excluded
    ]
    sh.write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setattr(v, "SHADOW", sh)
    rate, n = v.fire_rate()
    assert n == 3 and abs(rate - 1 / 3) < 1e-9
