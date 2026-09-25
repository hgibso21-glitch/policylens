## 1. Tests first

- [ ] 1.1 Add `TestReachability` to `tests/test_api.py`: allowed by a rule (check `rule_position` and `rule_name`)
- [ ] 1.2 Add tests: denied by an explicit deny rule, and implicit deny when nothing matches
- [ ] 1.3 Add tests: 404 for an unknown rule set, 422 for a bad IP, 422 for tcp without a port
- [ ] 1.4 Add a test that ICMP works without a port
- [ ] 1.5 Run `pytest` and confirm the new tests fail for the right reason

## 2. Implementation

- [ ] 2.1 Add the `reachability` route to `app/routes.py` following `audit_ruleset`
- [ ] 2.2 Build the `explanation` text as described in design.md
- [ ] 2.3 Make all new tests pass

## 3. Finish

- [ ] 3.1 `ruff check .`, `ruff format --check .` and `pytest --cov` all pass
- [ ] 3.2 Try it against the mock data: run with `SEED_MOCK_DATA=true`, then open `/docs`
- [ ] 3.3 Open a PR using the template, filling in the AI-usage section
- [ ] 3.4 After merge, archive the change with `/opsx:archive`
