# MVP Requirements Traceability

Status: Draft for Design Review

Last updated: 2026-07-11

Controlling Linear project: `Substrate / ContractView`

Source baseline: `solution_requirements.md` and `docs/product/pilot-decision-record.md`

## Purpose

Trace the exercise-level MVP backlog to the accepted architectural pillars, certifiable journeys, owning boundaries, and release gates. Story keys below are durable catalog identifiers and are included in the corresponding Linear issue descriptions.

## Trace

| Key | Requirement or story outcome | ADR pillar | Journey | Owning boundary | Release gate |
| --- | --- | --- | --- | --- | --- |
| DISC-01 | Confirm partner workflow, roles, volumes, outputs, and submission boundary | 2, 4 | 01-06 | API/workflow, configuration registry | Requirements coverage |
| DISC-02 | Secure pilot data-sharing terms and sanitized historical corpus | 1, 3 | 07, 09 | Provenance/event, extraction pipeline | Security/privacy, AI governance |
| DISC-03 | Inventory existing application and infrastructure before stack changes | 2, 3 | 08, 10 | Infrastructure, persistence | Architecture coverage |
| DISC-04 | Establish baseline metrics and return-reason taxonomy | 1, 3 | 01-07 | Reporting, provenance/event | Requirements coverage, provenance |
| FND-01 | Isolate agency and provider organizations and contract access | 4 | 01-08 | API/workflow | Human authority, security/privacy |
| FND-02 | Authenticate with MFA and enforce role/transition authorization | 4 | 03-08 | API/workflow | Human authority, security/privacy |
| FND-03 | Grant visible, scoped, time-bound support access | 1, 4 | 08 | API/workflow, provenance/event | Human authority, operational readiness |
| FND-04 | Import and version contract, budget, and purchase-order snapshots | 1, 2 | 01, 02, 10 | Configuration registry | Configuration governance, provenance |
| FND-05 | Store immutable artifacts with hashes, tenancy, and retention metadata | 1 | 01, 03, 07 | Ingestion, provenance/event | Provenance, security/privacy |
| FND-06 | Record append-only workflow events and field lineage | 1 | 01-10 | Provenance/event | Provenance |
| ING-01 | Upload mixed evidence with validation, scanning, and deduplication | 1 | 01 | Ingestion | Provenance, security/privacy |
| ING-02 | Import ledger and payroll rows with source-cell lineage | 1, 3 | 01 | Ingestion, extraction pipeline | Provenance, deterministic validation |
| ING-03 | Classify and extract documents with versioned AI/OCR provenance | 1, 3 | 01, 09 | Extraction pipeline | AI governance, provenance |
| ING-04 | Review and correct uncertain extraction without destructive overwrite | 1, 3, 4 | 09 | Extraction pipeline, API/workflow | AI governance, human authority |
| ING-05 | Assemble a draft invoice with mappings, allocations, and reconciliation | 1, 2, 3 | 01 | API/workflow | Deterministic validation, provenance |
| VAL-01 | Govern immutable configuration bundles through approval and activation | 2, 3, 4 | 08, 10 | Configuration registry | Configuration governance |
| VAL-02 | Execute deterministic rules with stable reason codes and reproducible runs | 1, 3 | 02, 10 | Validation engine | Deterministic validation, provenance |
| VAL-03 | Resolve findings and record authorized warning acceptance or exception | 1, 3, 4 | 02 | API/workflow, validation engine | Human authority, provenance |
| VAL-04 | Calculate available budget and reserve concurrent submissions atomically | 1, 3 | 02, 03, 05 | Validation engine, API/workflow | Deterministic validation, provenance |
| VAL-05 | Replay historical packages and certify rule/model quality | 1, 3 | 02, 09, 10 | Validation engine, extraction pipeline | Deterministic validation, AI governance |
| EXP-01 | Review, attest, and authorize an exact invoice/package version | 1, 4 | 03 | API/workflow | Human authority, provenance |
| EXP-02 | Generate a deterministic immutable package, manifests, and hashes | 1, 2, 3 | 03, 07 | Package generation | Deterministic validation, provenance |
| EXP-03 | Distinguish export from externally confirmed submission | 1, 4 | 03 | API/workflow | Human authority, provenance |
| EXP-04 | Return, revise, supersede, and resubmit without mutating history | 1, 4 | 04, 05 | API/workflow, provenance/event | Human authority, provenance |
| AGY-01 | Review provider packages in a scoped agency queue | 1, 4 | 04, 06 | Web app, API/workflow | Human authority, provenance |
| AGY-02 | Perform Level 1/Level 2 review and structured return/approval | 1, 4 | 04, 06 | API/workflow | Human authority, provenance |
| AGY-03 | Record authorized payment-review and disbursement status | 1, 4 | 06 | API/workflow | Human authority, provenance |
| AGY-04 | Reconstruct any submitted claim as a read-only auditor | 1 | 07 | Provenance/event | Provenance |
| OPS-01 | Notify users and calculate configured deadlines without implying authority | 2, 4 | 02-06, 08 | Notification service, API/workflow | Operational readiness |
| OPS-02 | Measure first-pass acceptance, cycle time, labor, and unsupported cases | 1 | 01-07 | Reporting | Requirements coverage, provenance |
| OPS-03 | Operate idempotent jobs, retries, dead letters, restore, and incident paths | 1, 3 | 01, 03, 09 | Infrastructure, owning services | Operational readiness |
| OPS-04 | Meet accessibility and supported-browser acceptance criteria | 4 | 01-08 | Web app, package generation | Requirements coverage |
| REL-01 | Certify all MVP journeys and assemble release evidence | 1-4 | 01-10 | Cross-cutting | All release gates |

## Explicit Validation Dependencies

The following are exercise defaults and must remain visible dependencies rather than hidden product facts:

- Customer and provider archetypes.
- Buying and sponsorship model.
- Contract types, actual workflow, volumes, and package distribution.
- Direct-submission commitments.
- Existing application and infrastructure inventory.
- Contractual data, retention, residency, and AI-processing terms.
- Historical evaluation corpus and existing accuracy methodology.
- Delivery team, onboarding capacity, and committed date.

## Coverage Assessment

- All MVP capabilities in `solution_requirements.md` map to at least one backlog story.
- All ten MVP-critical journeys map to implementation and certification work.
- All four ADR pillars are represented.
- Every release-certification gate has an owning story or explicit cross-cutting certification story.
- Customer-specific commitments remain unresolved by design; DISC stories convert them from assumptions into verified inputs.
