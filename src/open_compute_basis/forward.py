from __future__ import annotations

from decimal import Decimal
from typing import Any

from .hashing import quantize_money

GPU_ALIASES = (
    ("H100", ("h100",)),
    ("H200", ("h200",)),
    ("B200", ("b200",)),
    ("A100", ("a100",)),
    ("RTX5090", ("5090", "rtx 5090", "rtx5090")),
)


def _mid(bid: Any, ask: Any) -> Decimal | None:
    try:
        b = Decimal(str(bid)) if bid not in (None, "") else None
        a = Decimal(str(ask)) if ask not in (None, "") else None
    except ArithmeticError:
        return None
    if b is None and a is None:
        return None
    if b is None:
        return quantize_money(a)
    if a is None:
        return quantize_money(b)
    return quantize_money((b + a) / 2)


def _strike(market: dict[str, Any]) -> Decimal | None:
    for key in ("floor_strike", "cap_strike", "strike", "yes_sub_title", "subtitle"):
        raw = market.get(key)
        if raw is None:
            continue
        text = str(raw).replace("$", "").replace(",", "").strip()
        try:
            return quantize_money(text.split()[0])
        except (ArithmeticError, IndexError, ValueError):
            continue
    return None


def _gpu(market: dict[str, Any]) -> str | None:
    blob = " ".join(
        str(market.get(k) or "")
        for k in ("ticker", "title", "subtitle", "yes_sub_title", "rules_primary", "event_ticker")
    ).lower()
    for name, aliases in GPU_ALIASES:
        if any(a in blob for a in aliases):
            return name
    return None


def ladders_from_kalshi(payload: dict[str, Any]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for market in payload.get("markets") or []:
        gpu = _gpu(market)
        strike = _strike(market)
        if gpu is None or strike is None:
            continue
        expiry = str(market.get("close_time") or market.get("latest_expiration_time") or "unknown")
        mid = _mid(market.get("yes_bid_dollars"), market.get("yes_ask_dollars"))
        row = {
            "ticker": market.get("ticker"),
            "strike": strike,
            "bid": market.get("yes_bid_dollars"),
            "ask": market.get("yes_ask_dollars"),
            "midpoint": mid,
            "volume": market.get("volume_fp") or market.get("volume"),
            "updated_time": market.get("updated_time"),
            "status": market.get("status"),
        }
        groups.setdefault((gpu, expiry), []).append(row)
    out = []
    for (gpu, expiry), rows in sorted(groups.items()):
        rows = sorted(rows, key=lambda r: r["strike"])
        mids = [r["midpoint"] for r in rows if r["midpoint"] is not None]
        monotone = all(mids[i] >= mids[i + 1] for i in range(len(mids) - 1)) if len(mids) >= 2 else True
        implied = None
        flags = []
        if not monotone:
            flags.append("NONMONOTONE")
        elif mids:
            # For "price above strike" contracts, P(price > K) should fall as K rises.
            # Median strike is the first K whose midpoint (P above) drops to <= 0.5.
            implied = rows[0]["strike"]
            for row in rows:
                if row["midpoint"] is not None and row["midpoint"] <= Decimal("0.5"):
                    implied = row["strike"]
                    break
            else:
                implied = rows[-1]["strike"]
                flags.append("MEDIAN_AT_TAIL")
        out.append(
            {
                "gpu": gpu,
                "expiry": expiry,
                "ladder": rows,
                "implied_median_strike": implied if monotone else None,
                "quality_flags": flags,
                "not_a_forward_price": True,
            }
        )
    return out
