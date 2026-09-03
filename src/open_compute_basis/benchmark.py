from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from .confidence import grade, is_stale
from .hashing import quantize_money
from .normalize import assign_series, normalize_offers
from .settings import Settings


def median(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return quantize_money((ordered[mid - 1] + ordered[mid]) / 2)


def percentile(values: list[Decimal], p: float) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    idx = (len(ordered) - 1) * p
    lo = int(idx)
    hi = min(lo + 1, len(ordered) - 1)
    frac = Decimal(str(idx - lo))
    return quantize_money(ordered[lo] + (ordered[hi] - ordered[lo]) * frac)


def drop_outliers(values: list[Decimal], k: Decimal) -> list[Decimal]:
    if len(values) < 4:
        return list(values)
    q1 = percentile(values, 0.25)
    q3 = percentile(values, 0.75)
    mid = median(values)
    if q1 is None or q3 is None or mid is None:
        return list(values)
    iqr = q3 - q1
    if iqr == 0:
        return list(values)
    lo, hi = mid - k * iqr, mid + k * iqr
    return [v for v in values if lo <= v <= hi]


def calculate_series(
    offers: list[dict[str, Any]],
    series_id: str,
    now: str,
    settings: Settings,
) -> dict[str, Any]:
    bench = settings.raw["benchmark"]
    members = [o for o in offers if series_id in o.get("series_ids", [])]
    by_provider: dict[str, list[Decimal]] = defaultdict(list)
    sources: set[str] = set()
    timestamps: dict[str, str | None] = {}
    for offer in members:
        by_provider[str(offer["provider"])].append(offer["usd_per_gpu_hour"])
        sources.add(str(offer["source"]))
        timestamps[str(offer["source"])] = offer.get("captured_at")
    provider_medians = {p: median(vs) for p, vs in sorted(by_provider.items())}
    provider_medians = {p: v for p, v in provider_medians.items() if v is not None}
    sample = drop_outliers(list(provider_medians.values()), Decimal(str(bench["outlier_iqr_k"])))
    value = median(sample)
    q1 = percentile(sample, 0.25)
    q3 = percentile(sample, 0.75)
    stale = any(
        is_stale(ts, now, int(settings.raw["freshness"]["max_age_hours"])) for ts in timestamps.values()
    ) if timestamps else True
    confidence, status, flags = grade(
        provider_count=len(provider_medians),
        source_count=len(sources),
        stale=stale,
        iqr=(q1, q3) if q1 is not None and q3 is not None else None,
        median=value,
        min_providers_high=int(bench["high_confidence_min_providers"]),
        min_sources_high=int(bench["high_confidence_min_source_feeds"]),
    )
    unspecified = sum(1 for o in members if "VARIANT_UNSPECIFIED" in (o.get("quality_flags") or []))
    if unspecified:
        flags.append("VARIANT_UNSPECIFIED")
    return {
        "series_id": series_id,
        "status": status if value is not None else "NO_PRINT",
        "usd_per_gpu_hour": value,
        "iqr": [q1, q3] if q1 is not None and q3 is not None else None,
        "provider_count": len(provider_medians),
        "offer_count": len(members),
        "source_count": len(sources),
        "confidence": confidence if value is not None else "D",
        "quality_flags": flags if value is not None else flags + (["NO_PRINT"] if not members else []),
        "source_timestamps": timestamps,
        "provider_medians": provider_medians,
        "methodology_version": settings.methodology_version,
    }


def build_offers(
    receipts: dict[str, Any],
    settings: Settings,
) -> list[dict[str, Any]]:
    offers: list[dict[str, Any]] = []
    for source, receipt in receipts.items():
        payload = receipt.get("payload") or {}
        captured = receipt.get("captured_at")
        for offer in normalize_offers(source, payload, captured):
            offer["series_ids"] = assign_series(offer, settings.series)
            offers.append(offer)
    return offers


def calculate_all(offers: list[dict[str, Any]], now: str, settings: Settings) -> dict[str, Any]:
    return {series_id: calculate_series(offers, series_id, now, settings) for series_id in settings.series}
