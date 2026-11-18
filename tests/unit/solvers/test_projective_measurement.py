import cmath
import math

import pytest

from quantum_calculator.domain.numerical.layout import (
    DEGENERACY,
    EIGENVALUE,
    EXPECTATION_VALUE,
    MEASUREMENT,
    PROBABILITY,
)
from quantum_calculator.domain.numerical.problems import ComplexMatrix, ComplexVector
from quantum_calculator.domain.numerical.report import NumericalSolverReport
from quantum_calculator.solvers.quantum.finite_basis import ProjectiveMeasurementSolver
from support.numerical import column, finite_basis_problem

SOLVER = ProjectiveMeasurementSolver()
ROOT_HALF = math.sqrt(0.5)
PAULI_X: ComplexMatrix = ((0j, 1 + 0j), (1 + 0j, 0j))
PAULI_Y: ComplexMatrix = ((0j, -1j), (1j, 0j))
PAULI_Z: ComplexMatrix = ((1 + 0j, 0j), (0j, -1 + 0j))
PLUS_X: ComplexVector = (ROOT_HALF + 0j, ROOT_HALF + 0j)
X_BASIS: ComplexMatrix = (PLUS_X, (ROOT_HALF + 0j, -ROOT_HALF + 0j))
Y_BASIS: ComplexMatrix = ((ROOT_HALF + 0j, ROOT_HALF * 1j), (ROOT_HALF + 0j, -ROOT_HALF * 1j))
Z_ON_FIRST_OF_TWO_SPINS: ComplexMatrix = (
    (1 + 0j, 0j, 0j, 0j),
    (0j, 1 + 0j, 0j, 0j),
    (0j, 0j, -1 + 0j, 0j),
    (0j, 0j, 0j, -1 + 0j),
)


def _outcomes(report: NumericalSolverReport) -> list[tuple[float, float]]:
    return list(
        zip(
            column(report, MEASUREMENT, EIGENVALUE),
            column(report, MEASUREMENT, PROBABILITY),
            strict=True,
        )
    )


def _spin_outcomes(down: float, up: float) -> list[object]:
    return [pytest.approx((-1.0, down), abs=1e-12), pytest.approx((1.0, up), abs=1e-12)]


@pytest.mark.numerical
def test_spin_prepared_along_x_is_found_up_or_down_along_z_with_equal_probability() -> None:
    report = SOLVER.solve(finite_basis_problem(PLUS_X, PAULI_Z))

    assert _outcomes(report) == _spin_outcomes(down=0.5, up=0.5)
    assert report.answer(EXPECTATION_VALUE).value == pytest.approx(0.0, abs=1e-12)


@pytest.mark.numerical
@pytest.mark.parametrize("basis", [X_BASIS, Y_BASIS], ids=["x_basis", "y_basis"])
def test_probabilities_do_not_depend_on_the_orthonormal_basis_of_the_calculation(
    basis: ComplexMatrix,
) -> None:
    report = SOLVER.solve(finite_basis_problem(PLUS_X, PAULI_Z, basis=basis))

    assert _outcomes(report) == _spin_outcomes(down=0.5, up=0.5)


@pytest.mark.numerical
@pytest.mark.parametrize("angle", [0.3, math.pi / 2, math.pi, 4.0])
def test_probabilities_do_not_depend_on_a_global_phase(angle: float) -> None:
    rotated = tuple(cmath.exp(1j * angle) * component for component in PLUS_X)

    report = SOLVER.solve(finite_basis_problem(rotated, PAULI_Z))

    assert _outcomes(report) == _spin_outcomes(down=0.5, up=0.5)


@pytest.mark.numerical
def test_eigenstate_of_the_measured_observable_gives_a_certain_result() -> None:
    report = SOLVER.solve(finite_basis_problem(PLUS_X, PAULI_X))

    assert _outcomes(report) == _spin_outcomes(down=0.0, up=1.0)
    assert report.answer(EXPECTATION_VALUE).value == pytest.approx(1.0, abs=1e-12)


@pytest.mark.numerical
def test_complex_observable_is_measured_through_its_eigenspaces() -> None:
    report = SOLVER.solve(finite_basis_problem((1 + 0j, 0j), PAULI_Y))

    assert _outcomes(report) == _spin_outcomes(down=0.5, up=0.5)


@pytest.mark.numerical
def test_degenerate_eigenvalue_reports_the_probability_of_its_whole_subspace() -> None:
    state = (0.6 + 0j, 0.48j, 0.64 + 0j, 0j)

    report = SOLVER.solve(finite_basis_problem(state, Z_ON_FIRST_OF_TWO_SPINS))

    assert column(report, MEASUREMENT, DEGENERACY) == (2.0, 2.0)
    assert _outcomes(report) == _spin_outcomes(down=0.64**2, up=0.6**2 + 0.48**2)


def test_requested_normalization_is_recorded_with_the_original_norm() -> None:
    report = SOLVER.solve(finite_basis_problem((1 + 0j, 1 + 0j), PAULI_Z, normalize=True))

    effective = {parameter.name: parameter.value for parameter in report.effective}
    assert effective["normalization"].startswith("aplicada a pedido")
    assert repr(math.sqrt(2.0)) in effective["normalization"]


def test_state_given_normalized_is_recorded_as_left_untouched() -> None:
    report = SOLVER.solve(finite_basis_problem(PLUS_X, PAULI_Z))

    effective = {parameter.name: parameter.value for parameter in report.effective}
    assert effective["normalization"].startswith("não pedida")
    assert effective["basis"].startswith("computacional")
