# Persistence Package

## Purpose

This package will define ContractView's relational database and cache system while preserving service-level ownership of canonical data.

## Responsibilities

- Define relational schemas, migrations, transaction boundaries, and storage adapter interfaces.
- Define cache namespaces, key formats, TTL policies, invalidation primitives, and cache compatibility rules.
- Provide deterministic migration ordering, compatibility checks, and test utilities for storage behavior.

## Data Owned

- No canonical domain data ownership.
- Each service owns the records in its schema and cache namespace; this package owns only their shared persistence definitions and mechanics.

## Allowed Dependencies

- `packages/domain-types` where stable domain primitives are required by a storage contract.
- No apps, service internals, or infrastructure implementation.

## Events And Evidence

- Migration version and outcome records.
- Schema compatibility and cache-policy test evidence.
- Material domain and provenance events remain the responsibility of the owning services.

## Configuration Consumed

- Versioned database connection, migration, pool, encryption, backup, cache endpoint, TTL, and namespace configuration.
- Secrets must be referenced through approved environment configuration and must not be committed in package definitions.

## Deterministic Requirements

- Migrations have a stable order and explicit forward/backward compatibility expectations.
- Cache keys and invalidation behavior are stable for the same namespace and version.
- Cache misses or eviction must not change compliance results or authoritative workflow state.

## Human Authority Boundary

The package performs storage mechanics only. It cannot approve, return, waive, attest, finalize, submit, or change payment status.

## Prohibited Responsibilities

- Cross-service table access or a shared mutable domain model.
- Cache state as canonical state or as the only audit/provenance record.
- Destructive migration behavior without explicit review, backup, recovery, and rollout evidence.
- Mutation of submitted packages or loss of historical configuration and provenance references.
