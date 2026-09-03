from __future__ import annotations

import hashlib
from typing import Any

CORPUS_VERSION = "ocb-eval-v0.1"
PROMPT = (
    "Extract GPU SKU, region, service class, commitment, availability, "
    "and USD per GPU-hour from the document. Return the strict schema only."
)
PROMPT_HASH = hashlib.sha256(PROMPT.encode()).hexdigest()

SCHEMA_KEYS = {
    "gpu_sku": str,
    "region": str,
    "service_class": str,
    "commitment": str,
    "availability": str,
    "usd_per_gpu_hour": (int, float),
}


def prompt_hash() -> str:
    return PROMPT_HASH


def validate_extraction(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise ValueError("extraction must be an object")
    extra = set(obj) - set(SCHEMA_KEYS)
    if extra:
        raise ValueError(f"unexpected keys: {sorted(extra)}")
    missing = set(SCHEMA_KEYS) - set(obj)
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")
    for key, typ in SCHEMA_KEYS.items():
        if not isinstance(obj[key], typ):
            raise ValueError(f"{key} has wrong type")
    if isinstance(obj["usd_per_gpu_hour"], bool) or obj["usd_per_gpu_hour"] <= 0:
        raise ValueError("usd_per_gpu_hour must be a positive number")
    return dict(obj)


def score(predicted: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    pred = validate_extraction(predicted)
    gold_v = validate_extraction(gold)
    fields = {}
    hits = 0
    for key in SCHEMA_KEYS:
        if key == "usd_per_gpu_hour":
            ok = abs(float(pred[key]) - float(gold_v[key])) <= 0.01
        else:
            ok = str(pred[key]).strip().lower() == str(gold_v[key]).strip().lower()
        fields[key] = ok
        hits += int(ok)
    return {
        "corpus_version": CORPUS_VERSION,
        "prompt_hash": PROMPT_HASH,
        "score": hits / len(SCHEMA_KEYS),
        "fields": fields,
        "passed": hits == len(SCHEMA_KEYS),
    }


def run_fixture(document: str, predicted: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    input_hash = hashlib.sha256(document.encode()).hexdigest()
    result = score(predicted, gold)
    result.update(
        {
            "input_hash": input_hash,
            "quarantined": not result["passed"],
            "canonical_print_touched": False,
        }
    )
    return result
