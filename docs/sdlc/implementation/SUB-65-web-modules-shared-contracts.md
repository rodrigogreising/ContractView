# SUB-65 Web Modules And Shared Contract Evidence

Status: Build

## Control

- Issue: `SUB-65` / REC-10
- Branch: `codex/sub-65-web-modules-shared-contracts`
- Base SHA: `7504ad34d7055d0977ddb5705ca1add43576a62c`
- Project: ContractView / Build
- Merged prerequisites: SUB-58 `08ae4ffef3f2ef386473149b596b6a5abbc147d8`;
  SUB-61 `1cc5d9a78060a0c40bb67cb8770d0c7de2f53639`; SUB-62
  `be38a4a176dcca129bf053eebdc12dfc6d51be67`; SUB-63
  `a15d93637c0f998de5dc07374f6a6c975586f876`; SUB-68
  `7504ad34d7055d0977ddb5705ca1add43576a62c`
- Human code review: not required. Executable evidence plus immutable-diff AI
  reviews are the code gate.

## Implemented Boundary

The prior 1,875-line `App.tsx` owned transport, local DTOs, seeded credentials,
fixed contract context, orchestration, all feature rendering, and role routing.
The application shell is now 181 lines. `src/api` owns response/error handling;
capability folders own typed API facades and rendering; and `src/workspaces`
owns Configuration Administrator, NGO Preparer, NGO Approver, Government
Reviewer, and Auditor composition. No feature or workspace calls `fetch`.

`ContractContextDto` is an executable shared contract generated for Python and
TypeScript. `/auth/contracts` returns only contexts derived from canonical NGO/
agency ownership or explicit administrator/auditor assignment. The app no
longer contains a contract literal. Demo credentials live behind
`VITE_CONTRACTVIEW_DEMO_MODE`; the default production build tree-shakes them
and a bundle scan proves they are absent.

## Executable Evidence

- Static gate: 105 typed Python/script sources, 4 registries / 27 contracts, 47 table
  owners / 174 statements, 63 policy tests, 19 frontend tests, and production
  build pass.
- Two independent fresh-volume Compose passes each run 180 API tests and yield
  fingerprint `7a4690eb63c89aba73fdee2a93f1a4e18737468e965a56ee9dedfb8691d590fb`.
- Canonical context tests cover all five personas, multi-contract agency scope,
  explicit assignment scope, outsider denial, normal cookie session, and
  logout rejection.
- Frontend tests cover feature rendering, presentational role visibility,
  normalized API errors, accessible labels/live status, generated DTOs, demo
  boundary, contract-switch projection/epoch isolation, and absence of
  transport/fixed-contract/credential logic in App.
- Default production `dist` contains no seeded password/email or synthetic
  contract identifier; explicit Compose demo builds retain the paced persona
  cards needed by Journey 11.

## Review And Completion

Run ADR/architecture, boundary, security/privacy, requirements traceability,
implementation/tests, Journey 11, and release-readiness reviews against the
immutable PR base/head. Done requires hosted certification, retained reviewed
manifest, merge SHA, and clean post-merge verification. SUB-66 remains blocked
until this evidence is merged and verified.
