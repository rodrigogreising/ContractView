# SUB-79 Public Repository Candidate Evidence

Status: Build

## Control

- Issue: `SUB-79`
- Branch: `codex/sub-79-publication-candidate`
- Base SHA: `45964570a986f7f87b772ba73d46b17c233c915e`
- Project: ContractView / Build / At Risk
- Blocks: SUB-67 and its preserved PR #10
- Human code review: not required
- Human authority: explicit owner approval is required before public repository
  creation or visibility change

## Implementation Contract

The private repository remains the durable SDLC and audit store. A deterministic
builder exports a neutral standalone candidate from tracked and in-scope new
files, removes internal implementation evidence and product-research material,
rewrites the private product identifier to a descriptive public identity, and
scans text plus PDF/XLSX/PNG content and metadata. The candidate contains no
Git directory or inherited commit author data.

Fixtures are regenerated from `scenario.json`. Positive tests enforce closed
synthetic organization, persona, vendor, employee-reference, and reserved-domain
catalogs. They do not embed a third-party brand as a negative assertion.

## Required Evidence

- Byte-identical fixture regeneration across consecutive runs.
- Exact fixture hash manifest covering CSV, XLSX, PDF, and PNG bytes.
- Structural candidate scan for legacy/private fragments, high-confidence
  secret shapes, reserved email domains, binary content/metadata, excluded
  history, and excluded control-plane evidence.
- Source and candidate frontend tests/build.
- Source and candidate full API regression including real Tesseract extraction.
- Candidate-only clean Compose startup/reset with isolated PostgreSQL and MinIO.
- `artifacts/publication-candidate/PUBLICATION-MANIFEST.json` containing exact
  paths, hashes, commands, counts, environment, and retained log hashes.

## Review And Handoff

Security/privacy, implementation/tests, requirements traceability, and release
readiness AI reviews inspect the immutable PR diff. Publication remains blocked
after merge until the owner inspects the generated candidate and explicitly
authorizes creation of a new public repository from one clean baseline commit.
