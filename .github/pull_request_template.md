## What and why

<!-- One or two sentences. Link the OpenSpec change: openspec/changes/<name>/ -->

## Spec and tests

- [ ] Every scenario in the spec has at least one test
- [ ] I saw each new test fail before I made it pass
- [ ] `ruff check .`, `ruff format --check .` and `pytest --cov` pass locally

## AI usage

<!-- Required. Be specific; "none" is a fine answer. -->

- **Tools used:**
- **What the AI did:**
- **What I checked myself:** (ran it, read every line, tried a bad input, ...)

## Guardrails

- [ ] Synthetic data only, no secrets, no outbound network calls
- [ ] No tests weakened or skipped, coverage gate unchanged
- [ ] I did not change `AGENTS.md`, workflows, `.claude/`, Dockerfile or `deploy/` without saying so above
- [ ] I can explain every line in this PR
