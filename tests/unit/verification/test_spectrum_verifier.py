from dataclasses import replace

import pytest

from quantum_calculator.domain.numerical.layout import EIGENFUNCTIONS, eigenfunction, energy_level
from quantum_calculator.domain.numerical.report import NumericalSolverReport
from quantum_calculator.domain.verification import VerificationStatus
from quantum_calculator.solvers.quantum.stationary import TridiagonalSpectrumSolver
from quantum_calculator.verification.numerical.spectrum import SpectrumVerifier
from support.numerical import (
    JOULE,
    oscillator_spectrum_problem,
    statuses,
    well_spectrum_problem,
)

SOLVER = TridiagonalSpectrumSolver()
VERIFIER = SpectrumVerifier()
WELL = well_spectrum_problem(subintervals=512, levels=3)
OSCILLATOR = oscillator_spectrum_problem(half_width=8.0, subintervals=1024, levels=3)
WELL_CHECKS = (
    "discrete_residual",
    "weighted_orthonormality",
    "dirichlet_boundary",
    "level_placement",
    "mesh_refinement",
    "closed_form_agreement",
)


@pytest.fixture(scope="module")
def well_report() -> NumericalSolverReport:
    return SOLVER.solve(WELL)


def _with_energy(report: NumericalSolverReport, level: int, factor: float) -> NumericalSolverReport:
    answers = tuple(
        replace(answer, value=answer.value * factor)
        if answer.name == energy_level(level)
        else answer
        for answer in report.answers
    )
    return replace(report, answers=answers)


def _with_eigenfunction(
    report: NumericalSolverReport, level: int, values: tuple[float, ...]
) -> NumericalSolverReport:
    table = report.table(EIGENFUNCTIONS)
    columns = tuple(
        replace(column, values=values) if column.name == eigenfunction(level) else column
        for column in table.columns
    )
    tables = tuple(
        replace(table, columns=columns) if item.name == EIGENFUNCTIONS else item
        for item in report.tables
    )
    return replace(report, tables=tables)


@pytest.mark.numerical
def test_well_spectrum_from_the_solver_passes_every_check(
    well_report: NumericalSolverReport,
) -> None:
    verification = VERIFIER.verify(WELL, well_report)

    assert verification.status is VerificationStatus.PASSED
    assert statuses(verification) == dict.fromkeys(WELL_CHECKS, VerificationStatus.PASSED)
    assert [skipped.identifier for skipped in verification.not_performed] == ["domain_truncation"]


@pytest.mark.numerical
def test_oscillator_spectrum_also_passes_the_domain_truncation_experiment() -> None:
    verification = VERIFIER.verify(OSCILLATOR, SOLVER.solve(OSCILLATOR))

    assert verification.status is VerificationStatus.PASSED
    assert statuses(verification)["domain_truncation"] is VerificationStatus.PASSED
    assert verification.not_performed == ()


@pytest.mark.numerical
def test_spectrum_reported_in_joules_is_verified_like_the_one_in_electron_volts() -> None:
    in_joules = well_spectrum_problem(subintervals=128, levels=2, energy_unit=JOULE)

    assert VERIFIER.verify(in_joules, SOLVER.solve(in_joules)).status is VerificationStatus.PASSED


@pytest.mark.numerical
def test_deliberately_under_resolved_mesh_is_not_declared_converged() -> None:
    coarse = well_spectrum_problem(subintervals=16, levels=3)

    verification = VERIFIER.verify(coarse, SOLVER.solve(coarse))

    found = statuses(verification)
    assert found["mesh_refinement"] is VerificationStatus.INCONCLUSIVE
    assert found["discrete_residual"] is VerificationStatus.PASSED
    assert verification.status is not VerificationStatus.PASSED


@pytest.mark.numerical
def test_small_residual_does_not_stand_in_for_mesh_convergence() -> None:
    coarse = well_spectrum_problem(subintervals=16, levels=3)

    checks = {
        check.identifier: check for check in VERIFIER.verify(coarse, SOLVER.solve(coarse)).checks
    }

    assert "não a convergência da malha" in checks["discrete_residual"].statement
    assert "não é declarada convergida" in checks["mesh_refinement"].observed


@pytest.mark.numerical
def test_energy_that_is_not_the_discrete_eigenvalue_fails_the_residual(
    well_report: NumericalSolverReport,
) -> None:
    verification = VERIFIER.verify(WELL, _with_energy(well_report, 1, factor=2.0))

    found = statuses(verification)
    assert found["discrete_residual"] is VerificationStatus.FAILED
    assert found["level_placement"] is VerificationStatus.FAILED
    assert verification.status is VerificationStatus.FAILED


@pytest.mark.numerical
def test_levels_reported_out_of_order_fail_the_inertia_count_despite_a_small_residual(
    well_report: NumericalSolverReport,
) -> None:
    first, second, third = well_report.answers
    swapped_answers = (
        replace(second, name=first.name),
        replace(first, name=second.name),
        third,
    )
    table = well_report.table(EIGENFUNCTIONS)
    swapped = _with_eigenfunction(
        _with_eigenfunction(
            replace(well_report, answers=swapped_answers),
            1,
            table.column(eigenfunction(2)).values,
        ),
        2,
        table.column(eigenfunction(1)).values,
    )

    found = statuses(VERIFIER.verify(WELL, swapped))

    assert found["discrete_residual"] is VerificationStatus.PASSED
    assert found["level_placement"] is VerificationStatus.FAILED


@pytest.mark.numerical
def test_eigenfunction_scaled_by_the_euclidean_norm_fails_weighted_orthonormality(
    well_report: NumericalSolverReport,
) -> None:
    amplitudes = well_report.table(EIGENFUNCTIONS).column(eigenfunction(1)).values
    rescaled = tuple(2.0 * amplitude for amplitude in amplitudes)

    found = statuses(VERIFIER.verify(WELL, _with_eigenfunction(well_report, 1, rescaled)))

    assert found["weighted_orthonormality"] is VerificationStatus.FAILED
    assert found["discrete_residual"] is VerificationStatus.PASSED


@pytest.mark.numerical
def test_eigenfunction_that_does_not_vanish_at_a_wall_fails_the_boundary_check(
    well_report: NumericalSolverReport,
) -> None:
    amplitudes = well_report.table(EIGENFUNCTIONS).column(eigenfunction(1)).values
    leaking = (1.0, *amplitudes[1:])

    found = statuses(VERIFIER.verify(WELL, _with_eigenfunction(well_report, 1, leaking)))

    assert found["dirichlet_boundary"] is VerificationStatus.FAILED


@pytest.mark.numerical
def test_domain_that_cuts_the_oscillator_states_fails_the_truncation_experiment() -> None:
    cramped = oscillator_spectrum_problem(half_width=2.0, subintervals=256)

    verification = VERIFIER.verify(cramped, SOLVER.solve(cramped))

    found = statuses(verification)
    assert found["domain_truncation"] is VerificationStatus.FAILED
    assert found["closed_form_agreement"] is VerificationStatus.FAILED
    assert verification.status is VerificationStatus.FAILED
