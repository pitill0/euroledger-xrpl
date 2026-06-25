# EuroLedger XRPL Worker Components

This directory is reserved for future standalone worker packages or worker-specific tooling.

Current worker implementations live inside the backend application:

```text
backend/app/commands/xrpl_worker.py
backend/app/commands/payment_intent_expirer.py
backend/app/commands/webhook_worker.py
backend/app/workers/
```

They are executed as independent runtime processes using the backend container image.

## Current workers

EuroLedger XRPL currently uses:

```text
XRPL worker
Payment intent expirer
Webhook delivery worker
```

## Intended future scope

This directory may later contain:

- standalone worker packages;
- worker-specific Dockerfiles;
- worker deployment manifests;
- worker load testing tools;
- worker operational runbooks;
- reusable worker base classes;
- queue abstractions if the project moves beyond database-backed polling.

## Current status

```text
planned
```

There is no separate worker package in this directory yet.

## Recommended direction

Keep worker logic inside the backend package until there is a clear operational reason to split it.

A split may make sense when:

- worker dependencies diverge significantly from the API service;
- deployment targets differ;
- scaling requirements require independent packaging;
- a dedicated queue system is introduced;
- external users need to run only worker components.

## Related documentation

- `docs/architecture.md`
- `docs/backend-api-and-operations.md`
- `docs/payment-intent-expiration.md`
- `docs/merchant-webhook-operations.md`
- `backend/app/commands/`
- `backend/app/workers/`
