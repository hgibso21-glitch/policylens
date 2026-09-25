# Agentic workflow

How to work on PolicyLens with an AI coding agent without giving up control of the result. The rules themselves live in [AGENTS.md](../AGENTS.md); this page explains how to use them.

## The idea

An agent is fast and confident and does not know your intent. So the intent is written down first (a spec), the agent is constrained by rules it can read (AGENTS.md) and rules it cannot bypass (permissions, CI), and a human stays accountable for what merges.

## The loop

| Step | You | The agent | Evidence |
|---|---|---|---|
| 1. Explore | Describe the problem; ask questions | `/opsx:explore` helps you think it through | Notes only, nothing changes |
| 2. Propose | Review and correct the proposal | `/opsx:propose` drafts proposal, design, delta spec and tasks | `openspec/changes/<name>/` |
| 3. Test first | Read the tests and check they match the spec | Writes failing pytest tests for each scenario | Red test run |
| 4. Implement | Watch for scope creep | `/opsx:apply` works through `tasks.md`, one task at a time | Green test run |
| 5. Verify | Run the checks yourself | Runs `ruff` and `pytest --cov` and reports honestly | Real command output |
| 6. Review | Read the whole diff | The `reviewer` subagent checks it read-only | Review notes |
| 7. Pull request | Fill in the AI-usage section | Nothing | PR |
| 8. Archive | Confirm the merge | `/opsx:archive` folds the delta spec into `openspec/specs/` | Updated specs |

## Try it: the first change

The open change [add-reachability-endpoint](../openspec/changes/add-reachability-endpoint/) is ready to work on:

1. Read `proposal.md`, `design.md`, the delta spec and `tasks.md`.
2. In Claude Code run `/opsx:apply`, or in Copilot Chat run `/opsx-apply`.
3. Stop after task group 1 (tests). Run `pytest` and confirm the new tests fail, and that they fail for the reason you expect.
4. Continue to implementation. When done, run the `reviewer` agent.

## Where each guardrail lives

| Guardrail | File | Enforced by |
|---|---|---|
| Architecture and conduct rules | `AGENTS.md` | The agent reading it, plus review |
| Secrets unreadable, destructive commands blocked | `.claude/settings.json` | The tool itself |
| Guardrail files need approval to edit | `.claude/settings.json` (`ask` rules) | The tool, with a human prompt |
| Formatting after every edit | `.claude/hooks/format_python.py` | A hook |
| Behaviour matches the spec | `openspec/` | `openspec validate` in CI, plus the reviewer |
| Tests and coverage | `pyproject.toml` | CI (`pytest --cov`, 85% gate) |
| Manifests stay secure | `tests/test_manifests.py` | CI |
| Human accountability | `.github/pull_request_template.md` | Review |

Layers matter: AGENTS.md is advice an agent can ignore; permissions and CI are enforcement it cannot.

## Turning on branch protection

In repo Settings, Branches, add a rule for `main`: require a pull request, require the `Lint and test`, `Validate OpenSpec` and `Build and smoke-test image` checks, and require one approving review. Now the guardrails apply to everyone, agent or human.

## Habits that make this work

- **Small changes.** One OpenSpec change per branch. Agents drift on big tasks.
- **Specific prompts.** "Add the reachability route following `audit_ruleset`, using the scenarios in the delta spec" beats "add reachability".
- **Read before you run.** Never approve a command you do not understand.
- **Fail first.** A test you never saw fail proves nothing.
- **Say what the AI did.** In the PR, name the tools and what you personally checked.
- **Own it.** If you cannot explain a line, do not merge it.

## Adding to the guardrails

When an agent makes a mistake, ask what would have stopped it: a sentence in AGENTS.md, a permission rule, a test, or a CI check. Prefer the strongest option that fits, and propose it in a pull request. Changes to guardrail files always get human review.
