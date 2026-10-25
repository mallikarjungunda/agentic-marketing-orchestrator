# Agentic Marketing Orchestrator

A full-stack learning application for marketing campaign planning, drafting, review, human approval and simulated launch. Built to practice enterprise agent orchestration and explain architectural tradeoffs.

**Starter v0.1:** working local campaign flow with Next.js, FastAPI, LangGraph and database persistence. Demo mode is deterministic: it does not call an LLM. A separate live-model adapter is included. Product facts are fictional and launch is simulated.

## Quick start — Docker Compose

Prerequisites: Git and Docker with Compose.

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:3000. Create a campaign, run the workflow, review the draft, approve its version, then simulate launch. FastAPI documentation: http://localhost:8000/docs (authorize requests through the X-API-Key header). Configuration examples are local-only; replace demo secrets before sharing any environment.

Stop with `docker compose down`. Database data remains in the named volume. `docker compose down -v` permanently deletes that local data.

## Run without Docker

Prerequisites: Python 3.12 and Node.js 22. The API defaults to a local SQLite file.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
export API_KEY=local-demo-change-me
export LLM_PROVIDER=demo
uvicorn app.main:create_app --factory --app-dir apps/api --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd apps/web
cp .env.local.example .env.local
npm ci
npm run dev
```

## Optional live-model mode

In root `.env` for Docker, set `LLM_PROVIDER=openai`, `LLM_MODEL` to a model available in your account that supports structured outputs, and `OPENAI_API_KEY` to your key. Model calls incur provider charges. Restart/recreate API and web services. For non-Docker runs, export these variables in the API shell and set `APP_MODE=openai` in the web `.env.local` before restarting. Keep real keys out of Git. API keys are passed from the server-side web proxy and are never intentionally exposed to browser bundles.

## Tests and checks

```bash
PYTHONPATH=apps/api pytest apps/api/tests -q
cd apps/web
npm run build
```

CI runs the API tests and web build on push/PR. Python dependencies and npm dependencies are locked in `requirements.txt` and `package-lock.json`.

## Repository structure

| Directory | Responsibility |
| --- | --- |
| `apps/web` | Campaign UI and backend proxy |
| `apps/api/app` | API, agent adapters, orchestration and persistence |
| `apps/api/tests` | Workflow and API behavior tests |
| `docs` | Architecture, API reference and next milestones |
| `infra/aws` | Future AWS deployment plan |
| `.github/workflows` | CI checks |

See [architecture and limitations](docs/architecture.md) before extending or deploying. This starter uses synchronous graph execution, a shared backend API key, and a localhost-only web UI without user login. It does not yet provide durable per-node recovery, a background worker, real campaign launch, or production compliance validation.
