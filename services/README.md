# Services

This directory contains the implemented FastAPI API/worker under
`api-workflow` plus README boundary placeholders for capability ownership and
future extraction seams. The POC remains one
[modular-monolith](../docs/architecture/modular-monolith.md) API plus one
worker; the other folders are not independently deployed services and do not
authorize network calls or cross-capability imports.

Reference docs:

- [System map](../docs/architecture/system-map.md)
- [Service boundaries](../docs/architecture/service-boundaries.md)
- [Data flow](../docs/architecture/data-flow.md)
- [Journey certification index](../docs/journeys/README.md)

## Dependency Rules

- Services may depend on shared packages, but must not import another service's internal implementation.
- Each service must own a clear behavior and data boundary.
- Cross-service behavior must use explicit APIs, commands, events, or versioned contracts.
- Reporting projections must not become canonical workflow state.
- AI-assisted services may draft, classify, summarize, or suggest, but must not approve, waive, attest, finalize, or block submission.
- Capability modules collaborate through application ports, immutable snapshots, versioned events, or declared read models.
- Direct cross-capability SQL, table writes, shared mutable ORM models, and repository connection escape hatches are forbidden.

## Certification Expectations

Future service tests must certify:

- Deterministic behavior where required by ADR 0001.
- Immutable artifact and package references where applicable.
- Append-only material events and field-level lineage where applicable.
- Configuration bundle versioning where applicable.
- Human authority boundaries for workflow decisions.
- End-to-end journey evidence for every in-scope release.

## Current Units

- [api-workflow](api-workflow/README.md)
- [ingestion](ingestion/README.md)
- [extraction-pipeline](extraction-pipeline/README.md)
- [validation-engine](validation-engine/README.md)
- [package-generation](package-generation/README.md)
- [provenance-event](provenance-event/README.md)
- [configuration-registry](configuration-registry/README.md)
- [reporting](reporting/README.md)
- [notification](notification/README.md)
