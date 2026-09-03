from __future__ import annotations

from typing import Any

from ..settings import Settings
from .base import AdapterResult


class InjectiveAdapter:
    name = "injective"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cfg = settings.sources[self.name]

    def collect(self, *, fixture: Any | None = None) -> AdapterResult:
        return AdapterResult(
            source=self.name,
            role="forward",
            captured_at=None,
            source_as_of=None,
            payload={"disabled": True, "reason": "terms review required"},
            attribution=self.cfg["attribution"],
            license=self.cfg["license"],
            quality_flags=["DISABLED"],
            error="disabled",
        )
