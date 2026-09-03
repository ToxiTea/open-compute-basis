from __future__ import annotations

from typing import Any

from ..settings import Settings
from .base import AdapterResult


class FlopPendingAdapter:
    name = "flop_pending"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cfg = settings.sources[self.name]

    def collect(self, *, fixture: Any | None = None) -> AdapterResult:
        return AdapterResult(
            source=self.name,
            role="flop",
            captured_at=None,
            source_as_of=None,
            payload={
                "FLOP_STATUS": "AWAITING_OFFICIAL_SESSION_API",
                "sessions": [],
                "fixture": fixture,
            },
            attribution=self.cfg["attribution"],
            license=self.cfg["license"],
            quality_flags=["AWAITING_OFFICIAL_SESSION_API"],
        )
