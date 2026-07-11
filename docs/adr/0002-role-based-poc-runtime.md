# ADR 0002: Role-Based POC Runtime

## Status

Accepted

## Date

2026-07-11

## Context

ContractView needs a technically real, interview-ready POC rather than a production pilot. It must demonstrate configuration, ingestion, one real AI-assisted extraction path, deterministic validation, role-separated NGO and government decisions, immutable package revisions, and audit reconstruction through a recorded Playwright journey.

## Decision

Build the POC as a modular monolith with separately runnable web, API, worker, PostgreSQL, and MinIO processes under Docker Compose.

- React/TypeScript owns role-specific presentation and Playwright-visible behavior.
- FastAPI owns sessions, authorization, workflow commands, canonical invoice state, configuration lifecycle, validation coordination, package commands, and audit queries.
- A Python worker owns asynchronous import and OCR/LLM extraction jobs.
- PostgreSQL owns canonical transactional state, sessions, job records, append-only domain events, and field lineage.
- MinIO owns immutable original and generated artifact bytes; PostgreSQL stores hashes and references.
- Shared packages define domain, configuration, event, and rule contracts without becoming hidden services.

The POC keeps logical boundaries from ADR 0001 while avoiding deployable microservices. Modules may later split behind the same contracts.

## Authentication And Authority

- Seed five synthetic persona accounts with securely hashed passwords.
- Authenticate through the normal login endpoint and issue server-side cookie sessions.
- Logout revokes the server session.
- Every command authorizes persona, organization, resource scope, invoice state, and target version server-side.
- UI visibility improves usability but never substitutes for API enforcement.
- No role editor or user provisioning surface is built.

## Configuration

- Administrator edits a constrained reimbursement configuration through the UI.
- Activation creates an immutable version covering categories, limits, rule parameters, workflow/package labels, and output settings.
- Draft invoices use the active version at creation/revalidation; submitted versions retain their referenced configuration.

## AI Boundary

- One replaceable OCR/LLM adapter extracts draft fields from one supported synthetic receipt/vendor-invoice format.
- Each output records provider/model, prompt/parser version, source location, and confidence.
- Low-confidence or intentionally incorrect fixture output requires NGO human review.
- AI never creates deterministic findings, attestations, submissions, returns, approvals, or finalization.

## Deterministic And Immutable Behavior

- Service-period, required-evidence, budget, reconciliation, and duplicate rules execute deterministically against explicit versions.
- Package generation produces real PDF/JSON/ZIP artifacts and hashes.
- Submission locks the invoice/package version.
- Government return creates a linked draft revision; resubmission creates a new package hash without changing version 1.

## Consequences

### Positive

- The demo exercises real technology and authority boundaries without production-scale complexity.
- Docker Compose and synthetic fixtures make the result reproducible.
- Logical modules preserve an extraction path toward production architecture.

### Negative

- Single-database modules are less isolated than separate production services.
- Seeded authentication does not prove enterprise identity lifecycle.
- One document class does not prove broad extraction generality.

## Deferred

Multi-tenant production operations, identity administration, MFA/SSO, customer data, external procurement integration, payment, notifications, support access, retention automation, production SLOs, broad extraction, and hosted deployment.
