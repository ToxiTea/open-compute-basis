from __future__ import annotations

from decimal import Decimal
from typing import Any

from .hashing import quantize_money

EXAFLOP = Decimal("1e18")


def flop_per_eflop(fee_flop: Decimal, compute_flops: Decimal) -> Decimal:
    if compute_flops <= 0:
        raise ValueError("compute_flops must be positive")
    return quantize_money(fee_flop / (compute_flops / EXAFLOP))


def usd_per_eflop(fee_flop: Decimal, usd_per_flop_token: Decimal, compute_flops: Decimal) -> Decimal:
    if usd_per_flop_token <= 0:
        raise ValueError("usd_per_flop_token must be a real positive market price")
    return quantize_money((fee_flop * usd_per_flop_token) / (compute_flops / EXAFLOP))


def external_usd_per_eflop(usd_per_gpu_hour: Decimal, effective_pflop_per_second: Decimal) -> Decimal:
    if effective_pflop_per_second <= 0:
        raise ValueError("performance profile is unset")
    return quantize_money(usd_per_gpu_hour / (effective_pflop_per_second * Decimal("3.6")))


def basis_pct(flop_usd: Decimal, external_usd: Decimal) -> Decimal:
    if external_usd <= 0:
        raise ValueError("external usd per eflop must be positive")
    return quantize_money(((flop_usd / external_usd) - 1) * 100)


def summarize_sessions(
    sessions: list[dict[str, Any]],
    *,
    usd_per_flop_token: Decimal | None,
    profile: dict[str, Any] | None,
    simulated: bool,
) -> dict[str, Any]:
    rows = []
    for session in sessions:
        if session.get("state") not in {"completed", "successful"}:
            continue
        if session.get("challenged"):
            continue
        fee = Decimal(str(session["fee_flop"]))
        flops = Decimal(str(session["compute_flops"]))
        row = {
            "session_id": session.get("session_id"),
            "flop_per_eflop": flop_per_eflop(fee, flops),
            "usd_per_eflop": None,
            "basis_pct": None,
        }
        if usd_per_flop_token is not None and profile and Decimal(str(profile.get("effective_pflop_per_second") or 0)) > 0:
            row["usd_per_eflop"] = usd_per_eflop(fee, usd_per_flop_token, flops)
        rows.append(row)
    flags = ["SIMULATED"] if simulated else []
    return {
        "FLOP_STATUS": "SIMULATED" if simulated else "LIVE",
        "sessions": rows,
        "quality_flags": flags,
        "usd_token_price_used": usd_per_flop_token is not None,
    }
