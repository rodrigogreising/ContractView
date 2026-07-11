# SUB-28 Implementation Evidence: Authentication And RBAC

Status: Approved

## Scope

- Five seeded persona accounts with Argon2 password hashes.
- Normal credential login with opaque, hashed, database-backed session tokens.
- HttpOnly, SameSite cookie transport; authenticated identity endpoint; server revocation on logout.
- Authentication event records for successful login, failed login, and logout.
- React persona cards that fill credentials but still submit the normal login request.
- Visible authenticated display name, organization, role badge, and logout action.
- FastAPI dependency resolves actors exclusively from the server session and binds protected commands to the SUB-27 policy.

## Deliberate POC Limits

- Seeded accounts only.
- Local HTTP delivery uses a non-Secure cookie; hosted HTTPS is deferred and would require `Secure`.
- No invitations, role editor, password recovery, MFA, SSO, or test-only role switching.

## Verification

- Containerized API unit/integration suite covers opaque token storage, valid/invalid credentials, resolution, immediate logout revocation, fabricated-token rejection, role/resource policies, and no-mutation denials.
- Containerized React test verifies all five persona choices and the normal password form.
- Production frontend build type-checks and bundles successfully.
- Result: API suite 22 passed; React suite 1 passed; production web build passed.
- Live HTTP result: login 200, authenticated identity 200, forbidden NGO configuration activation 403, logout 204, revoked-session reuse 401.

## Review

- Decision: Approved.
- Findings: No blocking or required-fix findings for the Docker Compose POC.
- Follow-up: Secure cookies remain a required hosted-HTTPS hardening item, but hosted delivery is explicitly out of scope.
- Advancement: SUB-28 may move to Done while the project remains in Build.
