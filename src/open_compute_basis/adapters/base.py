from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class AdapterResult:
    source: str
    role: str
    captured_at: str | None
    source_as_of: str | None
    payload: Any
    attribution: str
    license: str
    quality_flags: list[str] = field(default_factory=list)
    error: str | None = None


class Adapter(Protocol):
    name: str

    def collect(self, *, fixture: Any | None = None) -> AdapterResult: ...
