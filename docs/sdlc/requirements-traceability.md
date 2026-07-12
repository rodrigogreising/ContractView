# POC Requirements Traceability

Status: Evidence Review; SUB-66 recovery recertification in progress

Last updated: 2026-07-12

## Trace

| Linear | POC outcome | ADR pillar | Journey | Owner | Build/release evidence |
| --- | --- | --- | --- | --- | --- |
| SUB-24 | Canonical role-based demo contract | 1-4 | 11 | Product | Approved charter and journey |
| SUB-25 | Synthetic fixture pack | 1, 3 | 11 | Test fixtures | Deterministic seed/reset |
| SUB-26 | Playwright recording harness | 1-4 | 11 | Web/test | Video, trace, screenshots |
| SUB-23 | Docker Compose runtime | 2, 3 | 11 | Infrastructure | Clean startup |
| SUB-27 | Agency/NGO organization boundaries | 4 | 11 | Identity/workflow | Cross-scope denial tests |
| SUB-28 | Seeded login/logout and RBAC UI/API | 4 | 11 | Identity/workflow | Session and permission tests |
| SUB-30 | Contract, budget, rule, workflow, package config | 2, 3 | 11 | Configuration | Immutable activation version |
| SUB-31 | Immutable artifact storage and hashes | 1 | 11 | Ingestion/artifacts | Integrity assertions |
| SUB-32 | Events, lineage, and audit queries | 1 | 11 | Provenance | Source-to-approval reconstruction |
| SUB-34 | UI upload and real processing status | 1 | 11 | Ingestion | Artifact/job evidence |
| SUB-33 | Ledger import with row lineage | 1, 3 | 11 | Extraction | Reconciled fixture import |
| SUB-35 | One real OCR/LLM extraction path | 1, 3 | 11 | Extraction | Golden fixture and trace |
| SUB-36 | Human extraction review/correction | 1, 3, 4 | 11 | Extraction/workflow | Correction lineage |
| SUB-37 | Evidence-linked draft assembly | 1, 2, 3 | 11 | Invoice/workflow | Mapped totals and sources |
| SUB-38 | Small configuration admin UI | 2, 3, 4 | 11 | Configuration/web | Activated version through UI |
| SUB-40 | Deterministic validation rules | 1, 3 | 11 | Validation | Stable rerun tests |
| SUB-39 | Finding resolution | 1, 3, 4 | 11 | Workflow/validation | Blocker and warning paths |
| SUB-41 | Budget availability | 1, 3 | 11 | Validation | Exact decimal tests |
| SUB-43 | NGO approver attestation | 1, 4 | 11 | Workflow | Actor/version event |
| SUB-44 | Real immutable package generation | 1-3 | 11 | Package generation | PDF/manifest/ZIP hashes |
| SUB-45 | Submit version to government queue | 1, 4 | 11 | Workflow | Locked version and event |
| SUB-47 | Government review queue | 1, 4 | 11 | Web/workflow | Scoped review UI |
| SUB-49 | Exact-line government return and corrected-version approval | 1, 4 | 11 | Workflow with Invoices query port and Provenance evidence | Provisioned-human authority; decision-specific reasons; nonblank note; exact unique v1 line keys; zero-mutation denials; actor/resource organizations; invoice/submission/package/decision references; v2-only approval |
| SUB-46 | NGO correction and resubmission | 1, 4 | 11 | Workflow/provenance | Immutable v1 and linked v2 |
| SUB-50 | Read-only audit timeline | 1 | 11 | Provenance/web | Both packages reconstructed |
| SUB-53 | Reproducible commands | 2, 3 | 11 | Infrastructure | Documented clean run |
| SUB-55 | Canonical E2E certification | 1-4 | 11 | Cross-cutting | Passing recorded Playwright run |
| SUB-59 | Enforceable modular-monolith layers, ownership, ontology split, and persistence rules | 1-4 | 11 and 01-10 reference | Architecture | ADR 0002 amendment, `modular-monolith.md`, machine policy and tests |
| SUB-61 | Executable ontology, closed vocabulary, compatibility rules, and generated API/web contracts | 1-4 | 01-11 reference | Shared contract packages | Four versioned registries, two generated consumers, compatibility/drift/consumer tests |
| SUB-62 | Physical module layers, capability repositories, table ownership, and explicit transactions | 1-4 | 01-11 reference | API/worker modular monolith | 39 table owners, 149 named statements, forbidden-import/ownership/transaction tests, clean Compose regression |
| SUB-63 | Complete configuration lifecycle, immutable test evidence, human approval, supersession, retirement, and rollback | 2-4 | 11 | Configuration/web | Generated lifecycle DTOs, 43 table owners, 157 named statements, semantic/hash/lifecycle/API/UI/authorization/immutability tests, clean Compose regression |
| SUB-64 | Versioned events and relations, exact invoice snapshots, corrected field lineage, immutable v1, reconstructable v2 | 1-4 | 11 | Provenance/invoices/workflow | 45 table owners, 167 named statements, envelope/trigger/relation/snapshot/lineage/auditor integration tests |
| SUB-67 | Pinned hermetic CI, isolated state, deterministic reset, and durable machine evidence | 1-4 | 11 precursor | Delivery/architecture/release | Exact tool/action/image pins, static gates, two fresh-volume Compose passes, schema-valid hashed artifact manifest, required master check |
| SUB-68 | Content-addressed validation inputs and reproducible package bytes | 1-4 | 11 | Validation/packages/provenance | Immutable snapshot/config/version manifests, shared rule/template execution, deterministic result/file/archive replay, changed-input trace |
| SUB-65 | Feature-owned web modules, server contract context, and demo credential boundary | 1-4 | 11 | Web/identity/all role projections | Generated ContractContext DTO, feature API/render modules, five role workspaces, API-error/visibility/accessibility tests, production-bundle scan |
| SUB-79 | Brand-neutral, privacy-safe public repository candidate | 1-4 synthetic POC boundary | 11 reference; no new runtime journey | Publication boundary and fixture generation | Reserved-domain identities, deterministic binary fixtures, history-free allowlisted export, content/metadata/secret scans, clean candidate regression, immutable AI review |
| SUB-66 | Reconcile all historical Done claims and recertify the merged recovery baseline | 1-4 | 11 clean-runtime precursor | Cross-cutting SDLC/release evidence | Exact 37-issue audit, ten merged prerequisite proofs, invalidated-claim register, owned exceptions, fail-closed continuation gate, clean static/Compose/hosted evidence |

## Recovery Architecture Trace

| Requirement | ADR decision | Boundary owner | Release criterion | Certification evidence |
| --- | --- | --- | --- | --- |
| One POC deployable without hidden coupling | ADR 0002 SUB-59 amendment | Six-layer API/worker modular monolith | Architecture coverage | Machine policy validates allowed layer direction |
| Configuration, invoice, artifact, extraction, validation, provenance, package, and workflow ownership | ADR 0002 plus ADR 0001 pillars 1-4 | Nine capability owners in `modular-monolith-policy.json` | Architecture coverage | Duplicate-owner and capability-cycle tests |
| No arbitrary cross-capability SQL | ADR 0002 persistence amendment | Application ports plus owner persistence adapters | Architecture coverage | Cross-capability SQL and ownership negative tests; REC-07 physical enforcement |
| Physical dependency and transaction boundaries | ADR 0002 SUB-62 implementation note | Domain/application/persistence/integration/worker/HTTP layers | Boundary and implementation coverage | Machine module policy, named statement catalog, runtime wrong-owner rejection, clean regression |
| Executable reimbursement ontology | ADR 0001 pillar 2 plus ADR 0002 SUB-59/SUB-61 amendments | Shared domain/config/rule/event contracts | Requirements coverage; Configuration governance; Deterministic validation; Provenance | Four `1.0.0` registries, generated Pydantic/TypeScript consumers, closed-vocabulary and additive-compatibility tests |
| Governed configuration lifecycle | ADR 0002 SUB-63 implementation note | Configuration application commands and capability-owned persistence | Configuration governance; Security/privacy; Journey 11 | Immutable definition/test/approval/event tables, prospective active projection, normal-session HTTP path, deterministic rollback hashes, bounded administrator UI |
| Versioned provenance and immutable invoice snapshots | ADR 0002 SUB-64 implementation note | Provenance event/relation writers, Invoices snapshot repository, submitted audit read model | Provenance; Security/privacy; Journey 11 | Required event envelope, all eight typed relations, stage snapshot foreign keys, exact expense-date and v1-to-v2 same-field lineage, append-only database tests |
| Reproducible delivery evidence | ADR 0002 SUB-67 implementation note | CI certification adapter over all modular-monolith validators and runtime | Architecture, operational, evidence, and release coverage | Pinned toolchains, two isolated Compose passes, equal semantic fingerprints, hashed machine-readable manifest, required GitHub check |
| Reproducible validation and package execution | ADR 0002 SUB-68 amendment | Validation/Packages owners plus shared application contract assembler | Deterministic validation; Provenance; AI/config governance; Journey 11 | Validation input and package reproduction manifests, shared rule/template contracts, exact result and byte replay, append-only/integrity tests |
| Web capability and authority separation | ADR 0002 SUB-65 note | React transport/features/workspaces plus server identity read model | Architecture; Security/privacy; Human authority; Journey 11 | No fetch outside transport, no production demo/fixed-contract literal, canonical contract-context tests, five role workspaces, 17 frontend tests |
| Public disclosure without private control-plane or identity leakage | Existing synthetic/non-branded POC boundary; no runtime architecture change | Publication export and fixture-generation tooling | Security/privacy; Release readiness | Allowlisted history-free tree, neutral identity rewrite, reserved-domain catalogs, binary metadata inspection, SHA-256 manifest, candidate-owned clean regression |
| Future extraction seams without distributed POC complexity | ADR 0002 | Capability application ports and events | Architecture coverage; Operational readiness when extraction occurs | Policy rejects shared tables and network-service expansion |

## Deferred And Canceled For POC

- SUB-29: production support access.
- SUB-42: historical/customer model certification.
- SUB-48: payment lifecycle.
- SUB-51: notifications and deadlines.
- SUB-52: business pilot analytics.
- SUB-54: full accessibility/browser certification.

## Coverage Decision

The active story set covers the complete charter and Journey 11. Production requirements remain documented in `solution_requirements.md` but are not POC completion criteria. Accessibility basics remain acceptance criteria within UI stories; AI fixture checks remain within extraction stories.
