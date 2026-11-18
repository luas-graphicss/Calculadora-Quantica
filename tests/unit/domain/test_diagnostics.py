from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCategory,
    DiagnosticCode,
    ProblemRejectedError,
)

UNSUPPORTED = Diagnostic(DiagnosticCode.UNSUPPORTED_HYPOTHESIS, "/hypotheses/walls", "m", "e")
INVALID = Diagnostic(DiagnosticCode.NON_POSITIVE_QUANTITY, "/parameters/mass/value", "m", "e")


def test_a_hypothesis_outside_the_card_is_an_unsupported_problem() -> None:
    assert UNSUPPORTED.category is DiagnosticCategory.UNSUPPORTED_PROBLEM


def test_a_non_positive_quantity_is_an_invalid_input() -> None:
    assert INVALID.category is DiagnosticCategory.INVALID_INPUT


def test_rejection_with_any_invalid_input_is_reported_as_invalid_input() -> None:
    rejection = ProblemRejectedError((UNSUPPORTED, INVALID))

    assert rejection.category is DiagnosticCategory.INVALID_INPUT


def test_rejection_with_only_unsupported_diagnostics_is_an_unsupported_problem() -> None:
    assert ProblemRejectedError((UNSUPPORTED,)).category is DiagnosticCategory.UNSUPPORTED_PROBLEM


def test_rejection_message_names_each_field() -> None:
    assert "/parameters/mass/value" in str(ProblemRejectedError((INVALID,)))
