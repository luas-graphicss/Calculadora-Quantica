import math

import pytest

from quantum_calculator.domain.diagnostics import DiagnosticCategory, ProblemRejectedError
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.numerical.layout import INTEGRAL
from quantum_calculator.solvers.quadrature.adaptive import AdaptiveQuadratureSolver
from support.numerical import quadrature_problem

SOLVER = AdaptiveQuadratureSolver()


def _refusal(integrand: str, lower: float, upper: float) -> ProblemRejectedError:
    with pytest.raises(ProblemRejectedError) as refusal:
        SOLVER.solve(quadrature_problem(integrand, lower, upper))
    return refusal.value


@pytest.mark.numerical
def test_sine_from_zero_to_pi_integrates_to_two() -> None:
    report = SOLVER.solve(quadrature_problem("sin(x)", 0.0, math.pi))

    answer = report.answer(INTEGRAL)
    assert abs(answer.value - 2.0) <= 1e-10
    assert report.nature is ResultNature.APPROXIMATE


@pytest.mark.numerical
def test_integrator_estimate_is_reported_apart_from_the_value() -> None:
    answer = SOLVER.solve(quadrature_problem("sin(x)", 0.0, math.pi)).answer(INTEGRAL)

    assert answer.estimate is not None
    assert 0.0 < answer.estimate.value <= 1e-12 + 1e-12 * 2.0
    assert "integrador" in answer.estimate.origin


def test_tolerances_evaluations_and_termination_are_recorded() -> None:
    report = SOLVER.solve(quadrature_problem("sin(x)", 0.0, math.pi))

    effective = {parameter.name: parameter.value for parameter in report.effective}
    assert effective["absolute_tolerance"] == "1e-12"
    assert effective["relative_tolerance"] == "1e-12"
    assert int(effective["evaluations"]) > 0
    assert int(effective["subintervals"]) >= 1
    assert "ier = 0" in effective["termination"]


@pytest.mark.numerical
def test_parameter_value_enters_the_integrand() -> None:
    problem = quadrature_problem("a*x^2", 0.0, 1.0, values={"a": 3.0})

    assert SOLVER.solve(problem).answer(INTEGRAL).value == pytest.approx(1.0, abs=1e-12)


def test_integrand_that_is_not_finite_inside_the_interval_yields_no_answer() -> None:
    refusal = _refusal("1/x^2", -1.0, 1.0)

    (diagnostic,) = refusal.diagnostics
    assert refusal.category is DiagnosticCategory.NON_CONVERGENT
    assert diagnostic.code.value == "non_finite_result"


def test_oscillation_the_subdivision_limit_cannot_resolve_yields_no_answer() -> None:
    refusal = _refusal("sin(1000*x^3)", 0.0, 10.0)

    (diagnostic,) = refusal.diagnostics
    assert refusal.category is DiagnosticCategory.NON_CONVERGENT
    assert diagnostic.code.value == "method_not_converged"
    assert "limite de subdivisões foi atingido" in diagnostic.message
