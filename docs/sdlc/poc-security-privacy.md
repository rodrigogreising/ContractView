# POC Security And Privacy Review

Status: Approved for synthetic-data POC

## Data Decision

Only synthetic, non-branded organizations, users, ledgers, receipts, contract terms, feedback, and packages may enter the POC. Real employee, client, bank, tax, health, customer, employer, or service-recipient data is prohibited.

## Sensitive Flows

- Seeded passwords are development secrets stored as hashes; plaintext demo credentials are documented only for the local synthetic environment.
- Cookie sessions use HTTP-only cookies, same-site protection, expiry, revocation on logout, and secure mode outside localhost.
- Uploads are restricted by configured type and size, hashed, tenant-scoped, and stored in MinIO.
- OCR/LLM requests contain synthetic fixture data only and use the minimum required pages/fields.
- Generated packages remain synthetic but are protected by the same authorization rules as uploads.
- Playwright video/traces may show demo credentials and synthetic data; artifacts are not production evidence.

## Threats And Mitigations

| Threat | Mitigation |
| --- | --- |
| Role escalation | Server-side RBAC and resource checks; forbidden-command tests |
| Session reuse after logout | Server revocation and Playwright assertion |
| Cross-organization reference | Organization scope on queries, commands, jobs, artifacts, and audit views |
| Submitted version mutation | Database invariants plus immutable object hashes |
| Malicious upload | POC type/size validation; clearly defer malware scanning before real data |
| Prompt/document injection | Synthetic constrained document class; treat extraction as untrusted draft |
| Secret leakage | Environment variables, ignored local secrets, redacted logs |
| Test backdoor | Prohibit role-switch endpoints and manual database mutation in certification |

## Accepted POC Risks

- No MFA, password recovery, invitation, or enterprise SSO.
- No malware scanner.
- No automated retention, deletion, legal hold, backup, or disaster recovery.
- No production penetration test or hosted security review.

These risks are acceptable only because the environment is local, synthetic, and non-production. Any real or hosted data use reopens security/privacy review.
