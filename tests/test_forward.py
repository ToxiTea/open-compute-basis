from decimal import Decimal

from open_compute_basis.forward import ladders_from_kalshi


def test_implied_median_and_nonmonotone_flag():
    payload = {
        "markets": [
            {
                "ticker": "A",
                "title": "H100 above",
                "yes_sub_title": "4.00",
                "yes_bid_dollars": "0.80",
                "yes_ask_dollars": "0.80",
                "close_time": "2026-09-30T20:00:00Z",
            },
            {
                "ticker": "B",
                "title": "H100 above",
                "yes_sub_title": "5.00",
                "yes_bid_dollars": "0.55",
                "yes_ask_dollars": "0.55",
                "close_time": "2026-09-30T20:00:00Z",
            },
            {
                "ticker": "C",
                "title": "H100 above",
                "yes_sub_title": "6.00",
                "yes_bid_dollars": "0.40",
                "yes_ask_dollars": "0.40",
                "close_time": "2026-09-30T20:00:00Z",
            },
        ]
    }
    ladders = ladders_from_kalshi(payload)
    assert len(ladders) == 1
    assert ladders[0]["implied_median_strike"] == Decimal("6.000000")
    assert ladders[0]["not_a_forward_price"] is True

    payload["markets"][1]["yes_bid_dollars"] = "0.90"
    payload["markets"][1]["yes_ask_dollars"] = "0.90"
    broken = ladders_from_kalshi(payload)[0]
    assert "NONMONOTONE" in broken["quality_flags"]
    assert broken["implied_median_strike"] is None
