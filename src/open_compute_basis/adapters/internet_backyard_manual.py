from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..settings import Settings
from .base import AdapterResult

REQUIRED = {
    "source",
    "source_as_of_date",
    "gpu",
    "form_factor",
    "headline",
    "providers",
    "provider_displayed_count_total",
    "quality_flags",
    "source_url",
}


class InternetBackyardManualAdapter:
    name = "internet_backyard_manual"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cfg = settings.sources[self.name]
        self.records_dir = settings.root / self.cfg["records_dir"]

    def collect(self, *, fixture: Any | None = None) -> AdapterResult:
        records = [fixture] if fixture is not None else self._load_records()
        validated = [validate_record(r) for r in records if r]
        return AdapterResult(
            source=self.name,
            role="comparison",
            captured_at=None,
            source_as_of=validated[-1]["source_as_of_date"] if validated else None,
            payload={"records": validated},
            attribution=self.cfg["attribution"],
            license=self.cfg["license"],
            quality_flags=["MANUAL", "COMPARISON_ONLY"],
        )

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.records_dir.exists():
            return []
        out = []
        for path in sorted(self.records_dir.glob("*.json")):
            with path.open(encoding="utf-8") as fh:
                out.append(json.load(fh))
        return out


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    missing = REQUIRED - set(record)
    if missing:
        raise ValueError(f"internet backyard record missing {sorted(missing)}")
    if record.get("source") != "internet_backyard_manual":
        raise ValueError("source must be internet_backyard_manual")
    headline = record["headline"]
    for key in ("usd_per_gpu_hour", "provider_count", "listing_count"):
        if key not in headline:
            raise ValueError(f"headline missing {key}")
        _require_number(headline[key], f"headline.{key}")
    displayed = 0
    for provider in record["providers"]:
        for key in ("median_usd_per_gpu_hour", "middle_50_low", "middle_50_high", "displayed_count"):
            _require_number(provider[key], f"provider.{key}")
        displayed += int(provider["displayed_count"])
    flags = list(record.get("quality_flags") or [])
    for required in ("MANUAL", "COMPARISON_ONLY"):
        if required not in flags:
            flags.append(required)
    if displayed != int(record["headline"]["listing_count"]):
        if "COUNT_MISMATCH" not in flags:
            flags.append("COUNT_MISMATCH")
    if int(record["provider_displayed_count_total"]) != displayed:
        if "COUNT_MISMATCH" not in flags:
            flags.append("COUNT_MISMATCH")
    record = dict(record)
    record["quality_flags"] = flags
    record["constituent_of_ocb"] = False
    if "captured_at" not in record:
        record["captured_at"] = None
    return record


def write_record(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    validated = validate_record(record)
    if path.exists():
        raise FileExistsError(f"manual records are append-only; {path} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(validated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return validated


def _require_number(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if isinstance(value, float) and value != value:
        raise ValueError(f"{name} is NaN")
