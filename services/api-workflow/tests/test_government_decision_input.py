import pytest

from app.application.commands.government_decision import (
    DecisionError,
    _validated_decision_input,
)


EXACT_LINES = {"EXP-002", "EXP-003", "EXP-004"}


def test_return_input_is_normalized_and_bound_to_exact_invoice_lines() -> None:
    note, lines = _validated_decision_input(
        "returned",
        "EVIDENCE_CORRECTION",
        "  Correct the evidence  ",
        [" EXP-004 "],
        EXACT_LINES,
    )
    assert note == "Correct the evidence"
    assert lines == ["EXP-004"]


@pytest.mark.parametrize(
    ("decision", "reason", "note", "lines", "message"),
    [
        ("returned", "EVIDENCE_CORRECTION", "note", [], "at least one"),
        (
            "returned",
            "EVIDENCE_CORRECTION",
            "note",
            ["EXP-004", "EXP-004"],
            "unique",
        ),
        (
            "returned",
            "EVIDENCE_CORRECTION",
            "note",
            ["EXP-999"],
            "exact submitted invoice",
        ),
        (
            "returned",
            "APPROVED_AS_CORRECTED",
            "note",
            ["EXP-004"],
            "return reason",
        ),
        (
            "approved",
            "EVIDENCE_CORRECTION",
            "note",
            [],
            "approval reason",
        ),
        (
            "approved",
            "APPROVED_AS_CORRECTED",
            "note",
            ["EXP-004"],
            "cannot introduce",
        ),
        ("returned", "EVIDENCE_CORRECTION", "   ", ["EXP-004"], "note"),
    ],
)
def test_invalid_decision_evidence_fails_closed(
    decision: str,
    reason: str,
    note: str,
    lines: list[str],
    message: str,
) -> None:
    with pytest.raises(DecisionError, match=message):
        _validated_decision_input(decision, reason, note, lines, EXACT_LINES)
