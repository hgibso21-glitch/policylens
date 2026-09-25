## Why

Engineers ask "would this packet get through?" before they change a firewall. The engine already answers that (`evaluate` in `app/engine.py`) and the response schemas exist (`ReachabilityOut` in `app/schemas.py`), but no endpoint exposes it. This is the missing piece of the API.

## What Changes

- Add `GET /rulesets/{id}/reachability?src=&dst=&protocol=&port=`.
- Return the decision (allow or deny), the rule that decided it, and a one-sentence explanation.
- No database or engine changes.

## Capabilities

### New Capabilities
- `reachability`: answer whether one specific packet is allowed by a stored rule set.

### Modified Capabilities
None.

## Non-goals

- No batch queries or CSV upload.
- No IPv6.
- No change to how rules are matched.

## Impact

- `app/routes.py`: one new route.
- `app/schemas.py`: none expected; the schemas already exist and the explanation text is built in the route.
- `tests/test_api.py`: new `TestReachability` class.
