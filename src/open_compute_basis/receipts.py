from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hashing import canonical_json, hash_obj, sha256_hex


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def write_receipt(dir_path: Path, source: str, payload: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    dir_path.mkdir(parents=True, exist_ok=True)
    body = {"source": source, "payload": payload, **(extra or {})}
    digest = hash_obj(body)
    path = dir_path / f"{source}.json"
    path.write_bytes(canonical_json(body))
    return {"path": str(path), "hash": digest, "source": source}


def load_receipts(dir_path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not dir_path.exists():
        return out
    for path in sorted(dir_path.glob("*.json")):
        out[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    return out


def write_json(path: Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json(obj)
    path.write_bytes(data)
    return sha256_hex(data)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
