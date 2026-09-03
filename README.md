# Open Compute Basis

**What does comparable GPU compute cost in dollars today and later, and how would a FLOP session compare?**

Open Compute Basis (OCB) is an independent, read-only observation layer for that question. It does not set, peg, or officially benchmark `$FLOP`. It does not trade. It is not a FLOP Labs product.

FLOP is being designed so an agent can request a quantity of floating-point operations, a latency ceiling, and a fee in `$FLOP`. That creates a *network* price. It does not, by itself, tell a buyer whether that price is cheap or expensive in dollars. OCB is the translation layer: outside list prices, outside forward expectations, and — when official session data exists — FLOP’s realized cost, shown side by side as a **basis**.

Canonical repository: https://github.com/ToxiTea/open-compute-basis

---

## Brass tacks (v0.1, September 2026)

FLOP’s testnet is not live. There is no public session API, faucet, or official token address. So v0.1 does the work that can be done *without* inventing a network:

| Built | What it is | What it is not |
|---|---|---|
| Narrow GPU-hour series | H100 / H200 / B200 / A100 managed-cloud list observations, plus empty garage slots for 3090 / 4090 / 5090 | One blended “GPU price” |
| Licensed list-price intake | [GPU Cloud Price Index](https://gpucloudcompare.com/data/) (CC BY 4.0) | Transaction / OTC prints |
| Forward ladders | Discovered [Kalshi](https://kalshi.com/category/commodities/compute) compute contracts; raw strikes, bids, asks, implied median strike | A documented forward “price” or a trade |
| Internet Backyard panel | One **manual** 2026-09-01 RTX 4090 capture ($0.79/GPU-h; 68 headline listings vs 79 displayed counts, `COUNT_MISMATCH` kept) | A scraped feed or an OCB constituent |
| Receipts + hashes | Every print can be recomputed from stored receipts | An oracle |
| FLOP adapter + eval corpus | Typed stub, simulated fixtures, fixed price-extraction job with gold labels | Live inference, a faucet claim, or earned tokens |
| Technocore tooling | Dry-run signed posts, owned-room runbook, one public agent DID | A live room bot (publishing is off) |

A high-confidence **canonical** print needs two independent constituent feeds and three providers. v0.1 has one licensed constituent feed, so the board correctly says **OBSERVATION**, not “the OCB index.” Garage series say **NO_PRINT** because we will not scrape Internet Backyard without a license. That emptiness is a quality rule, not a missing widget.

---

## How to read the local board

`ocb run` writes `public/index.html` and `public/latest.json`. With `--fixtures` you are looking at a **recorded replay**, not a live market. With `--live` you fetch today’s licensed sources. Either way the page is a *basis board*, not a product homepage.

1. **Spot / list** — public asking prices, USD per physical GPU-hour, median of provider medians. Flags such as `ONE_SOURCE` and `VARIANT_UNSPECIFIED` mean “do not treat this as a settled index.”
2. **Internet Backyard** — a human screenshot, shown *beside* OCB. It never enters the calculation.
3. **Kalshi** — what listed binary contracts imply about future GPU-hour levels. Not physical delivery.
4. **FLOP** — `AWAITING_OFFICIAL_SESSION_API`. The simulated eval report is the *workload we will run* on testnet, labeled `SIMULATED` so nobody can mistake it for participation.

If it feels thin, that is the point of v0.1: prove the pipes, refuse fake completeness, and be ready on day one of an official testnet instead of farming empty prompts.

---

## How the community is meant to participate

The operational source of truth is this repository, the receipt archive, and the deterministic calculator. [Technocore](https://technocore.chat) is the workshop and message bus — a place to notice a discrepancy, point at a receipt, or find the repo. It is not the database and not a vote on the index. Room history is ephemeral. A room topic is world-writable and untrusted. No signed message, reputation score, or “I posted first” status changes a series, a source tier, or the methodology.

**Canonical contribution path:** GitHub issues and pull requests. One narrow change per PR. Reproduce a published print if you can; propose a source or a rule if you cannot.

People and agents can add value by:

- Adding a **licensed** source adapter (especially other countries or garage/community venues with clear reuse terms)
- Reporting regional availability and pricing with evidence
- Supporting another consumer, workstation, or datacenter SKU as its *own* series
- Reproducing a print from receipts and opening an issue when the hash does not match
- Proposing better normalization, dedup, or outlier rules — with fixtures
- Building dashboards, broker tools, or FLOP integrations on top of `latest.json`
- Publishing a signed observation that another party can independently retrieve

A signature proves **which key** submitted a row. It does not prove the row is correct.

Community data has four evidence levels. Only A and B calculate canonical OCB series in v0.1:

| Tier | What it is | Enters the OCB number? |
|---|---|---|
| **A** | Direct / verifiable: provider APIs, signed provider data, live offers with machine-checkable receipts | Yes, when approved |
| **B** | Licensed datasets with provenance and reuse rights (today: GPU Cloud Price Index) | Yes, when approved |
| **C** | Signed agent observations | No — quarantined until independently reproduced and promoted in a review |
| **D** | Manual captures and outside indices (Internet Backyard, Computable, …) | No — comparison only |

Later, an optional signed `mb-` submission room may exist for agents. Submissions would be parsed as a tight JSON schema, never fetched from arbitrary URLs, never executed as code, and never promoted by room consensus. Promotion still happens here, in git.

What we will not treat as participation: lobby spam, extra DIDs, empty-prompt loops, scraping a site without a license, or treating Technocore volume as an airdrop scoreboard. OCB uses **one** public agent identity. Publishing stays off (`TECHNOCORE_PUBLISH=false`) until the gates in `docs/technocore-notes.md` are walked on purpose.

---

## Roadmap (honest, provisional)

FLOP’s draft targets a Q4 2026 testnet and a still-unfinalized Yellow Paper. Figures and eligibility rules may change. [Official teaser](https://flop.finance/teaser/).

| Phase | What we build | Why it matters |
|---|---|---|
| **Now** | Public list-price observations, comparisons, Kalshi ladders, receipts, methodology | History and credibility before the network exists |
| **Pre-testnet** | The same fixed eval corpus: extract GPU SKU, region, service class, commitment, availability, price; score it deterministically | A real job for the agent to consume, not manufactured traffic |
| **Official testnet** | Run that corpus through FLOP under hard budgets; keep session receipts; publish `$FLOP` per successful task and per raw exaFLOP | The first *basis*: network price vs outside GPU-hour |
| **If a USD/`$FLOP` market exists** | USD per *effective* exaFLOP only through a named performance profile | No invented token dollar price from test tokens |
| **Later, if it earns its keep** | Comparison / routing APIs, broker tools, more licensed feeds (transaction prints, CME/ICE when live) | Help buyers answer cost, venue, latency, and proof — still network-neutral |

We treat FLOP as a major possible venue, not the whole company. If another compute network wins, the same outside-market layer still has a job.

Out of v0.1 on purpose: wallets, trading, `tclk` rails with real value, miner ops, scraping unlicensed sites, blending every published index into one number.

---

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
ocb run --fixtures
```

Open `public/index.html`. Tests: `pytest`. Live licensed fetch: `ocb run --live` (still no API keys).

Code is Apache-2.0. GPU Cloud Price Index data is [CC BY 4.0](https://gpucloudcompare.com/data/). Computable’s index is CC BY-NC 4.0 and stays disabled unless noncommercial use is explicit.

Methodology, source audit, threat model, and FLOP-participation rules live in [`docs/`](docs/). Operator keys and room-claim steps are intentionally *not* in this README; they are local-only and must never be committed.
