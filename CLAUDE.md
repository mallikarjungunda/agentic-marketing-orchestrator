# Claude Code Instructions

Read and follow `AGENTS.md` first. It is the canonical repository-wide instruction file; this file only adds Claude-specific operating notes.

## Repository workflow

- Work from the repository root so OpenSpec and project paths resolve correctly.
- Inspect `README.md`, `docs/architecture.md`, and `docs/development.md` before cross-cutting changes.
- Use the OpenSpec CLI for non-trivial features and architectural changes. Start by running `openspec list --json` and reading `openspec/config.yaml`.
- Before completion, run the relevant API and web checks from `AGENTS.md` plus `openspec validate --all --strict`.
- Keep edits focused. Do not silently weaken approval, state-transition, retry, idempotency, authentication, or secret-handling guarantees.

The `.agents/skills/openspec-*` files are generated for Codex. Do not modify them manually or treat them as project source code.
