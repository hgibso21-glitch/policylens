## Approach

Follow the pattern of `audit_ruleset` in `app/routes.py`:

1. Load the rule set with `_get_ruleset_or_404`.
2. Compile it with `repository.compile_stored`.
3. Build the query with `engine.make_query(src, dst, protocol, port)`. It raises `ValueError` for bad input, which the route turns into HTTP 422.
4. Call `engine.evaluate(rules, query)`.
5. Build `ReachabilityOut`, including an explanation.

## Explanation wording

- Matched rule: `Allowed by rule 2 ('web-to-app').` or `Denied by rule 5 ('deny-all').`
- No match: `Denied: no rule matched (implicit deny).`

## Decisions

- Query parameters, not a request body: the call is a read with no side effects.
- `port` is optional in the URL because ICMP has no port. `make_query` enforces that tcp and udp need one.
