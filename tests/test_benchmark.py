from decimal import Decimal

from open_compute_basis.benchmark import calculate_series, drop_outliers, median
from open_compute_basis.settings import load_settings


def _offer(provider: str, price: str, source: str = "gpucloudcompare") -> dict:
    return {
        "provider": provider,
        "usd_per_gpu_hour": Decimal(price),
        "source": source,
        "captured_at": "2026-09-02T00:00:00Z",
        "series_ids": ["OCB-H100-SXM-OD-GLOBAL"],
        "quality_flags": [],
    }


def test_median_of_provider_medians():
    settings = load_settings()
    offers = [
        _offer("A", "1.00"),
        _offer("A", "100.00"),  # provider A median 50.5 would dominate a raw median
        _offer("B", "3.00"),
        _offer("C", "5.00"),
    ]
    # A listings 1 and 100 → median 50.5; then cross-provider median(50.5, 3, 5)
    result = calculate_series(offers, "OCB-H100-SXM-OD-GLOBAL", "2026-09-02T12:00:00Z", settings)
    assert result["provider_count"] == 3
    assert result["usd_per_gpu_hour"] == median(
        [Decimal("50.500000"), Decimal("3.000000"), Decimal("5.000000")]
    )
    assert result["status"] == "OBSERVATION"
    assert result["confidence"] == "B"
    assert "ONE_SOURCE" in result["quality_flags"]


def test_two_sources_can_be_canonical():
    settings = load_settings()
    offers = [
        _offer("A", "3.00", "gpucloudcompare"),
        _offer("B", "3.20", "gpucloudcompare"),
        _offer("C", "3.40", "other_feed"),
        _offer("A", "3.10", "other_feed"),
        _offer("B", "3.30", "other_feed"),
        _offer("C", "3.50", "gpucloudcompare"),
    ]
    result = calculate_series(offers, "OCB-H100-SXM-OD-GLOBAL", "2026-09-02T12:00:00Z", settings)
    assert result["source_count"] == 2
    assert result["status"] == "CANONICAL"
    assert result["confidence"] == "A"


def test_outlier_drop():
    kept = drop_outliers(
        [Decimal("3"), Decimal("3.2"), Decimal("3.4"), Decimal("3.1"), Decimal("400")],
        Decimal("8"),
    )
    assert Decimal("400") not in kept
