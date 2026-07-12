# SUB-49 Government Return And Final Approval Evidence

## Control

- Issue: SUB-49 / AGY-02
- Branch: `codex/sub-49-government-decisions`
- Base SHA: `d8f99ebd27a5d3d99a6d1ad59477e94acd142ce3`
- Project stage: Build
- Parent: SUB-22
- Architecture decision: no new ADR; this closes evidence validation inside
  ADR 0002's existing Workflow, Invoices, Provenance, and HTTP boundaries
- Human code review: not required

## Exact Decision Contract

Only the provisioned Government Reviewer may use the normal server command to:

1. return an exact submitted invoice/package version with one of
   `EVIDENCE_CORRECTION`, `AMOUNT_CORRECTION`, or `CLARIFICATION`, a nonblank
   note, and at least one unique affected expense key belonging to that exact
   invoice version; or
2. approve a corrected later submitted version with
   `APPROVED_AS_CORRECTED`, a nonblank note, and no newly introduced affected
   line keys.

The Workflow application command consumes exact invoice-line keys through an
Invoices-owned application query port. It does not query the Invoices table
through arbitrary cross-capability SQL. The decision transaction locks the
queue item, validates all evidence before mutation, appends the decision and
event/relation evidence, updates queue/invoice state through owner ports, and
commits atomically.

Unsupported decisions, mismatched reason classes, blank notes, blank/duplicate/
foreign affected lines, unauthorized actors, fabricated system/AI identities,
already-decided queue items, v1 approval, duplicate return, and approval without
a prior return all fail before durable mutation.

## Provenance And Authority

- The decision row binds queue, submission, exact invoice, exact package,
  decision, structured reason, normalized note, affected lines, canonical actor,
  role, and database decision time.
- Returned and approved events bind full invoice/submission/package/decision
  version references.
- `actorOrganizationId` remains the Government organization while
  `organizationId` remains the NGO resource owner. Actor context is not used as
  resource tenancy.
- Return creates the linked draft successor and typed `returned_as`/`amends`
  relations without mutating v1.
- Approval adds `approved_as` evidence for v2. System and AI actors have no
  authority path.

## Executable Evidence

- Pure decision-evidence validation: 8 tests covering normalization plus empty,
  duplicate, foreign-line, wrong-reason, approval-line, and blank-note denial.
- Integrated v1→v2 test proves four invalid return attempts preserve decision,
  revision-link, queue, and invoice-state fingerprints.
- The authorized path proves exact v1 decision fields, canonical actor/resource
  organizations, full version references, linked v2 correction/resubmission,
  distinct package reproduction hashes, final v2 approval, unchanged v1
  snapshots, and all eight provenance relation types.
- Static/policy gate: 4 registries / 27 contracts; 47 owners / 175 named
  statements; 6 layers / 9 capability owners; 71 repository tests; 19 frontend
  tests; production build and web boundaries passed.
- Clean runtime pass 1: 188 API tests passed.
- Clean runtime pass 2: 188 API tests passed.
- Equal reset fingerprint:
  `7a4690eb63c89aba73fdee2a93f1a4e18737468e965a56ee9dedfb8691d590fb`.
- Retained API-log hashes:
  `27a9bf44e25e6d464fe58abeaea1a89c41790b41a2ca51dee98958edbb614dfb`
  and `f8cdb7cb966e023ddb227d236efc1c16cade637372f39239c508fda75194ac6b`.
- Retained Compose-state hashes:
  `fb74b943bc4d22e8f73da2365b3c184e9d2e48924c131dabb53ca4cdfdeb2f4f`
  and `8ec3bd81b5355af42d610d058433bcd926f234144acb17444fba6a5ee9322006`.

## Dependency Impact

SUB-49 may be Done only after immutable AI review, merge, and clean post-merge
verification. Its merge unblocks SUB-46; SUB-50 still requires both SUB-49 and
the merged SUB-46 correction/resubmission evidence. Journey 11 and SUB-55
remain incomplete.
