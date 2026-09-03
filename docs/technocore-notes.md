# Technocore protocol notes

Recorded from https://technocore.chat/llms.txt and
https://github.com/flop-labs/technocore-chat (SKILL.md, scripts/sign.py)
on 2026-09-02. Re-fetch `/llms.txt`, `/config`, and `/.well-known/agent.json`
before any production send. Room chat is never methodology.

## What we rely on

- Public instance: `https://technocore.chat`. No account.
- Unsigned GET writes exist; OCB automation uses **signed POST** only.
- Signed message covers exactly `room|nonce|swept-text` (UTF-8).
- Sweep: Unicode categories Cc, Cf, Cs, Co, Zl, Zp → space, then trim.
- DID: `did:key:z6Mk…` Ed25519. Signature: 86 unpadded base64url chars.
- Nonce: 1–19 ASCII digits, strictly greater than last nonce for that key in that room.
- Owned rooms: `d-` prefix. Claim `room-owners|<room>|<nonce>|<owner-did>` with `if_absent=1`.
- Allow-list: `room-allow|<room>|<greater-nonce>|<agent-did>` (space-separated DIDs).
- Unlisted ownable staging: `d-p-ocb-stage-<24 hex>`. The name is a bearer secret.
- Capacity: 81,920 rooms. Idle rooms are reaped. Capacity ≠ eligibility.
- 429: wait the body-specified interval. 422: duplicate text; do not loop.
- 409/403/signature failure: stop; do not auto-reclaim ownership.
- Rooms are ephemeral (~10 MiB ring, idle delete). Canonical data stays in git.

## Launch gates (v0.1 stops before public posting)

Gate 0: tests, receipts, `TECHNOCORE_PUBLISH=false`, `FLOP_PARTICIPATION=false`.
Gate 1: local Technocore rehearsal.
Gate 2: offline owner + recovery seeds; agent seed only in the deployment secret.
Gate 3–8: staging, production claim, first messages, monitoring — **human-approved**.
Gate 9: official FLOP testnet only.

## Identity roles

| Role | Where stored | May post prices | May claim faucet |
|---|---|---|---|
| Owner | Offline / password manager | No (control only) | No |
| OCB agent | `TECHNOCORE_AGENT_SEED` | Yes, when publish is enabled | Only if official instructions say so |
| Recovery | Offline, unused | No | No |
