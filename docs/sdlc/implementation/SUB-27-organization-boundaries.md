# SUB-27 Implementation Evidence: Organization Boundaries

Status: Approved

## Scope

- Typed actors, five fixed persona roles, resource kinds, actions, and resource scope.
- Server command boundary that authorizes before invoking any mutation.
- NGO ownership, government agency/submission, configuration administration, decision publication, and auditor read-only policies.
- Invoice, configuration, artifact, job, package, government-decision, and audit scope coverage.

## Boundary Decision

SUB-27 defines reusable server policy independent of HTTP/session transport. SUB-28 binds the verified policy to real cookie sessions and FastAPI dependencies. This avoids test-only identity headers while allowing authorization and indirect-reference behavior to be proven before session implementation.

## Verification

- Command: `docker compose run --rm api pytest -q`
- Result: 18 passed.
- Cross-NGO access is denied.
- Government access requires matching agency and submitted state.
- Government decisions remain hidden from NGO users until published.
- Configuration activation is restricted to Configuration Administrator.
- Auditor is read-only.
- Unauthorized indirect-reference commands never invoke the mutation callback.
- NGO Approver and Government Reviewer authority remains separated.

## Review

- Decision: Approved.
- Findings: No blocking or required-fix findings.
- Follow-up: SUB-28 must bind this policy to server-issued sessions and FastAPI dependencies; HTTP authorization coverage belongs to that story.
- Advancement: SUB-27 may move to Done while the ContractView project remains in Build.
