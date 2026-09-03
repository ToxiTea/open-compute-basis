from __future__ import annotations

from decimal import Decimal
from typing import Any


def grade(
    *,
    provider_count: int,
    source_count: int,
    stale: bool,
    iqr: tuple[Decimal, Decimal] | None,
    median: Decimal | None,
    min_providers_high: int,
    min_sources_high: int,
) -> tuple[str, str, list[str]]:
    """Return (confidence, status, flags). status is CANONICAL | OBSERVATION | NO_PRINT."""
    flags: list[str] = []
    if stale or provider_count == 0 or median is None:
        return "D", "NO_PRINT", (["STALE"] if stale else []) + (["NO_COVERAGE"] if provider_count == 0 else [])
    dispersion = None
    if iqr and median > 0:
        dispersion = (iqr[1] - iqr[0]) / median
        if dispersion > Decimal("1.5"):
            flags.append("WIDE_DISPERSION")
    if provider_count >= min_providers_high and source_count >= min_sources_high and "WIDE_DISPERSION" not in flags:
        return "A", "CANONICAL", flags
    if provider_count >= min_providers_high and source_count == 1:
        flags.append("ONE_SOURCE")
        return "B", "OBSERVATION", flags
    flags.append("THIN_COVERAGE")
    return "C", "OBSERVATION", flags


def is_stale(source_as_of: str | None, now_date: str, max_age_hours: int) -> bool:
    if not source_as_of:
        return True
    # Daily snapshots: compare calendar dates; max_age_hours/24 days of slack.
    try:
        from datetime import date, timedelta

        as_of = date.fromisoformat(source_as_of[:10])
        today = date.fromisoformat(now_date[:10])
        return (today - as_of) > timedelta(hours=max_age_hours)
    except ValueError:
        return True
