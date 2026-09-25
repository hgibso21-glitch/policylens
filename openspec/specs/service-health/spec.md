# service-health Specification

## Purpose
Let a platform such as OpenShift decide when to route traffic to, or restart, the service.

## Requirements

### Requirement: Liveness probe
The system SHALL answer `/healthz` with 200 without touching the database.

#### Scenario: Process is up
- **WHEN** a client GETs `/healthz`
- **THEN** the response is 200 with `{"status": "ok"}`

### Requirement: Readiness probe
The system SHALL answer `/readyz` with 200 only when it can query its database.

#### Scenario: Database reachable
- **WHEN** a client GETs `/readyz` and the database responds
- **THEN** the response is 200 with `{"status": "ready"}`
