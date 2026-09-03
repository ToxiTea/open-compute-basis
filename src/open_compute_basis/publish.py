from __future__ import annotations

import html
from decimal import Decimal
from pathlib import Path
from typing import Any

from .receipts import write_json


def money(value: Any) -> str:
    if value in (None, ""):
        return "—"
    if isinstance(value, Decimal):
        return f"${format(value, 'f')}/GPU-h"
    try:
        return f"${format(Decimal(str(value)), 'f')}/GPU-h"
    except Exception:
        return str(value)


def render_latest(bundle: dict[str, Any]) -> dict[str, Any]:
    return bundle


def write_outputs(public_dir: Path, history_dir: Path, bundle: dict[str, Any]) -> dict[str, str]:
    latest = public_dir / "latest.json"
    dated = history_dir / f"{bundle['observation_date']}.json"
    latest_hash = write_json(latest, bundle)
    history_hash = write_json(dated, bundle)
    (public_dir / "index.html").write_text(render_html(bundle), encoding="utf-8")
    return {"latest_hash": latest_hash, "history_hash": history_hash}


def render_html(bundle: dict[str, Any]) -> str:
    series_rows = []
    for series_id, row in (bundle.get("series") or {}).items():
        iqr = row.get("iqr") or [None, None]
        series_rows.append(
            "<tr>"
            f"<td>{html.escape(series_id)}</td>"
            f"<td>{html.escape(str(row.get('status')))}</td>"
            f"<td>{html.escape(money(row.get('usd_per_gpu_hour')))}</td>"
            f"<td>{html.escape(money(iqr[0]))} – {html.escape(money(iqr[1]))}</td>"
            f"<td>{row.get('provider_count')}</td>"
            f"<td>{row.get('offer_count')}</td>"
            f"<td>{row.get('source_count')}</td>"
            f"<td>{html.escape(str(row.get('confidence')))}</td>"
            f"<td>{html.escape(', '.join(row.get('quality_flags') or []))}</td>"
            "</tr>"
        )
    ib_rows = []
    for rec in bundle.get("comparisons", {}).get("internet_backyard") or []:
        headline = rec.get("headline") or {}
        flags = ", ".join(rec.get("quality_flags") or [])
        ib_rows.append(
            f"<li><strong>Internet Backyard comparison — manually captured</strong> "
            f"{html.escape(str(rec.get('gpu')))} {html.escape(str(rec.get('form_factor')))} "
            f"{html.escape(money(headline.get('usd_per_gpu_hour')))} "
            f"on {html.escape(str(rec.get('source_as_of_date')))}; "
            f"headline listings {html.escape(str(headline.get('listing_count')))}; "
            f"displayed-count total {html.escape(str(rec.get('provider_displayed_count_total')))}; "
            f"flags: {html.escape(flags)}</li>"
        )
    ladders = []
    for item in bundle.get("forward", {}).get("kalshi") or []:
        ladders.append(
            f"<li>{html.escape(item.get('gpu') or '')} expiry {html.escape(str(item.get('expiry')))} "
            f"implied median strike {html.escape(money(item.get('implied_median_strike')))} "
            f"{html.escape(', '.join(item.get('quality_flags') or []))} "
            "(not a documented forward price)</li>"
        )
    attrs = "".join(f"<li>{html.escape(a)}</li>" for a in bundle.get("attribution") or [])
    flop = bundle.get("flop") or {}
    part = bundle.get("participation") or {}
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Open Compute Basis — Compute Basis Board</title>
  <style>
    body {{ font-family: Georgia, serif; margin: 2rem auto; max-width: 1100px; color: #111; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.95rem; }}
    th, td {{ border-bottom: 1px solid #ccc; padding: 0.4rem 0.5rem; text-align: left; }}
    .panel {{ border: 1px solid #bbb; padding: 1rem 1.2rem; margin: 1.2rem 0; }}
    .muted {{ color: #555; }}
    code {{ font-size: 0.9rem; }}
  </style>
</head>
<body>
  <h1>Open Compute Basis</h1>
  <p>What does comparable GPU compute cost in dollars, and how would a FLOP session compare?
  This board keeps those markets <em>separate</em>. It is not an oracle, peg, or official FLOP product.
  Methodology {html.escape(str(bundle.get('methodology_version')))}.</p>
  <p class="muted">Observation {html.escape(str(bundle.get('observation_time')))} ·
  print hash <code>{html.escape(str(bundle.get('print_hash') or ''))}</code> ·
  <a href="https://github.com/ToxiTea/open-compute-basis">repository</a></p>
  <p>Read top to bottom: public list prices, a manual outside comparison, prediction-market ladders,
  then FLOP (empty until an official session API exists).
  <code>OBSERVATION</code> means one licensed feed — useful, not a canonical index.
  <code>NO_PRINT</code> means coverage failed; we do not invent or carry a stale number.
  Garage RTX series stay blank until a licensed community feed exists. Internet Backyard is shown beside OCB, never inside it.</p>

  <div class="panel">
    <h2>Spot / list observations</h2>
    <p>Public asking prices in USD per physical GPU-hour. Value is the median of per-provider medians so one listing mill cannot dominate. IQR is the 25th–75th percentile of those provider medians.</p>
    <table>
      <thead><tr>
        <th>Series</th><th>Status</th><th>Median of provider medians</th>
        <th>IQR</th><th>Providers</th><th>Offers</th><th>Sources</th><th>Conf.</th><th>Flags</th>
      </tr></thead>
      <tbody>{''.join(series_rows)}</tbody>
    </table>
  </div>

  <div class="panel">
    <h2>Internet Backyard comparison — manually captured</h2>
    <p>Human-captured print from internetbackyard.com/compute-index. Comparison only. We do not scrape the site. The 68 vs 79 listing-count mismatch is preserved on purpose.</p>
    <ul>{''.join(ib_rows) or '<li>No manual records.</li>'}</ul>
  </div>

  <div class="panel">
    <h2>Forward-market observations (Kalshi)</h2>
    <p>Binary compute contracts discovered on Kalshi’s public API. The implied median strike is the first strike whose midpoint probability falls to 50%. That is a ladder summary, not a forward curve we would trade or call a price.</p>
    <ul>{''.join(ladders) or '<li>No discovered compute markets in this run.</li>'}</ul>
  </div>

  <div class="panel">
    <h2>FLOP session basis — awaiting official software/API</h2>
    <p>Status: <code>{html.escape(str(flop.get('FLOP_STATUS') or 'AWAITING_OFFICIAL_SESSION_API'))}</code>.
    No session prices are invented from Technocore chat. Transaction-index panel: none (no licensed clearing feed enabled).</p>
  </div>

  <div class="panel">
    <h2>Simulated inference-evaluation report</h2>
    <p>The fixed job OCB will run on an official testnet: extract GPU fields from a licensed excerpt and score against gold labels. Labeled SIMULATED. It does not earn tokens and does not write the table above.</p>
    <pre>{html.escape(_pretty(part))}</pre>
  </div>

  <div class="panel">
    <h2>Attribution</h2>
    <ul>{attrs}</ul>
    <p><a href="latest.json">latest.json</a></p>
  </div>
</body>
</html>
"""


def _pretty(obj: Any) -> str:
    import json

    return json.dumps(obj, indent=2, sort_keys=True, default=str)
