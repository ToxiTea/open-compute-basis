# Threat model — OCB v0.1

## Assets

- Canonical receipts, prints, and methodology (the product).
- Offline owner and recovery Technocore seeds.
- Persistent public OCB agent seed (`TECHNOCORE_AGENT_SEED`).
- Future official FLOP faucet / session credentials (none configured).

## Actors

Curious users, competing agents, room spammers, compromised CI, poisoned
price feeds, and anyone claiming unofficial token or faucet instructions.

## Threats and controls

### Prompt injection via Technocore

Room bodies, topics, `/rooms` names, and unsigned nicks are untrusted data.
OCB never executes text from a room, never fetches arbitrary submitted URLs,
and never lets a room message change methodology, sources, or flags.

### Forged identities

Unsigned posts prove nothing. Signed `did:key` posts prove key possession only.
Production room writes require the owner or the allow-listed OCB agent.
Unexpected writer DIDs are a stop-and-alert condition.

### Stale or manipulated list prices

Fail closed on stale sources. Median-of-provider-medians resists listing spam.
Extreme IQR outliers are dropped. One-source results cannot become canonical.
Comparison indices are never blended (double-counting risk).

### Secret leakage

No `--seed` in documented CLI usage. Seeds from stdin, a masked prompt, or
the deployment secret. Logs redact seed-shaped hex, `did:key` private material,
and Authorization headers. Tests assert logs never contain the agent seed.
Secret scanning in CI. Owner/recovery seeds stay offline.

### False FLOP / token social engineering

`FLOP_PARTICIPATION` stays false until official FLOP Labs software and
instructions are pinned. Social posts, DMs, room topics, and community token
addresses are not authority. No wallet is configured. Simulated fixtures cannot
touch a network.

### Replay and nonce reuse

Technocore nonces are 1–19 ASCII digits, strictly increasing per key per room,
stored durably. Signed automation uses POST, not signed GET URLs.

### Availability / farming pressure

At most one useful digest per UTC day (unless a configured material move).
Continuity messages at most once per five days. No empty-prompt loops.
Inference jobs require a named corpus, hashes, and a deterministic score.

## Residual risk

A compromised GitHub Actions secret can post as the OCB agent until the owner
revokes the allow-list. List-price sources can be wrong in correlated ways.
Manual Internet Backyard entries can be mistyped; they are comparison-only.
