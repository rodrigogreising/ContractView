# ContractView Role-Based POC Demo Charter

Status: Approved exercise scope

Last updated: 2026-07-11

Controlling Linear project: `Substrate / ContractView`

## Goal

Build a technically real, vendor-neutral proof of concept that demonstrates the core reimbursement value proposition end to end with synthetic data. The POC proves that configuration, ingestion, extraction, deterministic validation, human correction, NGO approval, government feedback, NGO resubmission, government approval, immutable packages, and audit reconstruction work together in one runnable system.

The POC is an engineering and product-design exercise. It is not a customer pilot, business validation, competitive deployment, production compliance claim, or representation of any employer's implementation.

## Demo Actors

| Persona | Synthetic organization | Allowed POC actions |
| --- | --- | --- |
| Configuration Administrator | Synthetic Platform Operations | Configure categories, rules, workflow labels, and package settings; activate a version |
| NGO Preparer | Synthetic Community Nonprofit | Upload evidence, review extraction, edit a draft, resolve findings, and revise a return |
| NGO Approver | Synthetic Community Nonprofit | Review, attest, generate a package, and submit an exact invoice version |
| Government Reviewer | Synthetic Public Agency | Review submitted packages, return with structured feedback, and approve a resubmission |
| Auditor | Synthetic Oversight Unit | Read versions, provenance, events, validation results, packages, feedback, and approval |

All names and artifacts are synthetic and non-branded.

## Identity And Authority

- Every persona is a distinct seeded user with a securely hashed password and a real server-issued session.
- The demo login page may provide persona cards that fill seeded credentials, but authentication still uses the normal login endpoint.
- Logout invalidates the session and returns to the login page.
- Every authenticated screen displays the user's name, organization, role badge, and logout action.
- Navigation and buttons reflect the role, while the API independently enforces authorization.
- Playwright must log out and log in between personas. Role switching through browser storage or a test-only endpoint is prohibited.
- User provisioning, role assignment UI, invitations, password recovery, MFA, and SSO are outside POC scope.

## Canonical Demo Flow

1. Reset and seed the synthetic environment.
2. Configuration Administrator logs in and activates configuration version 1.
3. NGO Preparer logs in and uploads a ledger plus receipt/vendor-invoice evidence.
4. Real ingestion and background processing register hashes, import ledger rows, and run one OCR/LLM extraction adapter.
5. NGO Preparer reviews and corrects one extracted value; both model output and correction remain visible in provenance.
6. The system assembles a draft invoice and runs deterministic service-period, required-evidence, budget, reconciliation, and duplicate checks.
7. NGO Preparer fixes a blocker and explains or dismisses a configured warning.
8. NGO Approver logs in, reviews the exact version, attests, generates an immutable package, and submits version 1 to the government queue.
9. Government Reviewer logs in, inspects evidence and validation context, and returns version 1 with structured feedback.
10. NGO Preparer logs in and creates a linked correction without mutating version 1.
11. NGO Approver logs in, re-attests, generates package version 2, and resubmits.
12. Government Reviewer logs in and approves version 2.
13. Auditor logs in and reconstructs the source-to-approval history for both immutable versions.

## Configurability Demonstrated

A small administrator UI supports:

- Budget categories and limits.
- Required-document rules.
- Service-period rule parameters.
- Budget and reconciliation rule parameters.
- Duplicate-warning parameters.
- Workflow and package display labels.

Activation creates an immutable configuration version. Submitted invoices retain the version used. The POC does not include a general-purpose rule builder, customer self-service administration, or AI-authored production configuration.

## Technical Baseline

- React and TypeScript web application.
- Python/FastAPI API and background worker.
- PostgreSQL canonical transactional store.
- MinIO/S3-compatible artifact storage.
- Replaceable real OCR/LLM adapter for one supported receipt/vendor-invoice format.
- Cookie-based server sessions and server-side RBAC.
- Docker Compose startup from a clean checkout.
- Synthetic fixtures only.

## Playwright Definition Of Done

The canonical journey is executed through visible UI interactions. The test:

- Uses real login/logout between all personas.
- Changes and activates configuration through the admin UI.
- Uploads synthetic files through the UI and waits for real background processing.
- Verifies visible identity, organization, and role on every session.
- Verifies forbidden UI actions are absent and direct unauthorized API commands fail without state change.
- Verifies extraction provenance, correction history, deterministic findings, budget totals, and issue resolution.
- Verifies package versions 1 and 2 have distinct hashes and version 1 remains unchanged.
- Verifies return feedback, resubmission, final approval, and audit reconstruction.
- Records video, trace, and screenshots.
- Provides a paced headed mode suitable for recording an interview demo.

POC completion requires the journey to pass from a clean Docker Compose environment without manual database edits or test-only role switching.

## In Scope

- Synthetic configuration and fixtures.
- One government agency, one NGO, and five personas.
- Real authentication sessions and server-side authorization.
- CSV/XLSX ledger import and PDF/image evidence upload.
- One real OCR/LLM extraction path with human correction.
- Draft assembly and field-level provenance.
- Three to five deterministic validation rules.
- NGO attestation and immutable package generation.
- Government return, NGO revision/resubmission, and government approval.
- Audit timeline and package/version inspection.
- Docker Compose and Playwright demo certification.

## Out Of Scope

- Real customer discovery, data-sharing, onboarding, or business validation.
- Real customer documents, names, branding, or confidential workflows.
- Multiple live tenants or production-grade organization administration.
- Invitations, role editor, password reset, MFA, and SSO.
- External procurement-system submission or status integration.
- Payment execution or payment-status lifecycle.
- Notifications, deadline management, support impersonation, legal hold, production retention automation, production SLOs, incident response program, and business-pilot analytics.
- Broad document extraction, handwriting recognition, historical model evaluation, and full accessibility/browser certification.

## Success Criteria

- The canonical Playwright journey passes from a clean seeded environment.
- The generated video tells the complete configuration-to-approval story.
- All core actions use real application paths rather than mocked UI state.
- Deterministic validation is reproducible for fixed inputs and configuration.
- AI remains draft-producing; humans correct values and make authority decisions.
- Submitted package versions are immutable and reconstructable.
- The POC can be explained as a focused architecture demonstration without making customer or production-readiness claims.

## Successor MVP

This charter remains the certified historical POC baseline. The separately
gated [Configurable Document-Intake MVP Charter](document-intake-mvp-charter.md)
defines the successor increment controlled by `SUB-73` and its design gate
`SUB-74`. MVP claims, fixtures, profile behavior, and Journey 12 evidence must
not be inferred from this POC certification.
