@AGENTS.md

## Claude Code specifics

- Spec-driven commands are installed: `/opsx:propose`, `/opsx:apply`, `/opsx:explore`, `/opsx:archive`, `/opsx:sync`, `/opsx:update`.
- `.claude/settings.json` enforces the guardrails above: `.env` files are unreadable, destructive git and cluster commands are denied, and edits to guardrail files ask for approval.
- A hook formats Python files with ruff after every edit.
- Use the `reviewer` subagent (`.claude/agents/reviewer.md`) for a read-only review before opening a PR.
