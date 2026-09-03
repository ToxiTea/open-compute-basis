from decimal import Decimal

from open_compute_basis.normalize import assign_series, normalize_offers
from open_compute_basis.settings import load_settings


def test_hourly_divided_by_gpu_count_and_nulls_dropped():
    payload = {
        "plans": [
            {
                "provider": "DigitalOcean",
                "plan_id": "gpu-h100x8-640gb",
                "price_hourly_usd": 35.28,
                "gpu_model": "H100",
                "gpu_count": 8,
            },
            {
                "provider": "OVHcloud",
                "plan_id": "h100-null",
                "price_hourly_usd": None,
                "gpu_model": "H100",
                "gpu_count": 8,
            },
        ]
    }
    offers = normalize_offers("gpucloudcompare", payload, "2026-09-02T03:30:02Z")
    assert len(offers) == 1
    assert offers[0]["usd_per_gpu_hour"] == Decimal("4.410000")


def test_spot_and_incompatible_variants_excluded_from_sxm():
    settings = load_settings()
    payload = {
        "plans": [
            {"provider": "A", "plan_id": "h100-spot", "price_hourly_usd": 1.0, "gpu_model": "H100", "gpu_count": 1},
            {"provider": "B", "plan_id": "nvl", "price_hourly_usd": 2.0, "gpu_model": "H100NVL", "gpu_count": 1},
            {"provider": "C", "plan_id": "pcie", "price_hourly_usd": 3.0, "gpu_model": "H100 PCIe", "gpu_count": 1},
            {"provider": "D", "plan_id": "sxm", "price_hourly_usd": 4.0, "gpu_model": "NVIDIA H100 SXM5", "gpu_count": 1},
        ]
    }
    offers = normalize_offers("gpucloudcompare", payload, "2026-09-02")
    for offer in offers:
        offer["series_ids"] = assign_series(offer, settings.series)
    by_id = {o["offer_id"]: o for o in offers}
    assert "OCB-H100-SXM-OD-GLOBAL" not in by_id["h100-spot"]["series_ids"]
    assert "OCB-H100-SXM-OD-GLOBAL" not in by_id["nvl"]["series_ids"]
    assert "OCB-H100-SXM-OD-GLOBAL" not in by_id["pcie"]["series_ids"]
    assert "OCB-H100-SXM-OD-GLOBAL" in by_id["sxm"]["series_ids"]
