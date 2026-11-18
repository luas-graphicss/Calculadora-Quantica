import pytest

from quantum_calculator.algebra.identity import IdentityTester
from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.domain.diagnostics import DiagnosticCategory, DiagnosticCode
from quantum_calculator.domain.verification import EvidenceKind, VerificationStatus
from quantum_calculator.solvers.symbolic.candidate import CandidateClaim
from quantum_calculator.verification.ode_substitution import OdeSubstitutionVerifier
from support.statements import DECAY, DECAY_CONDITION, DECAY_EQUATION, DECAY_SOLUTION
from support.symbolic import SymbolicBench, SymbolicResult

NOT_ZERO = "\N{NOT EQUAL TO} 0"
WRONG_INITIAL_VALUE = "y(t) = 2*y_0*exp(-k*t)"
WRONG_SIGN = "y(t) = y_0*exp(k*t)"
HIDDEN_IDENTITY = "y(t) = y_0*exp(-k*t) + y_0*(sin(k*t)^2 + cos(k*t)^2 - 1)"
RATES = {
    **DECAY,
    "s": {"role": "parameter", "domain": "real", "unit": "1/s"},
    "a": {"role": "parameter", "domain": "real", "unit": "1/s"},
}


@pytest.fixture
def bench(statement_validator: StatementValidator) -> SymbolicBench:
    return SymbolicBench(statement_validator, CandidateClaim(), OdeSubstitutionVerifier())


def _review(bench: SymbolicBench, candidate: str) -> SymbolicResult:
    return bench.run(DECAY_EQUATION, DECAY, conditions=[DECAY_CONDITION], candidate=candidate)


def _failed(result: SymbolicResult) -> set[str]:
    return {
        identifier
        for identifier, status in result.statuses.items()
        if status is VerificationStatus.FAILED
    }


def test_correct_candidate_satisfies_the_equation_and_the_initial_condition(
    bench: SymbolicBench,
) -> None:
    result = _review(bench, DECAY_SOLUTION)

    assert result.answer == DECAY_SOLUTION
    assert result.statuses["equation_residual"] is VerificationStatus.PASSED
    assert result.statuses["initial_condition"] is VerificationStatus.PASSED
    assert result.verification.status is VerificationStatus.PASSED


def test_candidate_with_the_wrong_initial_value_fails_only_the_initial_condition(
    bench: SymbolicBench,
) -> None:
    result = _review(bench, WRONG_INITIAL_VALUE)

    assert _failed(result) == {"initial_condition"}
    assert result.statuses["equation_residual"] is VerificationStatus.PASSED
    assert result.verification.status is VerificationStatus.FAILED


def test_candidate_with_the_wrong_sign_fails_only_the_equation(bench: SymbolicBench) -> None:
    result = _review(bench, WRONG_SIGN)

    assert _failed(result) == {"equation_residual"}
    assert result.statuses["initial_condition"] is VerificationStatus.PASSED
    assert result.verification.status is VerificationStatus.FAILED


def test_report_distinguishes_the_two_reasons_for_rejection(bench: SymbolicBench) -> None:
    wrong_value = _review(bench, WRONG_INITIAL_VALUE)
    wrong_sign = _review(bench, WRONG_SIGN)

    assert _failed(wrong_value).isdisjoint(_failed(wrong_sign))
    assert "y_0" in wrong_value.check("initial_condition").observed
    assert "2*k*y_0*exp(k*t)" in wrong_sign.check("equation_residual").observed


def test_candidate_wrong_in_both_ways_fails_both_checks(bench: SymbolicBench) -> None:
    assert _failed(_review(bench, "y(t) = 2*y_0*exp(k*t)")) == {
        "equation_residual",
        "initial_condition",
    }


def test_refutation_by_substitution_is_reported_as_proof_not_as_sampling(
    bench: SymbolicBench,
) -> None:
    check = _review(bench, WRONG_SIGN).check("equation_residual")

    assert check.kind is EvidenceKind.PROOF
    assert "amostr" not in check.observed


def test_agreement_at_sampled_points_alone_leaves_the_review_inconclusive(
    statement_validator: StatementValidator,
) -> None:
    sampling_only = OdeSubstitutionVerifier(IdentityTester(simplify=lambda residual: residual))
    bench = SymbolicBench(statement_validator, CandidateClaim(), sampling_only)

    result = bench.run(
        DECAY_EQUATION,
        DECAY,
        conditions=[DECAY_CONDITION],
        candidate=HIDDEN_IDENTITY,
    )

    check = result.check("equation_residual")
    assert check.status is VerificationStatus.INCONCLUSIVE
    assert check.kind is EvidenceKind.NUMERICAL_EVIDENCE
    assert "amostragem não prova a identidade" in check.observed
    assert result.verification.status is VerificationStatus.INCONCLUSIVE


def test_candidate_valid_only_for_a_nonzero_rate_is_conditional(bench: SymbolicBench) -> None:
    result = bench.run(
        "y' = a*y + s",
        RATES,
        conditions=[DECAY_CONDITION],
        candidate="y(t) = -s/a + (y_0 + s/a)*exp(a*t)",
    )

    assert result.assumptions == [f"a {NOT_ZERO}"]
    assert result.statuses["equation_residual"] is VerificationStatus.PASSED
    assert result.statuses["initial_condition"] is VerificationStatus.PASSED
    assert result.verification.status is VerificationStatus.CONDITIONAL


def test_candidate_hidden_behind_an_identity_is_proven_once_it_is_simplified(
    bench: SymbolicBench,
) -> None:
    result = _review(bench, HIDDEN_IDENTITY)

    assert result.check("equation_residual").kind is EvidenceKind.PROOF
    assert result.verification.status is VerificationStatus.PASSED


def test_candidate_defined_nowhere_is_refused_before_the_review(bench: SymbolicBench) -> None:
    diagnostic = bench.refusal(
        DECAY_EQUATION, DECAY, conditions=[DECAY_CONDITION], candidate="y(t) = y_0*k/(k - k)"
    )

    assert diagnostic.code is DiagnosticCode.UNDEFINED_EXPRESSION


def test_candidate_of_the_wrong_dimension_is_refused_at_validation(bench: SymbolicBench) -> None:
    diagnostic = bench.refusal(
        DECAY_EQUATION, DECAY, conditions=[DECAY_CONDITION], candidate="y(t) = k*y_0*exp(-k*t)"
    )

    assert diagnostic.code is DiagnosticCode.DIMENSION_MISMATCH
    assert diagnostic.pointer == "/candidate"


def test_review_is_offered_only_inside_the_family_the_card_declares(bench: SymbolicBench) -> None:
    diagnostic = bench.refusal(
        "y' = -k*y*y", DECAY, conditions=[DECAY_CONDITION], candidate="y(t) = y_0/(1 + k*y_0*t)"
    )

    assert diagnostic.code is DiagnosticCode.OUTSIDE_COVERAGE
    assert diagnostic.category is DiagnosticCategory.UNSUPPORTED_PROBLEM
