## ADDED Requirements

### Requirement: Reachability query
The system SHALL decide whether one packet, described by source IP, destination IP, protocol and (for tcp and udp) destination port, is allowed by a stored rule set, using first-match-wins evaluation with an implicit deny.

#### Scenario: Allowed by a rule
- **WHEN** a client GETs `/rulesets/{id}/reachability` with a packet matched by an allow rule
- **THEN** the response is 200 with `action` "allow", the matching `rule_position` and `rule_name`, `implicit_deny` false, and an explanation naming the rule

#### Scenario: Denied by a rule
- **WHEN** the first matching rule is a deny rule
- **THEN** `action` is "deny", the rule is identified, and `implicit_deny` is false

#### Scenario: Implicit deny
- **WHEN** no rule matches the packet
- **THEN** `action` is "deny", `rule_position` and `rule_name` are null, and `implicit_deny` is true

#### Scenario: ICMP needs no port
- **WHEN** the protocol is icmp and no port is given
- **THEN** the query is evaluated normally

### Requirement: Reachability input validation
The system SHALL reject malformed queries and unknown rule sets.

#### Scenario: Unknown rule set
- **WHEN** the rule set id does not exist
- **THEN** the response is 404

#### Scenario: Invalid address or protocol
- **WHEN** `src` or `dst` is not an IPv4 address, or `protocol` is not tcp, udp or icmp
- **THEN** the response is 422

#### Scenario: Missing port
- **WHEN** the protocol is tcp or udp and `port` is missing
- **THEN** the response is 422
