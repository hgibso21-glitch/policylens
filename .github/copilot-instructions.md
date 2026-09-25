# Copilot instructions

Follow [AGENTS.md](../AGENTS.md) in the repository root. It is the single source of truth for commands, architecture rules and guardrails.

The essentials:

- Spec first: start behaviour changes with an OpenSpec change (`/opsx-propose`). Write the failing pytest test before the code.
- `app/engine.py` and `app/baseline.py` stay pure: no FastAPI, no SQLAlchemy, no I/O.
- Synthetic data only. No secrets, no outbound network calls.
- Never weaken tests or the coverage gate to get a green build.
- Run `ruff check .`, `ruff format --check .` and `pytest --cov` before proposing a change is done.
