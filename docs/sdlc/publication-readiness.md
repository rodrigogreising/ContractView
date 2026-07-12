# Public Repository Candidate Readiness

Status: Candidate generation and executable certification required; public
visibility remains an owner decision.

## Publication Boundary

The public artifact is a standalone synthetic reimbursement-workflow proof of
concept created from an explicit allowlist. It is not a visibility change to
the private engineering repository. The candidate contains no inherited Git
history, private pull-request discussion, internal implementation evidence,
control-plane URLs, personal commit metadata, caches, local artifacts, or test
output from the private repository.

## Identity And Data Contract

- Every organization and persona uses an explicit `Synthetic` display name.
- Every email uses the reserved `example.test` domain.
- Vendors belong to a closed synthetic catalog in `scenario.json`.
- Payroll rows contain synthetic employee references rather than names.
- PDFs, PNGs, workbooks, ledgers, and package labels are generated from the
  same machine-readable scenario.
- PDF and workbook authorship metadata identifies only the synthetic fixture
  generator. PNG fixtures contain no textual metadata.
- No real customer, employer, organization, vendor, person, account,
  authentication secret, payment, or transaction is represented.

## Candidate Identity And Rights

- Descriptive title: `Synthetic Reimbursement Workflow POC`.
- Proposed repository slug: `synthetic-reimbursement-workflow-poc`.
- Rights policy: all rights reserved; public visibility grants no reuse license.
- Vulnerabilities are reported privately through GitHub Security Advisories.
- Selecting an open-source license is a separate future owner decision.

## Required Machine Evidence

`PUBLICATION-MANIFEST.json` must record the private source SHA without author
metadata, every included/excluded path, SHA-256 for every exported source file,
structural scan decisions, exact certification commands, environment versions,
test counts, and retained log hashes. The candidate must contain no `.git`
directory and must pass from its own directory using isolated PostgreSQL and
MinIO volumes with no published host ports.

## Decision

Candidate certification may be AI-reviewed. Creating a repository or changing
visibility requires explicit owner approval after inspecting the generated
candidate. Until then the decision is `Blocked for publication`, not because of
a code-review ceremony, but because public disclosure is an irreversible owner
authority decision.
