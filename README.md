# Open Compute Basis

Independent, reproducible GPU compute-basis observations. Not an oracle, not a peg, not financial advice, and not an official FLOP Labs product.

Canonical repository: https://github.com/ToxiTea/open-compute-basis

**TL;DR**

1. Collect licensed public GPU list prices and Kalshi compute market ladders.
2. Publish narrow USD/GPU-hour observations (never one universal “GPU price”).
3. Show Internet Backyard and other indices as comparisons, not constituents.
4. Keep FLOP session basis and testnet participation disabled until official software exists.
5. Fail closed on stale data; never trade; never scrape Internet Backyard.

## One-command local run

```powershell
cd C:\Users\brend\open-compute-basis
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
ocb run --fixtures --observation-time 2026-09-02T12:00:00Z
```

Then open `public/index.html` and `public/latest.json`. Tests: `pytest`.

If Windows blocks creating `.venv` or `var\` under Documents (OneDrive / Controlled Folder Access), keep the project here under your user profile, or set `OCB_DATA_DIR` to a writable folder.

## Credentials — what you need (and do not need)

**v0.1 collect / calculate / dashboard: none.**

| Item | Needed now? | Notes |
|---|---|---|
| GPU Cloud Price Index | No | Public JSON, CC BY 4.0, no key |
| Kalshi market data | No | Unauthenticated Trade API. Never create a Kalshi trading key |
| Computable GPU Index | No | Public, but CC BY-NC 4.0. Leave `ENABLE_NONCOMMERCIAL_SOURCE=false` unless you confirm noncommercial use |
| Internet Backyard | No login | Manual JSON only. Do not scrape. No API key exists |
| Wallet / exchange / `$FLOP` | **No** | Disabled until official FLOP testnet software is published |
| LLM API key | **No** | Pricing path is deterministic |
| Hostinger / Slack / Vercel | No | Not used |
| GitHub account | Optional | Only if you want Actions + Pages later |

**Later, only for a public Technocore launch (Gates 2–5), create these on a trusted local machine — never in this chat:**

1. **Owner seed** — 64 hex chars. Offline / password manager. Claims the room. Never GitHub Actions.
2. **OCB agent seed** — 64 hex chars. The one public agent identity. Store only as GitHub Actions secret `TECHNOCORE_AGENT_SEED`.
3. **Recovery seed** — 64 hex chars. Offline, unused until a suspected owner-key incident.

Create them with `ocb technocore identity create --role owner|agent|recovery`. The seed prints once. Do not paste seeds into issues, PRs, rooms, or AI chats. The public `did:key:z6Mk…` is safe to publish.

Owner and recovery DIDs must never claim a faucet or run inference.

## Flags (not secrets)

```
TECHNOCORE_PUBLISH=false          # keep off until the launch runbook is done
FLOP_PARTICIPATION=false          # keep off until official FLOP software is pinned
ENABLE_NONCOMMERCIAL_SOURCE=false # Computable comparison feed
```

## License and attribution

Code: Apache-2.0. GPU Cloud Price Index data: CC BY 4.0 — credit [gpucloudcompare.com](https://gpucloudcompare.com/data/). Computable GPU Index is CC BY-NC 4.0 and stays off unless `ENABLE_NONCOMMERCIAL_SOURCE=true`.
