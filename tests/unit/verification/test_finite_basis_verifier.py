import math
from dataclasses import replace

import pytest

from quantum_calculator.domain.numerical.layout import (
    DEGENERACY,
    EIGENVALUE,
    EXPECTATION_VALUE,
    MEASUREMENT,
    PROBABILITY,
)
from quantum_calculator.domain.numerical.problems import ComplexMatrix
from quantum_calculator.domain.numerical.report import NumericalSolverReport
from quantum_calculator.domain.verification import VerificationStatus
from quantum_calculator.solvers.quantum.finite_basis import ProjectiveMeasurementSolver
from quantum_calculator.verification.numerical.finite_basis import FiniteBasisVerifier
from support.numerical import finite_basis_problem, statuses

ROOT_HALF = math.sqrt(0.5)
PAULI_Z: ComplexMatrix = ((1 + 0j, 0j), (0j, -1 + 0j))
RAISING: ComplexMatrix = ((0j, 1 + 0j), (0j, 0j))
SPIN = finite_basis_problem((ROOT_HALF + 0j, ROOT_HALF + 0j), PAULI_Z)
VERIFIER = FiniteBasisVerifier()
EVERY_CHECK_PASSED = dict.fromkeys(
    (
        "hermitian_operator",
        "normalized_state",
        "total_probability",
        "subspace_projectors",
        "direct_expectation_value",
        "global_phase_invariance",
    ),
    VerificationStatus.PASSED,
)


def _with_column(
    report: NumericalSolverReport, name: str, values: tuple[float, ...]
) -> NumericalSolverReport:
    tables = tuple(
        replace(
            table,
            columns=tuple(
                replace(column, values=values) if column.name == name else column
                for column in table.columns
            ),
        )
        if table.name == MEASUREMENT
        else table
        for table in report.tables
    )
    return replace(report, tables=tables)


@pytest.mark.numerical
def test_measurement_from_the_solver_passes_every_check() -> None:
    verification = VERIFIER.verify(SPIN, ProjectiveMeasurementSolver().solve(SPIN))

    assert verification.status is VerificationStatus.PASSED
    assert statuses(verification) == EVERY_CHECK_PASSED


@pytest.mark.numerical
def test_calculation_in_another_basis_is_checked_against_the_input_basis() -> None:
    rotated = replace(
        SPIN,
        basis=((ROOT_HALF + 0j, ROOT_HALF + 0j), (ROOT_HALF + 0j, -ROOT_HALF + 0j)),
    )

    verification = VERIFIER.verify(rotated, ProjectiveMeasurementSolver().solve(rotated))

    assert statuses(verification) == EVERY_CHECK_PASSED


@pytest.mark.numerical
def test_swapped_probabilities_are_caught_by_the_independent_projectors() -> None:
    biased = replace(SPIN, state=(0.6 + 0j, 0.8 + 0j))
    report = ProjectiveMeasurementSolver().solve(biased)

    verification = VERIFIER.verify(biased, _with_column(report, PROBABILITY, (0.36, 0.64)))

    found = statuses(verification)
    assert found["subspace_projectors"] is VerificationStatus.FAILED
    assert found["total_probability"] is VerificationStatus.PASSED
    assert verification.status is VerificationStatus.FAILED


@pytest.mark.numerical
def test_wrong_degeneracy_is_caught_by_the_rank_of_the_projector() -> None:
    report = ProjectiveMeasurementSolver().solve(SPIN)

    verification = VERIFIER.verify(SPIN, _with_column(report, DEGENERACY, (1.0, 2.0)))

    assert statuses(verification)["subspace_projectors"] is VerificationStatus.FAILED


@pytest.mark.numerical
def test_wrong_eigenvalue_is_caught_by_the_independent_projectors() -> None:
    report = ProjectiveMeasurementSolver().solve(SPIN)

    verification = VERIFIER.verify(SPIN, _with_column(report, EIGENVALUE, (-1.0, 2.0)))

    assert statuses(verification)["subspace_projectors"] is VerificationStatus.FAILED


@pytest.mark.numerical
def test_wrong_expectation_value_is_caught_by_the_direct_product() -> None:
    report = ProjectiveMeasurementSolver().solve(SPIN)
    answer = replace(report.answer(EXPECTATION_VALUE), value=0.25)

    verification = VERIFIER.verify(SPIN, replace(report, answers=(answer,)))

    assert statuses(verification)["direct_expectation_value"] is VerificationStatus.FAILED


def test_operator_that_is_not_hermitian_fails_the_adjoint_check() -> None:
    forged = replace(SPIN, observable=RAISING)
    report = ProjectiveMeasurementSolver().solve(SPIN)

    verification = VERIFIER.verify(forged, report)

    assert statuses(verification)["hermitian_operator"] is VerificationStatus.FAILED
    assert verification.status is VerificationStatus.FAILED


def test_state_used_without_unit_norm_fails_the_normalization_check() -> None:
    unnormalized = replace(SPIN, state=(1 + 0j, 1 + 0j))

    verification = VERIFIER.verify(unnormalized, ProjectiveMeasurementSolver().solve(unnormalized))

    assert statuses(verification)["normalized_state"] is VerificationStatus.FAILED
