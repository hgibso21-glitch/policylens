# ruleset-audit Specification

## Purpose
Report rules that are redundant or dangerously broad so an engineer can clean them up.

## Requirements

### Requirement: Detect redundant rules
The system SHALL report a rule as shadowed when an earlier rule already matches every packet the later rule would match, and as a duplicate when both rules cover each other with the same action.

#### Scenario: Duplicate rule
- **WHEN** two rules match exactly the same traffic with the same action
- **THEN** the later rule is reported as `duplicate` with severity `low`

#### Scenario: Shadowed rule, same action
- **WHEN** an earlier rule with the same action covers a narrower later rule
- **THEN** the later rule is reported as `shadowed` with severity `medium`

#### Scenario: Shadowed rule, opposite action
- **WHEN** an earlier rule with the opposite action covers a later rule
- **THEN** the later rule is reported as `shadowed` with severity `high`, naming the earlier rule

### Requirement: Detect permissive rules
The system SHALL report allow rules that accept every service from any source.

#### Scenario: Any to any
- **WHEN** an allow rule has any source, any destination and all services
- **THEN** it is reported as `permissive` with severity `critical`

#### Scenario: Any source to a destination
- **WHEN** an allow rule has any source and all services but a specific destination
- **THEN** it is reported as `permissive` with severity `high`

### Requirement: Audit endpoint
The system SHALL expose findings at `/rulesets/{id}/audit`, ordered by rule position.

#### Scenario: Clean rule set
- **WHEN** a rule set has no findings
- **THEN** `finding_count` is 0 and `findings` is empty
