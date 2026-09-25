# AGENTS.md

Instructions for AI coding agents (Claude Code, GitHub Copilot, Codex and others) and for the humans working with them. Read this before changing anything.

## Project

PolicyLens is a small FastAPI service that analyses firewall rule sets: it audits them for redundant or over-permissive rules and certifies them against a baseline. **All data is synthetic mock data.** Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2 (SQLite), pytest, ruff. It ships as a Docker image to OpenShift.

## Commands

Activate the virtual environment first (`python -m venv .venv`, then `.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate` elsewhere).

| Task | Command |
|---|---|
| Install | `pip install -e ".[dev]"` |
| Test | `pytest` |
| Test with coverage (CI gate: 85%) | `pytest --cov` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Validate specs | `npx @fission-ai/openspec@1 validate --all --strict` |
| Run with mock data | set `SEED_MOCK_DATA=true`, then `uvicorn app.main:app --reload` |
| Build image | `docker build -t policylens .` |

## Architecture rules

- `app/engine.py` and `app/baseline.py` are **pure logic**. They must not import FastAPI, SQLAlchemy or `app.db`, and must not do I/O.
- `app/routes.py` only translates HTTP to those functions. No business rules in routes.
- `app/repository.py` is the only module that writes to the database. Raw SQL for reports lives only in `app/reports.py`.
- Request and response shapes live in `app/schemas.py`. Return Pydantic models, not dicts.
- Bad user input is a `ValueError` in the pure layer and an HTTP 422 in the route. Unknown ids are 404.

## Workflow: spec first, tests first

1. **Spec.** Every behaviour change starts as an OpenSpec change in `openspec/changes/<name>/` (`/opsx:propose` in Claude Code, `/opsx-propose` in Copilot). Read `openspec/specs/` for current behaviour.
2. **Test.** Write the failing pytest test for a scenario before the code that satisfies it. Run it and confirm it fails for the right reason.
3. **Implement.** The smallest change that makes the test pass. Follow the existing pattern in the neighbouring code.
4. **Verify.** Run `ruff check .`, `ruff format --check .` and `pytest --cov`. Report the real output; never claim a check passed without running it.
5. **Review.** A human reads the diff before it merges. Open the PR from the template and fill in the AI-usage section.
6. **Archive.** After merge, archive the change (`/opsx:archive`) so `openspec/specs/` stays the source of truth.

**Reusing this scaffold for a new project:** follow [docs/adapting-the-template.md](docs/adapting-the-template.md). Do it as an OpenSpec change, and leave no stale names, data or specs from the example behind.

## Guardrails

**Always**
- Keep changes small and on topic: one OpenSpec change per branch.
- Add or update tests with every behaviour change. Tests use the in-memory database fixture in `tests/conftest.py`.
- Keep `ruff` clean and coverage at or above 85%.
- Use synthetic data only: RFC 1918 ranges (`10.x`, `172.16-31.x`, `192.168.x`) and documentation ranges (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`).

**Never**
- Never commit secrets, tokens, kubeconfigs or `.env` files. Configuration comes from environment variables (see `.env.example`).
- Never use real company data, real IP plans, or real firewall configs.
- Never make outbound network calls from the app or the tests.
- Never weaken a test, lower the coverage gate, or add `# noqa` or `skip` to get a green run. Fix the cause or ask.
- Never run `git push --force`, `git reset --hard`, or delete cluster resources. Never run `oc login`; a human logs in.
- Never add a dependency without saying why in the PR.

**Ask a human first**
- Changing `AGENTS.md`, `.github/workflows/`, `.claude/`, `Dockerfile` or `deploy/openshift/`. These control what agents may do and what reaches the cluster.
- Anything that changes an existing OpenSpec requirement rather than adding one.
- Any step where the spec is ambiguous. Ask; do not guess.

## OpenShift and container constraints

- The container runs as a random non-root user in group 0 and listens on **8080**. Do not add `USER root` or a port below 1024.
- Anything the app writes must be under `/data`, which is group-writable.
- `tests/test_manifests.py` enforces the security settings in `deploy/openshift/`. If it fails, fix the manifest.

## Responsible AI use

AI assistance is expected here, and so is accountability. Whoever opens the PR must be able to explain every line in it. Review generated code as if a stranger wrote it, run it, and say in the PR what the AI did and what you checked.
