from __future__ import annotations

from typing import Any

from ..http import fetch_json
from ..settings import Settings
from .base import AdapterResult


class GpuCloudCompareAdapter:
    name = "gpucloudcompare"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cfg = settings.sources[self.name]

    def collect(self, *, fixture: Any | None = None) -> AdapterResult:
        payload = fixture if fixture is not None else fetch_json(
            self.cfg["endpoint"],
            timeout=float(self.settings.raw["http"]["timeout_seconds"]),
            retries=int(self.settings.raw["http"]["retries"]),
            backoff=float(self.settings.raw["http"]["retry_backoff_seconds"]),
            headers={"User-Agent": self.settings.raw["http"]["user_agent"]},
        )
        if not isinstance(payload, dict) or "plans" not in payload:
            raise ValueError("gpucloudcompare payload missing plans")
        return AdapterResult(
            source=self.name,
            role="constituent",
            captured_at=payload.get("generated_at") or payload.get("captured_at"),
            source_as_of=payload.get("captured_at"),
            payload=payload,
            attribution=self.cfg["attribution"],
            license=self.cfg["license"],
        )
