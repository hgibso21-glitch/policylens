# ruleset-management Specification

## Purpose
Store firewall rule sets and their address objects so they can be analysed later.

## Requirements

### Requirement: Create a rule set
The system SHALL accept a rule set (name, address objects, ordered rules) and store it, keeping the rule order as submitted.

#### Scenario: Valid rule set is stored
- **WHEN** a client POSTs a valid rule set to `/rulesets`
- **THEN** the response is 201 and each rule has a 1-based `position` in submitted order

#### Scenario: Unknown address object is rejected
- **WHEN** a rule refers to an address object name that is not defined
- **THEN** the response is 422, the detail names the missing object, and nothing is stored

#### Scenario: Malformed input is rejected
- **WHEN** a rule set has no rules, or an invalid CIDR, port, protocol or action
- **THEN** the response is 422 and nothing is stored

### Requirement: Read rule sets
The system SHALL list stored rule sets with their rule counts and return one rule set by id.

#### Scenario: List rule sets
- **WHEN** a client GETs `/rulesets`
- **THEN** each rule set appears with its id, name and rule count

#### Scenario: Unknown rule set
- **WHEN** a client GETs `/rulesets/{id}` for an id that does not exist
- **THEN** the response is 404
