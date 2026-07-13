# ContractView Configurable Document-Intake MVP Charter

Status: Design Review

Controlling Linear scope: `Substrate / ContractView / SUB-73`

Design gate: `SUB-74`

Machine-readable design: `docs/architecture/document-intake-mvp-policy.json`

## Relationship To The Certified POC

The role-based synthetic POC remains a certified historical baseline. This MVP
is a new, separately gated product increment. It keeps the POC's canonical
invoice, server authorization, immutable evidence, deterministic validation,
and human-authority guarantees while making configuration-first document
intake understandable and repeatable.

The MVP does not reinterpret prior POC evidence as proof of broad document
support, production readiness, customer validation, or multilingual product
coverage.

## Problem

The POC can execute one configured reimbursement journey, but it does not yet
give a Configuration Administrator a product-quality way to understand version
history, evaluate document layouts, govern reusable document profiles, or see
the prospective impact of activation. Other personas can complete the workflow
but lack landing pages that explain their next action, authority, and exact
configuration/profile context.

Without explicit profile versions and safe unknown-layout behavior, expanding
document intake would risk hidden customer-specific code, configuration drift,
untraceable extraction behavior, and accidental promotion of unsupported data
into canonical invoice state.

## Product Outcome

A Configuration Administrator can create, test, approve, activate, compare,
supersede, retire, and audit immutable reimbursement configuration and document
profile versions. The system can deterministically recognize two supported
synthetic vendor-invoice profiles—one English and one Spanish—while changed or
unknown layouts route to review without creating a canonical expense.

Each persona receives a role landing page over the same canonical workflow:

| Persona | Landing-page intent | Authority retained |
| --- | --- | --- |
| Configuration Administrator | Explain active configuration/profile versions, pending cluster suggestions, evaluation results, impact, and the next governance action. | Human-only profile/configuration test, approval, and prospective activation for assigned contracts. |
| NGO Preparer | Show evidence-processing status, recognized profile/version, review exceptions, open findings, and the next preparation action. | Review/correct draft fields and prepare revisions; cannot activate, attest, submit, return, or approve. |
| NGO Approver | Show the exact invoice, configuration/profile versions, validation freshness, package readiness, and outstanding blockers. | Human-only attestation and submission of an exact version. |
| Government Reviewer | Show submitted package, configuration/profile context, deterministic findings, and review queue status. | Human-only return or approval of a submitted version. |
| Auditor | Show immutable profile/configuration history and source-to-approval reconstruction. | Read-only reconstruction; no mutation authority. |

UI visibility remains explanatory. Server-side policy, canonical assignments,
resource scope, lifecycle state, and exact version remain authoritative.

## Document Profile Contract

A `DocumentProfileVersion` is not a second ontology. It is a Configuration-
owned composition of existing `Artifact`, `Schema`, typed `Field`, `Mapping`,
`Rule`, `Workflow`, `View`, `ConfigurationBundle`, and `Event` contracts.

An immutable profile version records:

- profile id and semantic version;
- artifact class and BCP 47 language tag;
- synthetic vendor aliases;
- required typed fields and source-location requirements;
- deterministic normalization and ledger-match rules;
- deterministic fingerprint specification;
- fixture-set version and evaluation-evidence hash; and
- predecessor/successor plus exact activated configuration-bundle references.

The lifecycle is:

`draft -> tested -> approved -> active -> superseded -> retired`

Testing freezes the candidate and creates immutable evaluation evidence. A
canonically assigned human Configuration Administrator approves it. Activation
occurs only through a prospectively activated configuration bundle that names
the exact profile id and version. Rollback prepares a new tested successor; it
does not reactivate or mutate history.

## Deterministic Cluster And Routing Behavior

Extraction owns a read-only cluster projection derived from canonicalized media
type, language tag, normalized OCR tokens, page geometry, and anchor positions.
The projection uses `sha256-canonical-json-v1` and is reproducible for identical
artifact bytes, OCR/parser version, and fingerprint specification.

A cluster is a suggestion, not configuration. It cannot assign, approve, or
activate a profile. Administrator confirmation creates a Configuration-owned
draft association that still traverses test, approval, and bundle activation.

The only supported runtime outcomes are:

- `recognized_profile_draft`: exact active profile matched; extracted fields
  remain draft until human review; or
- `needs_profile_review`: no exact active profile or a changed layout; retain
  artifact/OCR/fingerprint evidence and create no canonical expense.

## Supported Synthetic Scope And Evaluation

The MVP fixture pack uses closed synthetic catalogs and deterministic generators,
not a blacklist of names or sensitive terms. The minimum evaluation set contains:

- two printed English vendor invoices for one supported profile;
- two printed Spanish vendor invoices for one supported profile;
- one changed-layout variant of a supported profile;
- one unknown-layout vendor invoice; and
- one historical-replay case after a profile/configuration successor activates.

Acceptance metrics:

| Measure | Required result |
| --- | --- |
| Required normalized fields and source locations for supported fixtures | 100% exact against the versioned expected record |
| Identical artifact/profile/OCR/parser/configuration input | Identical fingerprint, normalized draft, or explicit deterministic failure |
| Changed and unknown layouts | 100% `needs_profile_review`; zero canonical expense mutation |
| Cluster suggestion without administrator confirmation | Zero profile assignments and zero activation events |
| Successor activation | Prior submitted invoice keeps its original configuration/profile ids, results, package bytes, and audit reconstruction |

The UI is English. English and Spanish describe source-document profiles, not
user-interface localization.

## Automation And AI Boundary

The MVP permits pinned local OCR as a replaceable adapter and records the exact
OCR/parser versions. It uses no hosted model, runtime LLM, external model key,
or AI-assisted profile drafting. Profile matching, normalization, ledger
matching, validation, workflow, and package behavior are deterministic.

The existing POC extraction record remains historical evidence; it does not
authorize runtime AI in the MVP. System and AI actors have no configuration or
human-workflow authority.

## In Scope

- Governed configuration history, detail, diff, test evidence, impact, and
  provenance.
- Immutable English/Spanish vendor-invoice profile versions.
- Deterministic cluster suggestions requiring administrator confirmation.
- Safe changed/unknown-layout review routing.
- Exact profile/configuration references on extraction, invoice, validation,
  package, submission, and audit evidence.
- Dedicated Configuration Administrator workspace and lightweight landing
  pages for the other four personas.
- Synthetic fixtures, executable evaluation, and a final recorded journey.

## Out Of Scope

- Real, pilot, customer, employee, service-recipient, payroll, bank, tax, or
  health data.
- Customer, employer, public-agency, nonprofit, or vendor branding.
- Hosted model calls, runtime LLM extraction, AI-assisted profile drafting, or
  automatic profile assignment.
- Broad document classes, handwriting, multilingual UI, translation workflow,
  customer self-service rule building, or unbounded schema editing.
- Production deployment, external submission, payment execution,
  notifications, identity administration, SSO/MFA, malware scanning,
  production retention/recovery, or business-outcome claims.

## Delivery And Completion

1. `SUB-74` accepts this product, ADR, boundary, security, governance,
   traceability, and journey design.
2. `SUB-75` exposes governed configuration lifecycle and provenance contracts.
3. `SUB-76` implements immutable profiles, deterministic clustering/routing,
   and fixture evaluation.
4. `SUB-77` implements the Configuration Administrator workspace.
5. `SUB-78` implements role landing pages and certifies Journey 12.

The MVP is complete only when all five leaves are merged and post-merge
verified and Journey 12 proves supported English/Spanish profiles, safe unknown
routing, prospective successor activation, stable historical reconstruction,
server authority, and retained machine/browser evidence.
