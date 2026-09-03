from __future__ import annotations

from typing import Any

from ..http import fetch_json
from ..settings import Settings
from .base import AdapterResult


class ComputableAdapter:
    name = "computable"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cfg = settings.sources[self.name]

    def collect(self, *, fixture: Any | None = None) -> AdapterResult:
        if not self.settings.enable_noncommercial_source:
            return AdapterResult(
                source=self.name,
                role="comparison",
                captured_at=None,
                source_as_of=None,
                payload={"disabled": True, "reason": "ENABLE_NONCOMMERCIAL_SOURCE=false"},
                attribution=self.cfg["attribution"],
                license=self.cfg["license"],
                quality_flags=["DISABLED", "NONCOMMERCIAL"],
            )
        if fixture is not None:
            payload = fixture
        else:
            observations = []
            for gpu in self.cfg.get("gpus") or []:
                url = str(self.cfg["endpoint"]).format(gpu=gpu)
                observations.append({"gpu": gpu, "latest": fetch_json(url)})
            payload = {"observations": observations}
        return AdapterResult(
            source=self.name,
            role="comparison",
            captured_at=None,
            source_as_of=None,
            payload=payload,
            attribution=self.cfg["attribution"],
            license=self.cfg["license"],
            quality_flags=["COMPARISON_ONLY", "NONCOMMERCIAL"],
        )
