from __future__ import annotations

from typing import Any

from ..settings import Settings
from .base import AdapterResult


class FlopTestnetAdapter:
    """Disabled until official FLOP software, faucet, schema, and chain ID are pinned."""

    name = "flop_testnet"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cfg = settings.sources[self.name]

    def collect(self, *, fixture: Any | None = None) -> AdapterResult:
        if self.settings.flop_participation:
            raise RuntimeError(
                "FLOP_PARTICIPATION is true but no official pinned config exists; fail closed"
            )
        return AdapterResult(
            source=self.name,
            role="flop",
            captured_at=None,
            source_as_of=None,
            payload={"enabled": False, "reason": "official testnet not configured"},
            attribution=self.cfg["attribution"],
            license=self.cfg["license"],
            quality_flags=["DISABLED"],
            error="disabled",
        )
