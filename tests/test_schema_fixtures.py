from open_compute_basis.normalize import normalize_offers


def test_missing_fields_and_bad_prices_are_dropped():
    payload = {
        "plans": [
            {"provider": "A"},
            {"provider": "B", "plan_id": "x", "price_hourly_usd": 0, "gpu_model": "H100", "gpu_count": 1},
            {"provider": "C", "plan_id": "y", "price_hourly_usd": -1, "gpu_model": "H100", "gpu_count": 1},
            {"provider": "D", "plan_id": "z", "price_hourly_usd": "nope", "gpu_model": "H100", "gpu_count": 1},
            {"provider": "E", "plan_id": "ok", "price_hourly_usd": 2.5, "gpu_model": "H100", "gpu_count": 1},
        ]
    }
    offers = normalize_offers("gpucloudcompare", payload, "2026-09-02")
    assert [o["offer_id"] for o in offers] == ["ok"]


def test_empty_source_outage():
    assert normalize_offers("gpucloudcompare", {"plans": []}, "2026-09-02") == []
    assert normalize_offers("unknown", {}, None) == []
