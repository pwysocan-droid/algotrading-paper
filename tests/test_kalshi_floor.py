"""Charter E Stage 0 floor-study pure logic — bucketing, documented fee, and the
lower-bound cost aggregation. No network, no DB, no orders."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "venues" / "kalshi"))
import floor_report as fr  # noqa: E402


def test_price_bucket_edges_and_tails():
    assert fr.price_bucket(0.03) == (0.0, 0.05)
    assert fr.price_bucket(0.50) == (0.50, 0.55)
    assert fr.price_bucket(0.97) == (0.95, 1.00)
    assert fr.price_bucket(None) is None
    assert fr.is_tail((0.0, 0.05)) and fr.is_tail((0.95, 1.00))
    assert not fr.is_tail((0.50, 0.55))


def test_kalshi_fee_rounds_up_to_cent():
    # 0.07 * 0.05 * 0.95 = 0.003325 -> ceil to $0.01
    assert fr.kalshi_fee(0.05) == 0.01
    # 0.07 * 0.5 * 0.5 = 0.0175 -> ceil to $0.02
    assert fr.kalshi_fee(0.50) == 0.02
    assert fr.kalshi_fee(None) is None


def test_bucket_stats_aggregates_cost_lower_bound():
    rows = [
        {"mid": 0.05, "spread": 0.02, "yes_bid_size": 10, "yes_ask_size": 20, "ticker": "A"},
        {"mid": 0.06, "spread": 0.04, "yes_bid_size": 5, "yes_ask_size": 5, "ticker": "B"},
        {"mid": 0.50, "spread": 0.01, "yes_bid_size": 100, "yes_ask_size": 100, "ticker": "C"},
    ]
    stats = {s["bucket"]: s for s in fr.bucket_stats(rows)}
    tail = stats["0.05-0.10"]
    assert tail["tail"] and tail["n_markets"] == 2
    # median spread of {0.02,0.04}=0.03; fee at mid 0.075 = ceil(0.07*.075*.925*100)/100=0.01
    # all-in LB = 0.03 + 2*0.01 = 0.05
    assert tail["median_spread"] == 0.03
    assert math.isclose(tail["allin_roundtrip_cost_lower_bound"], 0.05, abs_tol=1e-9)
    assert not stats["0.50-0.55"]["tail"]
