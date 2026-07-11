# SUB-43 Implementation Evidence: Exact-Version NGO Attestation

Status: Approved

## Scope

- NGO Approver preview includes exact invoice/material revision, totals, configuration version, current findings, validation run/hash/freshness, and planned package contents/evidence count.
- Attestation requires the exact versioned text, a validation run matching the current material revision, and no open blocker.
- Append-only record stores actor, role, text/version, timestamp, invoice, validation run, material revision, and SHA-256 fingerprint over invoice lines, artifact hashes, configuration, and validation hashes.
- Current/stale status is computed server-side; a material revision change invalidates the prior attestation automatically.

## Authority

- Only NGO Approver may attest (`Action.ATTEST`).
- NGO Preparer may prepare/correct but cannot attest.
- Attestation does not submit; package and submission remain separate authority-checked commands.

## Verification

- Focused API suite: `7 passed` (`tests/test_validation.py`).
- Frontend component suite: `8 passed`; production TypeScript/Vite build passed.
- Eligible preview exposes all exact-version context and package preview.
- Open blockers and stale validation reject attestation.
- Preparer attempt creates no record.
- Actor/role/text/version/time/fingerprint/event are present.
- Material revision change makes the prior record stale; fresh validation is required before re-attestation.

## Review Decision

Approved. The implementation preserves separation of duties, binds the human attestation to immutable inputs, and does not grant submission authority or mutate prior evidence.
