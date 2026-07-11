# POC Requirements Traceability

Status: Design Review recovery; prior Build trace retained pending SUB-59 approval

Last updated: 2026-07-11

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
| SUB-49 | Government return and approval | 1, 4 | 11 | Workflow | Human decision events |
| SUB-46 | NGO correction and resubmission | 1, 4 | 11 | Workflow/provenance | Immutable v1 and linked v2 |
| SUB-50 | Read-only audit timeline | 1 | 11 | Provenance/web | Both packages reconstructed |
| SUB-53 | Reproducible commands | 2, 3 | 11 | Infrastructure | Documented clean run |
| SUB-55 | Canonical E2E certification | 1-4 | 11 | Cross-cutting | Passing recorded Playwright run |
| SUB-59 | Enforceable modular-monolith layers, ownership, ontology split, and persistence rules | 1-4 | 11 and 01-10 reference | Architecture | ADR 0002 amendment, `modular-monolith.md`, machine policy and tests |

## Recovery Architecture Trace

| Requirement | ADR decision | Boundary owner | Certification evidence |
| --- | --- | --- | --- |
| One POC deployable without hidden coupling | ADR 0002 SUB-59 amendment | Six-layer API/worker modular monolith | Machine policy validates allowed layer direction |
| Configuration, invoice, artifact, extraction, validation, provenance, package, and workflow ownership | ADR 0002 plus ADR 0001 pillars 1-4 | Nine capability owners in `modular-monolith-policy.json` | Duplicate-owner and capability-cycle tests |
| No arbitrary cross-capability SQL | ADR 0002 persistence amendment | Application ports plus owner persistence adapters | Cross-capability SQL and ownership negative tests; REC-07 physical enforcement |
| Executable reimbursement ontology | ADR 0001 pillar 2 plus ADR 0002 amendment | Shared domain/config/rule/event contracts | Closed vocabulary and configuration/runtime split tests; REC-05 runtime contracts |
| Future extraction seams without distributed POC complexity | ADR 0002 | Capability application ports and events | Policy rejects shared tables and network-service expansion |

## Deferred And Canceled For POC

- SUB-29: production support access.
- SUB-42: historical/customer model certification.
- SUB-48: payment lifecycle.
- SUB-51: notifications and deadlines.
- SUB-52: business pilot analytics.
- SUB-54: full accessibility/browser certification.

## Coverage Decision

The active story set covers the complete charter and Journey 11. Production requirements remain documented in `solution_requirements.md` but are not POC completion criteria. Accessibility basics remain acceptance criteria within UI stories; AI fixture checks remain within extraction stories.
