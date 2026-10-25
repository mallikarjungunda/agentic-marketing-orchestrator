# Architecture and boundaries

The Next.js UI sends same-origin requests through a server-side proxy. The proxy adds the API key, keeping the key out of browser JavaScript. FastAPI persists campaigns and approval/launch records in SQLAlchemy. LangGraph executes plan → draft → review, returning to draft at most twice. A failed reviewer blocks approval. Review completion pauses the business process by storing `awaiting_approval`; a version-bound decision API resumes the business process, not a LangGraph interrupt.

Planning and review are real LangGraph nodes. Demo mode is deterministic and performs zero model calls. Live OpenAI mode uses structured Pydantic outputs and an explicitly configured model. All offers and product information are fictional. The basic review is illustrative and is not a complete factual, legal or regulatory validator.

## Persistence and reliability

Campaign results, events, pending approvals and mock launch receipts survive process restarts. Within a generation request, retries are limited to transient exceptions and three attempts per node. There are at most three draft generations. Permanent errors are recorded as failed; a new run regenerates the full graph. Mock launch receipts are unique per campaign. PostgreSQL row locks serialize run/decision/launch operations on a campaign. SQLite is intended for single-user local development.

## Explicit starter limitations

- Generation runs synchronously in the API process. No durable worker queue or node-level LangGraph checkpoints yet. If the process dies mid-generation the transaction rolls back; the user must run it again.
- The database transaction holds a campaign row lock during model work. Replace with a leased job/worker architecture before scaling.
- UI status updates occur after requests finish; no token streaming or background progress feed yet.
- Backend uses a shared API key. The web UI has no end-user login or identity-based approval authority. Bind to localhost only; add OIDC, roles, CSRF protection and rate limits before hosting.
- Launch is an atomic database simulation. Real external launch needs a transactional outbox, provider-side idempotency and reconciliation of ambiguous outcomes.
- Tables are created at startup for initial setup. Introduce Alembic migrations before changing a shared database schema.
- No real campaign metrics or optimization agent yet.

## Next milestones

1. OIDC authentication and role-bound approval audit records.
2. Durable worker, queue, LangGraph PostgreSQL checkpoints, crash recovery and cancellation.
3. Versioned approved-document retrieval, richer review rules, evaluation datasets and cost/latency tracing.
4. Parallel brand/policy reviews and an explicit conflict policy.
5. AWS infrastructure as code, staging, secret manager, migrations and deployment workflow.
