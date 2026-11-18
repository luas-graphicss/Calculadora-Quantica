import math

import pytest

from quantum_calculator.domain.diagnostics import DiagnosticCategory, ProblemRejectedError
from quantum_calculator.domain.numerical.layout import TRAJECTORY, final_value
from quantum_calculator.solvers.ode.explicit_runge_kutta import ExplicitRungeKuttaSolver
from support.numerical import VARIABLE, column, initial_value_problem

SOLVER = ExplicitRungeKuttaSolver()
DECAY = initial_value_problem({"y": "-k*y"}, {"y": 1.0}, end=5.0, samples=51, values={"k": 1.0})
OSCILLATOR = initial_value_problem(
    {"x": "v", "v": "-x"}, {"x": 1.0, "v": 0.0}, end=2 * math.pi, samples=33
)


@pytest.mark.numerical
def test_decay_follows_the_exponential_at_every_requested_instant() -> None:
    report = SOLVER.solve(DECAY)

    instants = column(report, TRAJECTORY, VARIABLE)
    values = column(report, TRAJECTORY, "y")
    assert len(instants) == 51
    assert instants[0] == 0.0
    assert instants[-1] == 5.0
    assert (
        max(
            abs(value - math.exp(-instant)) for instant, value in zip(instants, values, strict=True)
        )
        <= 1e-8
    )


@pytest.mark.numerical
def test_small_system_returns_to_its_initial_state_after_one_period() -> None:
    report = SOLVER.solve(OSCILLATOR)

    assert report.answer(final_value("x")).value == pytest.approx(1.0, abs=1e-8)
    assert report.answer(final_value("v")).value == pytest.approx(0.0, abs=1e-8)
    assert column(report, TRAJECTORY, "x")[16] == pytest.approx(-1.0, abs=1e-8)


def test_tolerances_evaluations_and_termination_are_recorded() -> None:
    report = SOLVER.solve(DECAY)

    effective = {parameter.name: parameter.value for parameter in report.effective}
    assert effective["relative_tolerance"] == "1e-10"
    assert effective["absolute_tolerance"] == "1e-12"
    assert int(effective["evaluations"]) > 0
    assert "successfully reached the end" in effective["termination"]


def test_solution_that_blows_up_inside_the_interval_yields_no_answer() -> None:
    blow_up = initial_value_problem({"y": "y^2"}, {"y": 1.0}, end=2.0, samples=11)

    with pytest.raises(ProblemRejectedError) as refusal:
        SOLVER.solve(blow_up)

    (diagnostic,) = refusal.value.diagnostics
    assert refusal.value.category is DiagnosticCategory.NON_CONVERGENT
    assert diagnostic.code.value == "method_not_converged"
    assert "step size" in diagnostic.message


def test_right_hand_side_that_is_not_finite_yields_no_answer() -> None:
    singular = initial_value_problem({"y": "1/(t - 1)"}, {"y": 0.0}, end=2.0, samples=3)

    with pytest.raises(ProblemRejectedError) as refusal:
        SOLVER.solve(singular)

    assert refusal.value.category is DiagnosticCategory.NON_CONVERGENT
