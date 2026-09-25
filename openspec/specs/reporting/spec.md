# reporting Specification

## Purpose
Give a quick, SQL-backed overview of what is stored.

## Requirements

### Requirement: Summary report
The system SHALL report, for every rule set, the number of rules per action and per protocol at `/reports/summary`.

#### Scenario: Counts per group
- **WHEN** a rule set has one allow rule and one deny rule
- **THEN** its `by_action` lists allow 1 and deny 1

#### Scenario: No data
- **WHEN** nothing is stored
- **THEN** the report contains an empty list of rule sets
