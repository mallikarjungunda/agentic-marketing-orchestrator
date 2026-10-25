# Agent Instructions

## Scope and precedence

These instructions apply to the entire repository. `AGENTS.md` is the canonical shared guidance for coding agents. Tool-specific instruction files may add usage notes, but they must not contradict this file.

## Project overview

Agentic Marketing Orchestrator is a learning-oriented full-stack application for campaign planning, drafting, review, human approval, and simulated launch.

- `apps/web`: Next.js 16 and TypeScript UI plus the server-side API proxy.
- `apps/api`: FastAPI, SQLAlchemy, Pydantic, and LangGraph orchestration.
- `apps/api/tests`: API and workflow behavior tests.
- `docs`: Architecture, development guidance, and documented limitations.
- `infra/aws`: Future deployment planning only; it does not create infrastructure.
- `openspec`: OpenSpec configuration, specifications, and change artifacts.

Read `README.md`, `docs/architecture.md`, and `docs/development.md` before making architectural or cross-cutting changes.

## OpenSpec workflow

The repository uses the `spec-driven` OpenSpec schema. For a non-trivial feature, behavior change, or architectural change:

1. Inspect `openspec/config.yaml`, current specs, and active changes.
2. Create or update the OpenSpec change artifacts before implementation.
3. Keep implementation and task checkboxes synchronized.
4. Run `openspec validate --all --strict` before considering the change complete.
5. Archive only after implementation and validation are complete.

Codex workflows live under `.agents/skills/openspec-*`. Do not hand-edit generated OpenSpec workflow files; refresh them with the OpenSpec CLI.

Small documentation corrections and narrowly scoped bug fixes do not require a new proposal unless the user explicitly requests the OpenSpec workflow.

## Engineering constraints

- Preserve deterministic demo mode; it must perform no model calls.
- Treat live-model behavior as opt-in and keep structured Pydantic outputs.
- Never turn the illustrative reviewer into an authoritative legal, factual, or compliance claim.
- Keep launch simulated unless the task explicitly introduces a safely designed external integration.
- Preserve version-bound approvals, valid state transitions, idempotent mock launch behavior, and PostgreSQL row-locking assumptions.
- Keep the API key server-side. Never expose secrets through browser bundles, logs, fixtures, or committed environment files.
- Do not present the starter as production-ready. Maintain the limitations documented in `docs/architecture.md` unless the implementation genuinely removes them.
- Add or update tests for API, orchestration, state-transition, persistence, or retry behavior changes.
- Update relevant documentation when behavior, configuration, architecture, or operational steps change.

## Validation commands

Run checks appropriate to the files changed. The standard full validation is:

```bash
PYTHONPATH=apps/api pytest apps/api/tests -q
cd apps/web && npm run typecheck && npm run build
openspec validate --all --strict
```

For an end-to-end local smoke test:

```bash
cp .env.example .env
docker compose up --build
```

Do not commit generated local environments, databases, caches, real credentials, or `.env` files.

## Completion criteria

A change is complete only when its requested behavior is implemented, relevant checks pass, documentation and OpenSpec artifacts are consistent, and no secrets or unrelated changes are included.
