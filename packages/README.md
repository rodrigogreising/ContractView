# Packages

This directory contains README-only placeholders for future shared packages. Shared packages define contracts and fixtures; they must not hide service behavior or create implicit runtime coupling.

Reference docs:

- [System map](../docs/architecture/system-map.md)
- [Domain model](../docs/architecture/domain-model.md)
- [Service boundaries](../docs/architecture/service-boundaries.md)
- [Release certification](../docs/sdlc/release-certification.md)

## Dependency Rules

- Shared packages may define stable types, contracts, fixtures, and test utilities.
- Shared packages must not depend on service internals.
- Shared packages must not own runtime state.
- Storage definitions do not transfer data ownership from a service to a shared package.
- Shared packages must avoid framework-specific assumptions until a later ADR selects implementation technology.

## Certification Expectations

Future shared package tests must certify:

- Contract stability for events, rules, configuration, and domain primitives.
- Fixtures can support end-to-end journey certification.
- Shared contracts preserve provenance, deterministic validation, configuration lifecycle, and human authority requirements.
- Breaking changes are visible to services and apps through explicit versioning or migration notes.

## Current Units

- [domain-types](domain-types/README.md)
- [rule-contracts](rule-contracts/README.md)
- [event-contracts](event-contracts/README.md)
- [configuration-contracts](configuration-contracts/README.md)
- [infrastructure](infrastructure/README.md)
- [persistence](persistence/README.md)
- [test-fixtures](test-fixtures/README.md)
