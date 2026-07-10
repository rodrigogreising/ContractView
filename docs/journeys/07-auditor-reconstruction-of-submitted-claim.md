# Journey 07: Auditor Reconstruction Of Submitted Claim

## Purpose

Prove that an auditor can reconstruct a submitted claim without mutation rights.

## Actors

- Auditor/comptroller/read-only oversight role.
- System actor: provenance/event service.
- System actor: reporting layer.

## Preconditions

- At least one invoice has completed submission and agency review.
- Auditor has read-only access scoped to the relevant organization, contract, or invoice.
- Required events, lineage, artifacts, and validation runs are retained.

## Workflow Path

1. Auditor searches by agency, nonprofit, contract, invoice, user, rule, date, or amount.
2. Auditor opens a submitted claim.
3. Auditor traces a claimed amount back to source artifact and source location.
4. Auditor inspects validation results, corrections, waivers, submission package, review decisions, and payment status.
5. Auditor exports or records audit evidence where allowed.

## Expected Provenance Evidence

- Source and generated artifact hashes.
- Field lineage from claimed amount to source location.
- Validation run and configuration bundle versions.
- Correction, waiver, attestation, return, approval, and payment-status events.
- Read-only audit access event where required by policy.

## Failure Modes

- Auditor cannot mutate invoice, artifacts, issues, rules, or approvals.
- Missing retained artifact shows tombstone/hash/redacted lineage according to retention policy.
- Queryable projection cannot contradict event/provenance records.

## Certification Criteria

- Auditor can answer the ADR traceability question for a claimed amount.
- Auditor access is inspectable and non-mutating.
- Historical validation result is reproducible from recorded versions.
- Chain of custody is reviewable from upload to submission to approval.
