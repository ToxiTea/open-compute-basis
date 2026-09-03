from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    return data


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    root: Path
    methodology_version: str
    project_name: str
    canonical_url: str
    disclaimer: str
    raw: dict[str, Any] = field(repr=False)
    sources: dict[str, Any] = field(repr=False)
    series: dict[str, Any] = field(repr=False)
    performance_profiles: dict[str, Any] = field(repr=False)

    @property
    def technocore_publish(self) -> bool:
        return _truthy(os.environ.get("TECHNOCORE_PUBLISH")) or bool(
            self.raw.get("technocore", {}).get("publish")
        )

    @property
    def flop_participation(self) -> bool:
        return _truthy(os.environ.get("FLOP_PARTICIPATION")) or bool(
            self.raw.get("flop", {}).get("participation")
        )

    @property
    def enable_noncommercial_source(self) -> bool:
        return _truthy(os.environ.get("ENABLE_NONCOMMERCIAL_SOURCE")) or bool(
            self.raw.get("flags", {}).get("enable_noncommercial_source")
        )

    @property
    def agent_seed_env(self) -> str:
        return str(self.raw.get("technocore", {}).get("agent_seed_env") or "TECHNOCORE_AGENT_SEED")

    def source_enabled(self, name: str) -> bool:
        cfg = self.sources.get(name) or {}
        if not cfg.get("enabled"):
            if cfg.get("requires_flag") == "ENABLE_NONCOMMERCIAL_SOURCE" and self.enable_noncommercial_source:
                return True
            return False
        if cfg.get("requires_flag") == "ENABLE_NONCOMMERCIAL_SOURCE" and not self.enable_noncommercial_source:
            return False
        return True


def load_settings(root: Path | None = None) -> Settings:
    root = root or ROOT
    raw = _load_yaml(root / "config" / "settings.yaml")
    return Settings(
        root=root,
        methodology_version=str(raw["methodology_version"]),
        project_name=str(raw["project_name"]),
        canonical_url=str(raw["canonical_url"]),
        disclaimer=str(raw["disclaimer"]),
        raw=raw,
        sources=_load_yaml(root / "config" / "sources.yaml"),
        series=_load_yaml(root / "config" / "series.yaml"),
        performance_profiles=_load_yaml(root / "config" / "performance_profiles.yaml"),
    )
