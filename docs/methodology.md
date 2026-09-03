# Methodology v0.1.0

Open Compute Basis (OCB) publishes **narrow, comparable GPU-hour observations**
and, later, FLOP session basis. It does not average every published index into
one number, does not set or peg `$FLOP`, and is not an oracle.

## What is calculated vs what is shown beside it

1. **Constituent feeds** — licensed raw provider offers. These calculate OCB series.
2. **Comparison / control indices** — Internet Backyard, Computable, and similar. Shown beside OCB. Never blended.
3. **Forward-market observations** — Kalshi strike ladders. Not today's physical spot.
4. **FLOP observations** — completed official sessions when they exist. Until then: `FLOP_STATUS=AWAITING_OFFICIAL_SESSION_API`.

v0.1 has one constituent feed (GPU Cloud Price Index). A high-confidence
canonical print therefore cannot exist yet. One-source results are published as
**observations**, not as the benchmark.

## Units and identity

Every offer is normalized to **USD per physical GPU-hour**.

A series is a tuple: GPU SKU, interconnect, pricing type (on-demand / spot /
reserved), service class (managed cloud vs community), geography.

v0.1 series:

- `OCB-H100-SXM-OD-GLOBAL`
- `OCB-H200-SXM-OD-GLOBAL`
- `OCB-B200-OD-GLOBAL`
- `OCB-A100-SXM-OD-GLOBAL`
- `OCB-RTX3090-COMMUNITY-GLOBAL`
- `OCB-RTX4090-COMMUNITY-GLOBAL`
- `OCB-RTX5090-COMMUNITY-GLOBAL`

Community/garage offers are never mixed with managed-cloud offers. Spot is
never mixed with on-demand. RTX 4090 is never mixed with 4090D.

When a managed-cloud source omits interconnect, the offer may enter the named
SXM series only with `VARIANT_UNSPECIFIED`. Explicit NVL or PCIe labels are
excluded from SXM series.

Monthly-only rows are dropped. Hourly price is divided by `gpu_count`.
Unavailable, stale, malformed, or non-positive prices are dropped.

## Aggregation

For each series and observation time:

1. Keep valid normalized offers.
2. Drop extreme outliers more than `8 × IQR` from the sample median (empty IQR ⇒ no drop).
3. Median per provider (a provider with thousands of listings cannot dominate).
4. Cross-provider value = **median of provider medians**.
5. Publish sample 25th and 75th percentiles, provider count, offer count, source count.
6. Grade confidence from coverage, staleness, dispersion, and cross-source agreement.
7. If freshness fails: `NO_PRINT`. Never silently carry yesterday's value.

### Confidence

| Grade | Rule |
|---|---|
| A | ≥3 independent providers, ≥2 constituent feeds, fresh, moderate dispersion |
| B | ≥3 providers, 1 constituent feed, fresh — **observation only** |
| C | 1–2 providers or wide dispersion — observation only |
| D / NO_PRINT | Stale, empty, or schema failure |

High-confidence canonical print requires **three providers and two constituent feeds**.

## Prediction markets

Kalshi binary contracts are discovered, grouped by GPU and expiry, and stored
as raw strike ladders (bid, ask, midpoint, volume, update time).

A **market-implied median strike** is the first strike whose cumulative
midpoint probability is ≥ 0.5 on a monotone ladder. If the ladder is not
monotone, the observation is flagged `NONMONOTONE` and no median is published.

This is not called a forward “price”. Expected-value integration is out of scope
for v0.1.

## FLOP basis (interface only)

Until an official session API exists, status is `AWAITING_OFFICIAL_SESSION_API`.

When official successful, unchallenged sessions exist:

```
flop_per_eflop = fee_flop / (compute_flops / 1e18)
usd_per_eflop  = (fee_flop * usd_per_flop_token) / (compute_flops / 1e18)
basis_pct      = ((flop_usd_per_effective_eflop / external_usd_per_effective_eflop) - 1) * 100
```

USD conversion requires a real USD/`$FLOP` market **and** a named performance
profile. Test tokens never imply a dollar price.

```
external_usd_per_eflop = usd_per_gpu_hour / (effective_pflop_per_second * 3.6)
```

If the profile is unset, publish `$FLOP` per raw exaFLOP beside USD per GPU-hour.

## Reproducibility

Every run writes raw receipts, normalized rows, and a dated print. Publication
requires recomputing the print from stored receipts and matching the SHA-256 of
canonical JSON. Identical receipts must produce byte-identical output.

## Known limitations

- One constituent feed. Canonical high-confidence prints are structurally unavailable.
- GPU Cloud Price Index is managed-cloud list prices. Garage series will usually `NO_PRINT`.
- Interconnect is often unspecified.
- Kalshi coverage depends on which compute contracts are listed that day.
- Internet Backyard is a manual comparison with a documented count mismatch.
- No FLOP session data. Simulated fixtures are labeled `SIMULATED` and do not earn tokens.
