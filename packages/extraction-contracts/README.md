# Extraction Contracts

Executable shared contracts for deterministic document fingerprints, profile
matches, safe routing, cluster projections, source-located draft fields, and
ledger reconciliation. Configuration definitions and lifecycle remain owned by
`configuration-contracts`; these contracts describe Extraction-owned runtime
evidence and never grant assignment or activation authority.

The package depends only on `domain-types` and `configuration-contracts` and is
generated into the API and web consumers by
`scripts/generate_shared_contracts.py`.
