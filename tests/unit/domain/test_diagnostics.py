import copy

import pytest

from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCategory,
    DiagnosticCode,
    ProblemRejectedError,
    SourceExcerpt,
)

UNSUPPORTED = Diagnostic(DiagnosticCode.UNSUPPORTED_HYPOTHESIS, "/hypotheses/walls", "m", "e")
INVALID = Diagnostic(DiagnosticCode.NON_POSITIVE_QUANTITY, "/parameters/mass/value", "m", "e")
AMBIGUOUS = Diagnostic(
    DiagnosticCode.AMBIGUOUS_DIVISION, "/statement", "m", "e", SourceExcerpt("1/2x", 0, 4)
)
OVER_BUDGET = Diagnostic(DiagnosticCode.EXPRESSION_TOO_DEEP, "/statement", "m", "e")
OVER_PROFILE = Diagnostic(DiagnosticCode.RESOURCE_LIMIT_EXCEEDED, "/numerics/steps", "m", "e")
NOT_CONVERGED = Diagnostic(DiagnosticCode.METHOD_NOT_CONVERGED, "", "m", "e")
NON_FINITE = Diagnostic(DiagnosticCode.NON_FINITE_RESULT, "", "m", "e")
NON_HERMITIAN = Diagnostic(DiagnosticCode.NON_HERMITIAN_OPERATOR, "/observable/matrix", "m", "e")


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


def test_a_statement_with_two_readings_is_an_ambiguous_input() -> None:
    assert AMBIGUOUS.category is DiagnosticCategory.AMBIGUOUS_INPUT


def test_a_statement_over_a_complexity_limit_exceeds_the_budget() -> None:
    assert OVER_BUDGET.category is DiagnosticCategory.BUDGET_EXCEEDED


def test_a_request_above_the_homologated_profile_exceeds_the_budget() -> None:
    assert OVER_PROFILE.category is DiagnosticCategory.BUDGET_EXCEEDED


@pytest.mark.parametrize("diagnostic", [NOT_CONVERGED, NON_FINITE])
def test_a_method_that_fails_to_deliver_a_finite_answer_is_non_convergent(
    diagnostic: Diagnostic,
) -> None:
    assert diagnostic.category is DiagnosticCategory.NON_CONVERGENT


def test_an_operator_that_is_not_hermitian_is_an_invalid_input() -> None:
    assert NON_HERMITIAN.category is DiagnosticCategory.INVALID_INPUT


@pytest.mark.parametrize(
    ("diagnostics", "category"),
    [
        ((UNSUPPORTED, AMBIGUOUS), DiagnosticCategory.AMBIGUOUS_INPUT),
        ((AMBIGUOUS, OVER_BUDGET), DiagnosticCategory.BUDGET_EXCEEDED),
        ((OVER_BUDGET, INVALID, AMBIGUOUS), DiagnosticCategory.INVALID_INPUT),
        ((NOT_CONVERGED, UNSUPPORTED), DiagnosticCategory.UNSUPPORTED_PROBLEM),
        ((NOT_CONVERGED,), DiagnosticCategory.NON_CONVERGENT),
    ],
)
def test_rejection_reports_the_category_the_user_must_act_on_first(
    diagnostics: tuple[Diagnostic, ...], category: DiagnosticCategory
) -> None:
    assert ProblemRejectedError(diagnostics).category is category


def test_rejection_rebuilt_from_its_reduced_form_keeps_its_diagnostics() -> None:
    restored = copy.deepcopy(ProblemRejectedError((AMBIGUOUS, INVALID)))

    assert restored.diagnostics == (AMBIGUOUS, INVALID)
