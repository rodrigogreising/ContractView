from app.configuration import (
    active_summary,
    activate_version,
    approve_version,
    test_draft,
)


def ensure_active_configuration(actor, contract_id: str) -> dict:
    active = active_summary(actor, contract_id)
    if active:
        return active
    tested = test_draft(actor, contract_id, "Synthetic test setup evidence")
    approve_version(actor, tested["id"], "Synthetic authorized test approval")
    return activate_version(actor, tested["id"], "Synthetic initial activation")
