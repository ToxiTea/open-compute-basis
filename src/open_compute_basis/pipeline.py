from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .adapters.computable import ComputableAdapter
from .adapters.flop_pending import FlopPendingAdapter
from .adapters.gpucloudcompare import GpuCloudCompareAdapter
from .adapters.internet_backyard_manual import InternetBackyardManualAdapter
from .adapters.kalshi import KalshiAdapter
from .benchmark import build_offers, calculate_all
from .flop_basis import summarize_sessions
from .forward import ladders_from_kalshi
from .hashing import hash_obj
from .inference_eval import CORPUS_VERSION, run_fixture
from .participation import render_participation
from .publish import write_outputs
from .receipts import load_receipts, utc_now, utc_today, write_json, write_receipt
from .settings import Settings, load_settings

ADAPTERS = {
    "gpucloudcompare": GpuCloudCompareAdapter,
    "kalshi": KalshiAdapter,
    "internet_backyard_manual": InternetBackyardManualAdapter,
    "computable": ComputableAdapter,
    "flop_pending": FlopPendingAdapter,
}


def collect(settings: Settings, fixture_dir: Path | None) -> dict[str, Any]:
    fixtures = _load_fixtures(fixture_dir) if fixture_dir else {}
    results = {}
    for name, cls in ADAPTERS.items():
        if not settings.source_enabled(name) and name != "flop_pending":
            continue
        adapter = cls(settings)
        results[name] = adapter.collect(fixture=fixtures.get(name))
    return results


def persist_receipts(run_dir: Path, collected: dict[str, Any]) -> dict[str, str]:
    raw_dir = run_dir / "receipts"
    hashes = {}
    for name, result in collected.items():
        extra = {
            "captured_at": result.captured_at,
            "source_as_of": result.source_as_of,
            "role": result.role,
            "attribution": result.attribution,
            "license": result.license,
            "quality_flags": result.quality_flags,
        }
        rec = write_receipt(raw_dir, name, result.payload, extra)
        hashes[name] = rec["hash"]
    return hashes


def calculate_bundle(settings: Settings, run_dir: Path, *, observation_time: str | None = None) -> dict[str, Any]:
    receipts = load_receipts(run_dir / "receipts")
    now = observation_time or utc_now()
    offers = build_offers(receipts, settings)
    write_json(run_dir / "normalized.json", _jsonable(offers))
    series = calculate_all(offers, now, settings)
    kalshi_payload = (receipts.get("kalshi") or {}).get("payload") or {}
    ib_payload = (receipts.get("internet_backyard_manual") or {}).get("payload") or {}
    flop_payload = (receipts.get("flop_pending") or {}).get("payload") or {}
    attribution = []
    for name, receipt in receipts.items():
        if receipt.get("attribution"):
            attribution.append(receipt["attribution"])
    bundle = {
        "project": settings.project_name,
        "methodology_version": settings.methodology_version,
        "disclaimer": settings.disclaimer,
        "canonical_url": settings.canonical_url,
        "observation_time": now,
        "observation_date": now[:10],
        "series": series,
        "comparisons": {
            "internet_backyard": ib_payload.get("records") or [],
            "computable": (receipts.get("computable") or {}).get("payload"),
        },
        "forward": {"kalshi": ladders_from_kalshi(kalshi_payload)},
        "flop": {
            "FLOP_STATUS": flop_payload.get("FLOP_STATUS") or settings.raw["flop"]["status"],
            "sessions": flop_payload.get("sessions") or [],
        },
        "attribution": attribution,
        "receipt_hashes": {k: hash_obj(v) for k, v in receipts.items()},
    }
    return bundle


def verify_from_receipts(settings: Settings, run_dir: Path, expected: dict[str, Any]) -> None:
    recomputed = calculate_bundle(settings, run_dir, observation_time=expected["observation_time"])
    # print_hash is assigned after first calculate; compare without it
    left = {k: v for k, v in expected.items() if k != "print_hash"}
    if hash_obj(left) != hash_obj(recomputed):
        raise RuntimeError("reproduction hash mismatch; refusing to publish")


def attach_eval(bundle: dict[str, Any], settings: Settings) -> dict[str, Any]:
    fixture_path = settings.root / "tests" / "fixtures" / "inference" / "job.json"
    if fixture_path.exists():
        job = json.loads(fixture_path.read_text(encoding="utf-8"))
        eval_result = run_fixture(job["document"], job["predicted"], job["gold"])
        receipt = {
            "session_id": "sim-ocb-eval-001",
            "corpus_version": CORPUS_VERSION,
            "fee_flop": "1.0",
            "final_state": "completed" if eval_result["passed"] else "failed",
            "validation_passed": eval_result["passed"],
            "challenged": False,
            "simulated": True,
            **eval_result,
        }
        bundle["inference_eval"] = eval_result
        bundle["participation"] = render_participation([receipt], simulated=True)
    else:
        bundle["participation"] = render_participation([], simulated=True)
    return bundle


def run(
    *,
    root: Path | None = None,
    fixture_dir: Path | None = None,
    live: bool = False,
    observation_time: str | None = None,
) -> dict[str, Any]:
    settings = load_settings(root)
    stamp = (observation_time or utc_now()).replace(":", "")
    data_root = Path(os.environ.get("OCB_DATA_DIR") or settings.root)
    run_dir = data_root / "var" / "runs" / stamp
    if fixture_dir is None and not live:
        fixture_dir = settings.root / "tests" / "fixtures"
    collected = collect(settings, fixture_dir)
    persist_receipts(run_dir, collected)
    bundle = calculate_bundle(settings, run_dir, observation_time=observation_time or utc_now())
    verify_from_receipts(settings, run_dir, bundle)
    bundle = attach_eval(bundle, settings)
    bundle["print_hash"] = hash_obj({k: v for k, v in bundle.items() if k != "print_hash"})
    public_dir = data_root / "public" if data_root != settings.root else settings.root / "public"
    hashes = write_outputs(public_dir, data_root / "var" / "history", bundle)
    bundle["latest_hash"] = hashes["latest_hash"]
    bundle["history_hash"] = hashes["history_hash"]
    write_json(run_dir / "bundle.json", bundle)
    return bundle


def _load_fixtures(fixture_dir: Path) -> dict[str, Any]:
    mapping = {
        "gpucloudcompare": fixture_dir / "gpucloudcompare" / "current.json",
        "kalshi": fixture_dir / "kalshi" / "markets.json",
        "computable": fixture_dir / "computable" / "latest.json",
        "flop_pending": fixture_dir / "flop" / "pending.json",
    }
    out: dict[str, Any] = {}
    for name, path in mapping.items():
        if path.exists():
            out[name] = json.loads(path.read_text(encoding="utf-8"))
    return out


def _jsonable(obj: Any) -> Any:
    from decimal import Decimal

    if isinstance(obj, Decimal):
        return format(obj, "f")
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonable(v) for v in obj]
    return obj
