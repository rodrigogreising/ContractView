# ContractView Requirements Traceability

Status: Journey 11 POC certified; SUB-74 configurable document-intake MVP
design review active

Last updated: 2026-07-13

## Trace

| Linear | POC outcome | ADR pillar | Journey | Owner | Build/release evidence |
| --- | --- | --- | --- | --- | --- |
| SUB-24 | Canonical role-based demo contract | 1-4 | 11 | Product | Approved charter and journey |
| SUB-25 | Synthetic fixture pack | 1, 3 | 11 | Test fixtures | Deterministic seed/reset |
| SUB-26 | Canonical Playwright recording harness | 1-4 | 11 | External browser certification adapter over public web/API surfaces | Isolated reset/Compose; five normal persona sessions; visible complete lifecycle; direct 403 assertions; immutable v1/distinct v2 archive hashes matched in audit; headless CI plus paced headed video, trace, screenshots, JSON, logs, and Compose state |
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
| SUB-46 | Exact-line NGO correction and resubmission | 1, 3, 4 | 11 | Invoices correction command with Workflow read model and Provenance evidence | Persisted decision-bound line; zero-mutation denial; normalized correction/decision lineage; deterministic v2 revalidation; separate Approver attestation/package/resubmission; byte/hash/finding/feedback/event/snapshot-stable v1; distinct v2 manifests and archive |
| SUB-50 | Typed read-only source-to-approval audit timeline | 1 | 11 | Provenance application query + generated event contracts + audit web feature | Canonical submitted scope; complete material event sequence; exact actors/roles/orgs/timestamps/version refs/hashes; all eight relations; source→validation→snapshot→both-package claim trails; immutable v1/distinct v2 hashes; zero-mutation auditor denials |
| SUB-53 | Reproducible clean-checkout operator commands | 2, 3 | 11 | Operations adapter over Compose and supported management/browser commands | Prerequisite validation; parameterized isolated ports; start/stop/migrate/seed/safe reset/API/worker/web/health; equal reset fingerprints; headless and paced headed one-command evidence; synthetic-only credential runbook |
| SUB-55 | Canonical E2E certification | 1-4 | 11 | External browser/release certification over web, API, worker, nine capability owners, PostgreSQL, and MinIO | Exact visible user/org/role/permissions/logout for five personas; complete UI lifecycle; direct server denials and zero mutation; deterministic validation/package replay; immutable v1/distinct v2; clean headless plus paced headed JSON/video/trace/screenshots/logs/Compose evidence; immutable AI reviews and final synthetic-POC release decision |
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

## Configurable Document-Intake MVP Trace

| Requirement | ADR pillar/decision | Canonical owner | Boundary evidence | Journey 12 criterion | Release evidence | Delivery issue |
| --- | --- | --- | --- | --- | --- | --- |
| `MVP-REQ-01` Govern immutable document profile versions through `draft -> tested -> approved -> active -> superseded -> retired` | ADR 0001 pillars 2-4; ADR 0003 decisions 1 and 4 | Configuration | `docs/architecture/service-boundaries.md` Configuration row; `docs/architecture/document-intake-mvp-policy.json` lifecycle/invariants | Exact lifecycle, immutable evidence, assigned-human approval, prospective activation, stable history | `scripts/tests/test_mvp_design_evidence.py`; SUB-75/76 manifests; Journey 12 lifecycle evidence | SUB-75, SUB-76 |
| `MVP-REQ-02` Compose profiles from the executable reimbursement ontology rather than a parallel schema or customer branch | ADR 0001 pillar 2; ADR 0003 decision 1 | Shared contracts and Configuration | `docs/architecture/domain-model.md`; `docs/architecture/service-boundaries.md` Configuration boundary | Contract compatibility and exact profile/configuration references | `scripts/tests/test_mvp_design_evidence.py`; SUB-75/76 contract compatibility evidence | SUB-75, SUB-76 |
| `MVP-REQ-03` Derive reproducible noncanonical document clusters without automatic assignment | ADR 0001 pillars 1-3; ADR 0003 decision 2 | Extraction | `docs/architecture/data-flow.md`; `docs/architecture/service-boundaries.md` Extraction row | Identical-input fingerprint equality and zero cluster assignment/activation | `scripts/tests/test_mvp_design_evidence.py`; SUB-76 deterministic fingerprint evidence | SUB-76 |
| `MVP-REQ-04` Support narrow synthetic English and Spanish vendor-invoice profiles | ADR 0003 decisions 1, 3, and 6 | Configuration, Extraction, Test fixtures | `docs/architecture/document-intake-mvp-policy.json`; `docs/architecture/service-boundaries.md` | At least two fixtures per profile with 100% required field/source exactness | `scripts/tests/test_mvp_design_evidence.py`; SUB-76 fixture manifest; `docs/journeys/12-configurable-document-intake-mvp.md` | SUB-76 |
| `MVP-REQ-05` Route changed and unknown layouts safely before canonical invoice use | ADR 0001 pillars 1, 3, and 4; ADR 0003 decision 3 | Extraction and Invoices | `docs/architecture/data-flow.md`; `docs/architecture/service-boundaries.md` closed routing contract | 100% `needs_profile_review`; zero canonical expense/validation mutation | `scripts/tests/test_mvp_design_evidence.py`; SUB-76 zero-mutation integration evidence; Journey 12 | SUB-76 |
| `MVP-REQ-06` Give Configuration Administrators governed history, detail, diff, evaluation, impact, and provenance views | ADR 0003 decisions 1, 5, and 7 | Configuration and Web projection | `docs/architecture/system-map.md`; `docs/architecture/service-boundaries.md` Web row | Normal authenticated UI commands; server scope; visible exact versions and next action | `scripts/tests/test_mvp_design_evidence.py`; SUB-77 frontend/authorization manifest; Journey 12 | SUB-77 |
| `MVP-REQ-07` Give all five personas useful landing pages over one canonical workflow | ADR 0001 pillar 4; ADR 0003 decision 7 | Web projections and owning server capabilities | `docs/architecture/system-map.md`; `docs/architecture/poc-boundary-review.md` | Identity/org/role/context/authority/next action/logout for every persona | `scripts/tests/test_mvp_design_evidence.py`; SUB-78 Playwright artifacts; `docs/journeys/12-configurable-document-intake-mvp.md` | SUB-78 |
| `MVP-REQ-08` Keep configuration, profile, invoice, validation, package, and decision history reproducible after successors | ADR 0001 pillars 1-3; ADR 0003 decision 4 | Configuration, Invoices, Validation, Packages, Provenance | `docs/architecture/domain-model.md`; `docs/architecture/data-flow.md`; `docs/architecture/service-boundaries.md` | Historical profile/config refs, results, package bytes/hashes, and reconstruction remain stable | `scripts/tests/test_mvp_design_evidence.py`; SUB-75/76 manifests; SUB-78 audit/Playwright artifacts | SUB-75, SUB-76, SUB-78 |
| `MVP-REQ-09` Preserve server-side tenant and human authority with zero-mutation denials | ADR 0001 pillar 4; ADR 0003 decisions 5 and 7 | Identity/RBAC and each command owner | `docs/architecture/poc-boundary-review.md`; `docs/architecture/service-boundaries.md` | Direct/indirect cross-scope, wrong-role, stale, and invalid-transition denials mutate nothing | `scripts/tests/test_mvp_design_evidence.py`; SUB-75/77 authorization manifests; SUB-78 direct-denial evidence | SUB-75, SUB-77, SUB-78 |
| `MVP-REQ-10` Use synthetic data and deterministic/local adapters with no hosted model or runtime AI authority | ADR 0001 pillar 3; ADR 0003 decision 6 | Test fixtures, Extraction, AI/config governance | `docs/architecture/document-intake-mvp-policy.json`; `docs/architecture/poc-boundary-review.md` | Positive synthetic catalogs, pinned local OCR, no external key/call, system/AI empty authority | `scripts/tests/test_mvp_design_evidence.py`; SUB-76 fixture/evaluation manifest; SUB-78 retained environment evidence | SUB-76, SUB-78 |

## Deferred And Canceled For POC

- SUB-29: production support access.
- SUB-42: historical/customer model certification.
- SUB-48: payment lifecycle.
- SUB-51: notifications and deadlines.
- SUB-52: business pilot analytics.
- SUB-54: full accessibility/browser certification.

## Coverage Decision

The active story set covers the complete charter and Journey 11. Production requirements remain documented in `solution_requirements.md` but are not POC completion criteria. Accessibility basics remain acceptance criteria within UI stories; AI fixture checks remain within extraction stories.
