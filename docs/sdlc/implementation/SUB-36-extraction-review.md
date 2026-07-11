# SUB-36 Implementation Evidence: Human Extraction Review

Status: Approved

## Scope

- NGO Preparer review UI shows the source artifact, page reference, proposed value, and confidence together.
- Each proposed field supports explicit accept or correction; the canonical path corrects amount 1820.00 to 1280.00.
- Original proposal remains unchanged. The current reviewed projection stores the accepted/corrected value and actor/time.
- An append-only review record, material event, and successor lineage retain decision, proposed/reviewed values, actor, reason, source artifact/location, and predecessor lineage.
- Artifact download independently enforces session, role, and organization scope.

## AI And Validation Boundary

- OCR fields remain unusable as canonical validation inputs until reviewed.
- `reviewed_value()` rejects proposed/unreviewed fields and returns only accepted/corrected values.
- Only NGO Preparer may review; repeated review or an unchanged correction is rejected without new history.

## Verification

- Real OCR proposal corrected 1820.00 -> 1280.00 while both lineage values remain.
- Other configured fields explicitly accepted.
- Actor/time/source/reason and event are present.
- Unreviewed value rejection and reviewed-value consumption are proven.
- Approver/cross-organization attempts fail without mutation.
- React renders evidence, proposal, confidence, accept, and correct controls.
- Focused extraction/review suite: 5 passed.
- React suite: 3 passed; production TypeScript/Vite build passed.
- Authoritative clean full API suite: 55 passed.

## Review

- Implementation decision: Approved.
- AI-governance decision: Approved.
- Findings: No blocking or required-fix findings.
- Advancement: SUB-36 may move to Done; SUB-37 may consume reviewed fields and preserved proposal lineage.
