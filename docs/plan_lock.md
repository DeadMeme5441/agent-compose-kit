---
title: Plan Lock
---

# Plan Lock

`compose.plan_lock(cfg, registry_resolves, alias_resolves) -> LockfilePlan`

Inputs (provided by your backend; no network here):
- `registry_resolves(kind, key, range) -> { version, etag?, uri? }`
- `alias_resolves(alias) -> { provider?, model, resolver?, secret_ref?, params? }`

Output structure:
- `registryPins: [ { kind, key, range, pinned?, etag?, uri?, ref?, error? } ]`
- `aliasPins: [ { alias, provider?, model?, resolver?, secret_ref?, params_fingerprint? } ]`

Deterministic and order‑independent, suitable for persisting alongside your config.

