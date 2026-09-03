# Source audit — Open Compute Basis v0.1

Recorded 2026-09-02. A source is implemented only when permitted use is clear.
Internet Backyard is human-viewable and disabled for automated ingestion.

## Implemented in v0.1

### GPU Cloud Price Index (`gpucloudcompare`)

| Field | Value |
|---|---|
| Role | Constituent (Tier B) |
| Endpoint | `https://gpucloudcompare.com/data/current.json` (CSV and `history-daily.json` also published) |
| Fields | `provider`, `plan_id`, `gpu_model`, `gpu_count`, `price_hourly_usd`, `price_monthly_usd`, `locations`, `captured_at`, plus host sizing |
| Update frequency | Daily public snapshot |
| Authentication | None |
| Rate limits | Unstated; OCB uses a 2 req/s client cap and 20s timeout |
| License / terms | CC BY 4.0 |
| Attribution | `Source: GPU Cloud Price Index — gpucloudcompare.com (CC-BY 4.0)` |
| Commercial use | Permitted with attribution |
| Automated republication | Permitted with attribution |
| Notes | Public **list** prices, not negotiated or transaction prints. Hourly and monthly fields are never mixed by the publisher. OCB uses hourly USD only and divides by `gpu_count`. Spot-looking plan IDs are excluded from on-demand series. |

### Kalshi public Trade API (`kalshi`)

| Field | Value |
|---|---|
| Role | Forward-market observation (Tier A market data) |
| Endpoint | `https://external-api.kalshi.com/trade-api/v2` — series, markets, orderbooks |
| Fields | ticker, event, status, yes/no bid/ask, volume, expiry, orderbook levels |
| Update frequency | Live |
| Authentication | None for market data. Trading endpoints require keys and are **not used**. |
| Rate limits | Unstated on the public quick-start; OCB respects 429 bodies and the client cap |
| License / terms | Kalshi public API / exchange terms. Read-only market data only. |
| Attribution | Kalshi public Trade API |
| Commercial use | Review Kalshi terms before any commercial productization |
| Automated republication | OCB stores raw ladders and publishes derived observations, not a full order-book dump |
| Notes | Markets are discovered by keyword, not hardcoded event IDs. OCB never places an order. |

### Computable GPU Index (`computable`)

| Field | Value |
|---|---|
| Role | Comparison / control index (not a constituent) |
| Endpoint | `https://api.getcomputable.com/v1/index/{H100\|H200\|B200\|B300}/latest` |
| Fields | Index value, observation time, unit, stability band; receipts via `?include=receipts` |
| Update frequency | Scheduled observations |
| Authentication | None |
| Rate limits | Unstated; same client cap |
| License / terms | Published values: **CC BY-NC 4.0**. Code is Apache-2.0. |
| Attribution | Computable GPU Index (CC BY-NC 4.0) |
| Commercial use | **Not permitted** without permission |
| Automated republication | Disabled by default. Gated on `ENABLE_NONCOMMERCIAL_SOURCE=true`. Outputs stay labeled comparison-only and noncommercial. |
| Notes | Useful cross-check for H100/H200/B200. Never blended into OCB. |

### Internet Backyard Compute Market Index (`internet_backyard_manual`)

| Field | Value |
|---|---|
| Role | Tier D manual comparison |
| Endpoint | `https://www.internetbackyard.com/compute-index` (webpage only) |
| Fields | Headline GPU-hour, provider medians and middle-50%, listing counts |
| Update frequency | Human capture |
| Authentication | None for viewing |
| Rate limits | n/a — **no scraper** |
| License / terms | No documented public API or data-reuse license visible on 2026-09-02 |
| Attribution | Internet Backyard comparison — manually captured |
| Commercial use | Unknown |
| Automated republication | **Forbidden** until a documented API, license, or written permission exists |
| Notes | First record is the 2026-09-01 RTX 4090 PCIe screenshot. Headline listings 68 vs displayed-count subtotal 79 is preserved as `COUNT_MISMATCH`. Never a constituent. |

### FLOP official session data (`flop_pending` / `flop_testnet`)

| Field | Value |
|---|---|
| Role | FLOP network observations |
| Endpoint | None public as of 2026-09-02 |
| Fields | Draft session: model hash, max latency, FLOPs, confidentiality, fee in `$FLOP` |
| Update frequency | n/a |
| Authentication | n/a |
| License / terms | Official draft at https://flop.finance/teaser/ (provisional) |
| Attribution | FLOP draft / future official receipts |
| Commercial use | n/a |
| Automated republication | n/a |
| Notes | Public GitHub org has Technocore Chat and `tclk` only. Adapter is a typed stub. Fixtures are labeled `SIMULATED`. `FLOP_PARTICIPATION=false`. No wallet, faucet, or token address is configured. |

## Optional / disabled until a later audit

| Source | Why disabled |
|---|---|
| OpenComputePrices | Upstream data rights and source terms not verified for republication |
| Ornn OCPI | Free viewing is not treated as a republication license |
| Injective/Helix H100 perp | Derivative/oracle observation; terms review required; not physical delivery |
| Silicon Data | Paid full history/API |
| CME compute futures | Scheduled 2026-10-05, pending regulatory review; not live |
| ICE/Ornn GPU futures | Announced, not verified live |

## Attribution block (emit with every public print)

```
Source: GPU Cloud Price Index — gpucloudcompare.com (CC-BY 4.0)
Forward observations: Kalshi public Trade API
Internet Backyard comparison — manually captured; not an OCB constituent
Computable GPU Index appears only when ENABLE_NONCOMMERCIAL_SOURCE=true (CC BY-NC 4.0)
Open Compute Basis calculations: Apache-2.0 code; OCB-created datasets CC BY 4.0 only where every upstream right permits it
```
