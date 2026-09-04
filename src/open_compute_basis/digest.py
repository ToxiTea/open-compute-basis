from __future__ import annotations

from typing import Any

from .settings import Settings


def build_report(bundle: dict[str, Any], settings: Settings) -> str:
    series = bundle.get("series") or {}
    obs = bundle.get("observation_time") or "unknown"
    flop = (bundle.get("flop") or {}).get("FLOP_STATUS") or settings.raw["flop"]["status"]
    ib = (bundle.get("comparisons") or {}).get("internet_backyard") or []
    kalshi = (bundle.get("forward") or {}).get("kalshi") or []
    eval_ = bundle.get("inference_eval") or {}
    lines = [
        "OCB STATUS",
        f"Updated: {obs}",
        "Not financial advice. Public-safe: no seeds in this file.",
        "",
        "STATUS",
        f"  methodology     {bundle.get('methodology_version')}",
        f"  print hash      {bundle.get('print_hash')}",
        f"  technocore post {settings.technocore_publish}",
        f"  flop participate {settings.flop_participation}",
        f"  flop            {flop}",
        f"  url             {bundle.get('canonical_url') or settings.canonical_url}",
        "",
        "ACTIVITY",
    ]
    for series_id, row in series.items():
        flags = ", ".join(row.get("quality_flags") or []) or "-"
        price = row.get("usd_per_gpu_hour")
        price_s = "-" if price in (None, "") else str(price)
        lines.append(
            f"  {series_id}  {row.get('status')}  {price_s} USD/GPU-h  conf {row.get('confidence')}  {flags}"
        )
    ib_note = "none"
    if ib:
        rec = ib[-1]
        headline = rec.get("headline") or {}
        ib_note = (
            f"{rec.get('gpu')} {headline.get('usd_per_gpu_hour')}/GPU-h "
            f"as of {rec.get('source_as_of_date')}  {','.join(rec.get('quality_flags') or [])}"
        )
    lines += [
        f"  internet backyard  {ib_note}",
        f"  kalshi ladders     {len(kalshi)}",
        f"  simulated eval     passed={eval_.get('passed')} score={eval_.get('score')} (not tokens)",
        "",
        "STAY PARKED",
        "  Do not post to public Technocore until launch gates pass.",
        "  Do not set FLOP_PARTICIPATION until official FLOP Labs software is pinned.",
        "  Do not buy a purported pre-launch token or paste seeds anywhere.",
        "  Do not scrape Internet Backyard. Garage series stay NO_PRINT until a licensed feed exists.",
        "",
        "TODOS",
    ]
    for item in _todos(bundle, settings, ib, series):
        box = "[x]" if item["done"] else "[ ]"
        lines.append(f"  {box} {item['text']}")
    lines.append("")
    return "\n".join(lines)


def _todos(
    bundle: dict[str, Any],
    settings: Settings,
    ib: list[dict[str, Any]],
    series: dict[str, Any],
) -> list[dict[str, Any]]:
    url = str(bundle.get("canonical_url") or settings.canonical_url)
    pages_on = "github.io" in url
    one_source = any("ONE_SOURCE" in (row.get("quality_flags") or []) for row in series.values())
    return [
        {
            "done": pages_on,
            "text": "GitHub Pages is live at https://toxitea.github.io/open-compute-basis/",
        },
        {
            "done": False,
            "text": "Confirm owner and recovery seeds are in a password manager.",
        },
        {
            "done": not one_source,
            "text": "Watch for a second licensed constituent feed before calling any print canonical.",
        },
        {
            "done": False,
            "text": "Optional: ocb run --live and skim H100 flags.",
        },
        {
            "done": bool(ib),
            "text": "Optional: newer Internet Backyard manual check when you next visit the site.",
        },
    ]
