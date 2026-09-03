from __future__ import annotations

from typing import Any

from ..http import fetch_json
from ..settings import Settings
from .base import AdapterResult

COMPUTE_HINTS = (
    "h100",
    "h200",
    "b200",
    "a100",
    "rtx 5090",
    "rtx5090",
    "gpu",
    "compute",
    "gpu-hour",
    "gpu hour",
)


class KalshiAdapter:
    name = "kalshi"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cfg = settings.sources[self.name]
        self.base = str(self.cfg["endpoint"]).rstrip("/")

    def collect(self, *, fixture: Any | None = None) -> AdapterResult:
        if fixture is not None:
            payload = fixture
        else:
            payload = self._discover()
        markets = payload.get("markets") if isinstance(payload, dict) else None
        if not isinstance(markets, list):
            raise ValueError("kalshi payload missing markets list")
        return AdapterResult(
            source=self.name,
            role="forward",
            captured_at=payload.get("captured_at"),
            source_as_of=payload.get("captured_at"),
            payload=payload,
            attribution=self.cfg["attribution"],
            license=self.cfg["license"],
        )

    def _discover(self) -> dict[str, Any]:
        timeout = float(self.settings.raw["http"]["timeout_seconds"])
        retries = int(self.settings.raw["http"]["retries"])
        headers = {"User-Agent": self.settings.raw["http"]["user_agent"]}
        markets: list[dict[str, Any]] = []
        cursor: str | None = None
        pages = 0
        while pages < 8:
            params: dict[str, Any] = {"status": "open", "limit": 200}
            if cursor:
                params["cursor"] = cursor
            data = fetch_json(
                f"{self.base}/markets",
                timeout=timeout,
                retries=retries,
                headers=headers,
                params=params,
            )
            for market in data.get("markets") or []:
                blob = " ".join(
                    str(market.get(k) or "")
                    for k in ("ticker", "title", "subtitle", "yes_sub_title", "rules_primary")
                ).lower()
                if any(hint in blob for hint in COMPUTE_HINTS):
                    markets.append(market)
            cursor = data.get("cursor")
            pages += 1
            if not cursor:
                break
        return {"captured_at": None, "markets": markets, "discovery": "keyword"}
