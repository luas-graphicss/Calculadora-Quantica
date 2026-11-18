import math
from dataclasses import replace

import pytest

from quantum_calculator.domain.numerical.layout import INTEGRAL
from quantum_calculator.domain.numerical.report import ErrorEstimate, NumericalSolverReport
from quantum_calculator.domain.verification import EvidenceKind, VerificationStatus
from quantum_calculator.solvers.quadrature.adaptive import AdaptiveQuadratureSolver
from quantum_calculator.verification.numerical.quadrature import QuadratureVerifier
from support.numerical import quadrature_problem, statuses

SINE = quadrature_problem("sin(x)", 0.0, math.pi)
VERIFIER = QuadratureVerifier()


def _claim(value: float, estimate: float | None = 1e-14) -> NumericalSolverReport:
    honest = AdaptiveQuadratureSolver().solve(SINE)
    answer = replace(
        honest.answer(INTEGRAL),
        value=value,
        estimate=None if estimate is None else ErrorEstimate(estimate, "claimed"),
    )
    return replace(honest, answers=(answer,))


@pytest.mark.numerical
def test_value_from_the_adaptive_integrator_passes_both_checks() -> None:
    report = VERIFIER.verify(SINE, AdaptiveQuadratureSolver().solve(SINE))

    assert report.status is VerificationStatus.PASSED
    assert statuses(report) == {
        "integrator_error_estimate": VerificationStatus.PASSED,
        "independent_quadrature": VerificationStatus.PASSED,
    }
    assert [skipped.identifier for skipped in report.not_performed] == ["closed_form_primitive"]


@pytest.mark.numerical
def test_independent_rule_is_numerical_evidence_not_a_proof() -> None:
    report = VERIFIER.verify(SINE, AdaptiveQuadratureSolver().solve(SINE))

    kinds = {check.identifier: check.kind for check in report.checks}
    assert kinds["independent_quadrature"] is EvidenceKind.NUMERICAL_EVIDENCE
    assert kinds["integrator_error_estimate"] is EvidenceKind.CONSISTENCY_TEST


@pytest.mark.numerical
def test_wrong_value_is_caught_by_the_independent_rule() -> None:
    report = VERIFIER.verify(SINE, _claim(2.0 + 1e-9))

    assert statuses(report)["independent_quadrature"] is VerificationStatus.FAILED
    assert report.status is VerificationStatus.FAILED


def test_estimate_above_the_requested_tolerance_fails_the_consistency_check() -> None:
    report = VERIFIER.verify(SINE, _claim(2.0, estimate=1e-6))

    assert statuses(report)["integrator_error_estimate"] is VerificationStatus.FAILED


def test_result_without_an_error_estimate_is_not_approved() -> None:
    report = VERIFIER.verify(SINE, _claim(2.0, estimate=None))

    assert statuses(report)["integrator_error_estimate"] is VerificationStatus.FAILED


@pytest.mark.numerical
def test_reference_rule_that_has_not_settled_leaves_the_check_inconclusive() -> None:
    kink = quadrature_problem("sqrt(abs(x - 1/3))", 0.0, 1.0)
    exact = (2 / 3) * ((1 / 3) ** 1.5 + (2 / 3) ** 1.5)

    report = VERIFIER.verify(kink, _claim(exact))

    assert statuses(report)["independent_quadrature"] is VerificationStatus.INCONCLUSIVE
    assert report.status is VerificationStatus.INCONCLUSIVE
