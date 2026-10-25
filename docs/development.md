# Development guide

## Modules

- `apps/web`: Next.js / TypeScript campaign workspace and server-side API proxy.
- `apps/api/app/schemas.py`: validated API and agent contracts.
- `apps/api/app/agents.py`: deterministic demo and live model adapters.
- `apps/api/app/orchestration.py`: bounded LangGraph workflow and retry policy.
- `apps/api/app/db.py`: campaign, event and mock launch persistence.
- `apps/api/app/main.py`: application factory, protected API and version-bound decisions.
- `apps/api/tests`: behavioral API and workflow checks.
- `infra/aws`: deployment planning; no resources created.

## API

Protected routes require `X-API-Key`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness |
| GET / POST | `/campaigns` | List or create campaigns |
| GET | `/campaigns/{id}` | Retrieve state and execution history |
| POST | `/campaigns/{id}/run` | Generate and review content |
| POST | `/campaigns/{id}/decision` | Submit `{"version":1,"decision":"approve"}` or reject |
| POST | `/campaigns/{id}/launch` | Idempotent mock launch of approved content |

A generation error returns the campaign with status `failed`; clients must inspect status. Stale decisions and invalid transitions return HTTP 409. Auth failures return 401.

## Interview exercises

Explain why durable business state differs from durable node execution. Add a worker crash test. Show why stale draft approval is rejected. Demonstrate two launch requests returning the same receipt. Explain which retries are safe and why an LLM reviewer is not an authoritative compliance gate.
