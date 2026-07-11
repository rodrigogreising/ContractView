# Apps

This directory contains the implemented React web app and an admin-console
boundary placeholder. The web app is the POC user interface; a separately
deployed admin console is not part of the current runtime.

Apps are HTTP clients of the [modular-monolith](../docs/architecture/modular-monolith.md)
application boundary. They consume shared DTO contracts but never import
capability, persistence, or integration implementations.

Reference docs:

- [System map](../docs/architecture/system-map.md)
- [Service boundaries](../docs/architecture/service-boundaries.md)
- [Journey certification index](../docs/journeys/README.md)
- [ADR 0001](../docs/adr/0001-core-architectural-pillars.md)

## Dependency Rules

- Apps may depend on API contracts and shared domain types.
- Apps must not import service internals.
- Apps must submit material workflow changes through the API/workflow boundary.
- Apps must render role-specific views over shared canonical invoice state.
- Apps must not implement compliance-critical decisions only in client logic.
- Apps cannot submit actor roles, job results, validation outcomes, or workflow state as trusted facts.

## Certification Expectations

Future app tests must certify:

- Role-specific workflows for nonprofit, agency, auditor, support, and admin users.
- No stakeholder-specific invoice copies.
- Permission and authority controls are visible and enforced through server-side workflow commands.
- Evidence, validation reasons, confidence, and provenance summaries are understandable to users.
- Certified user journeys can be executed end to end through the UI when the relevant backend units exist.

## Current Units

- [web-app](web-app/README.md)
- [admin-console](admin-console/README.md)
