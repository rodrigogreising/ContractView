# SUB-25 Implementation Evidence: Synthetic Fixture Pack

Status: Implemented and verified

## Scope

- Four synthetic organizations and five distinct persona accounts.
- One synthetic agency/NGO contract, three budget categories, and one inactive draft configuration.
- CSV and professionally formatted XLSX ledger with five expenses and a $10,130.00 control total.
- Synthetic payroll XLSX with formula-driven $4,200.00 claimed total.
- Four synthetic vendor-invoice PDFs and one PNG rendering.
- Machine-readable expected blocker, warning, extraction correction, government return, version-2 correction, final state, and immutable-package expectations.
- SHA-256 manifest for every source artifact.

## Intentional Journey Conditions

- EXP-003 presents a printed subtotal of $1,820.00 and an approved claim total of $1,280.00, providing the human extraction-correction path.
- EXP-004 is dated 2026-07-03, outside the configured June service period, and must trigger `SERVICE_PERIOD` until corrected to 2026-06-30 in version 2.
- EXP-005 is a separate $1,850.00 Synthetic Facilities Vendor A charge one day after EXP-002 and must trigger `POSSIBLE_DUPLICATE`; its distinct invoice number supports warning resolution.
- Government return code and comment are synthetic and explicitly tied to the service-date correction.

## Seed Boundary

The deterministic seed loads only organizations, persona identities with Argon2 password hashes, contract, budget categories, and a draft configuration. It does not create invoices, jobs, extraction results, validation runs, submissions, returns, revisions, packages, or approvals.

## Verification

- Spreadsheet values/formulas inspected; ledger formula total is $10,130.00 and payroll formula total is $4,200.00.
- Ledger and payroll render previews visually inspected for clipping, formatting, and legibility.
- All four PDF pages rendered to PNG and visually inspected; explicit white page backgrounds prevent transparency defects.
- PDF text extraction confirms invoice numbers, dates, amounts, adjustment, notes, and synthetic-data notice.
- PNG pixel checks confirm white page backgrounds.
- Fixture SHA-256 manifest matches current bytes.
- Containerized Pytest: 5 passed, covering scenario completeness, totals, category totals, hashes, and forbidden branding/data terms.
- Clean reset seeded counts: 4 organizations, 5 users, 1 contract, 3 budget categories, 1 draft configuration.
- Running seed twice preserved those counts.
- All five stored password values begin with the Argon2id hash prefix; plaintext passwords are not stored in PostgreSQL.

## Review

Decision: Approved.

The fixture pack is complete, synthetic, non-branded, deterministic at the entity/expectation level, and contains all conditions required by Journey 11 without seeding later workflow outcomes.
