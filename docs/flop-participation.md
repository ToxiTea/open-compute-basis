# FLOP participation — confirmed, secondary, unknown

This document is not a claim of eligibility. Figures come from the official
FLOP draft teaser (updated 2026-08-26, explicitly provisional) unless marked
secondary.

## Confirmed in the official draft (may change)

- Q4 2026 testnet, roughly 90 days; mainnet targeted Q1 2027.
- Genesis airdrop 3.5 billion `$FLOP`, subject to a still-provisional Yellow Paper.
- Up to 1.2 billion `$FLOP` for **agents** based largely on testnet inference spend, plus unspecified prizes.
- Agent allocation arrives locked; spendable on inference or staking. Draft unlock: every 3 `$FLOP` spent on inference unlocks 1 airdropped `$FLOP`.
- Up to 1.2 billion `$FLOP` for **miners** for verified compute delivered.
- Recommended miner hardware: GPU with at least 16 GB VRAM (provisional).
- Session request fields in the draft: model-weight hash, max latency, compute in FLOPs, confidentiality flag, fee in `$FLOP`.
- No public session API, faucet, chain ID, or official token address as of 2026-09-02.

## Secondary (not protocol authority)

Tat Thang's 2026-09-01 AMA recap: keep one real agent identity; do not farm
identities or fake activity; wait for the official Q4 testnet; no live `$FLOP`
token and no official Discord. Useful as culture, not as a scoring rule.

Technocore room-count snapshots are operational, not eligibility rules.

## Unknown

- Exact faucet procedure, DID/address linkage, claim rules, prizes.
- Whether Technocore posts, Git commits, or room age affect any allocation.
- Mainnet claim and remaining unlock mechanics.

## OCB rules

- **One persistent public OCB agent DID.** Owner, recovery, staging, and replacement keys never claim a faucet or submit inference.
- Useful workload only: the versioned evaluation corpus (`ocb-eval-v0.1`).
- Hard per-session and daily test-token caps, max jobs, max retries, emergency stop.
- Count only completed, independently scored, non-duplicate sessions.
- Reject empty prompts, spend loops, fabricated demand, and undisclosed self-dealing.
- Receipts live in the repository archive, not Technocore.
- `FLOP_PARTICIPATION=false` until official software is reviewed and pinned.
- Expected token value never enters job selection or the benchmark.

## Workload

Corpus `ocb-eval-v0.1` extracts GPU SKU, region, service class, commitment,
availability, and USD/GPU-hour from licensed source excerpts into a strict
schema, then scores against gold labels. Model output is quarantined until
validators accept it. It never writes a canonical OCB print.
