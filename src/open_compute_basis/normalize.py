from __future__ import annotations

from decimal import Decimal
from typing import Any

from .hashing import quantize_money

SPOT_MARKERS = ("spot", "preempt", "interrupt")


def normalize_offers(source: str, payload: dict[str, Any], captured_at: str | None) -> list[dict[str, Any]]:
    if source == "gpucloudcompare":
        return _from_gpucloudcompare(payload, captured_at)
    return []


def _from_gpucloudcompare(payload: dict[str, Any], captured_at: str | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for plan in payload.get("plans") or []:
        hourly = plan.get("price_hourly_usd")
        gpu_count = plan.get("gpu_count") or 1
        model = str(plan.get("gpu_model") or "")
        plan_id = str(plan.get("plan_id") or "")
        if hourly is None:
            continue
        try:
            hourly_d = Decimal(str(hourly))
            count = int(gpu_count)
        except (ArithmeticError, ValueError, TypeError):
            continue
        if hourly_d <= 0 or count <= 0:
            continue
        per_gpu = quantize_money(hourly_d / count)
        pricing = "SPOT" if any(m in plan_id.lower() for m in SPOT_MARKERS) else "ON_DEMAND"
        flags: list[str] = []
        variant = _variant(model)
        if variant == "UNKNOWN":
            flags.append("VARIANT_UNSPECIFIED")
        out.append(
            {
                "source": "gpucloudcompare",
                "tier": "B",
                "provider": str(plan.get("provider") or "unknown"),
                "offer_id": plan_id,
                "gpu_model": model,
                "gpu_family": _family(model),
                "variant": variant,
                "gpu_count": count,
                "usd_per_gpu_hour": per_gpu,
                "pricing_type": pricing,
                "service_class": "MANAGED_CLOUD",
                "locations": list(plan.get("locations") or []),
                "available": hourly is not None,
                "captured_at": captured_at or plan.get("captured_at"),
                "quality_flags": flags,
            }
        )
    return out


def _family(model: str) -> str:
    u = model.upper().replace(" ", "")
    if "RTX4090" in u or "4090" in u:
        return "RTX4090"
    if "RTX3090" in u or "3090" in u:
        return "RTX3090"
    if "RTX5090" in u or "5090" in u:
        return "RTX5090"
    if "H200" in u:
        return "H200"
    if "H100" in u:
        return "H100"
    if "B200" in u:
        return "B200"
    if "A100" in u:
        return "A100"
    return "OTHER"


def _variant(model: str) -> str:
    u = model.upper()
    if "NVL" in u:
        return "NVL"
    if "PCIE" in u or "PCI-E" in u:
        return "PCIE"
    if "SXM" in u or "HBM3" in u or "HBM" in u:
        return "SXM"
    return "UNKNOWN"


def assign_series(offer: dict[str, Any], series_cfg: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    model = str(offer.get("gpu_model") or "")
    for series_id, cfg in series_cfg.items():
        if offer.get("pricing_type") != cfg.get("pricing_type"):
            continue
        if offer.get("service_class") != cfg.get("service_class"):
            continue
        if any(ex.lower() in model.lower() for ex in cfg.get("exclude_model_substrings") or []):
            # exclusion is only applied when the substring is not the series' own gpu token
            # e.g. H100 series excluding H200. "H100" in "H100" should not self-exclude.
            if _serious_exclude(model, cfg):
                continue
        if not any(inc.lower() in model.lower() for inc in cfg.get("include_model_substrings") or []):
            continue
        interconnect = cfg.get("interconnect")
        variant = offer.get("variant")
        if interconnect not in {None, "ANY"}:
            if variant == interconnect:
                hits.append(series_id)
            elif variant == "UNKNOWN" and cfg.get("include_unspecified_family"):
                offer.setdefault("quality_flags", [])
                flag = cfg.get("unspecified_flag")
                if flag and flag not in offer["quality_flags"]:
                    offer["quality_flags"].append(flag)
                hits.append(series_id)
        else:
            hits.append(series_id)
    return hits


def _serious_exclude(model: str, cfg: dict[str, Any]) -> bool:
    model_l = model.lower()
    gpu = str(cfg.get("gpu") or "").lower()
    for ex in cfg.get("exclude_model_substrings") or []:
        ex_l = ex.lower()
        if ex_l.replace(" ", "") in gpu.replace(" ", ""):
            continue
        if gpu and gpu in ex_l.replace(" ", ""):
            continue
        if ex_l in model_l:
            return True
    return False
