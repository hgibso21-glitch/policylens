# baseline-certification Specification

## Purpose
Decide whether a rule set meets the organisation's minimum security baseline.

## Requirements

### Requirement: Baseline checks
The system SHALL evaluate five checks: BL-001 no allow from any to any; BL-002 no SSH, Telnet or RDP open to any source; BL-003 the last rule is an explicit deny-all; BL-004 no shadowed rules; BL-005 no duplicate rules.

#### Scenario: Open management port
- **WHEN** an allow rule from any source includes tcp port 22, 23 or 3389
- **THEN** BL-002 fails and the detail names the rule and the exposed service

#### Scenario: Missing cleanup rule
- **WHEN** the final rule is not a deny from any to any on all services, or there are no rules
- **THEN** BL-003 fails

### Requirement: Certification result
The system SHALL mark a rule set certified only when every baseline check passes, and expose the result at `/rulesets/{id}/certification`.

#### Scenario: All checks pass
- **WHEN** no check fails
- **THEN** `certified` is true and all five checks are listed as passed

#### Scenario: Any check fails
- **WHEN** at least one check fails
- **THEN** `certified` is false and the failing checks carry human-readable details
