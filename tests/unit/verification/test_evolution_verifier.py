from dataclasses import replace

import pytest

from quantum_calculator.domain.numerical.layout import (
    DENSITY,
    FINAL_DENSITY,
    NORM,
    OBSERVABLES,
    PHASE_ERROR,
    RELATIVE_PHASE,
    TIME_REFINEMENT,
)
from quantum_calculator.domain.numerical.report import NumericalSolverReport
from quantum_calculator.domain.verification import VerificationStatus
from quantum_calculator.solvers.quantum.evolution import CrankNicolsonEvolutionSolver
from quantum_calculator.verification.numerical.evolution import EvolutionVerifier
from support.numerical import statuses, well_evolution_problem

BEAT = well_evolution_problem(subintervals=256, steps=1024, samples=9)
VERIFIER = EvolutionVerifier()
BEAT_CHECKS = (
    "norm_conservation",
    "final_density_integral",
    "relative_phase",
    "scheme_dispersion",
    "temporal_order",
)


@pytest.fixture(scope="module")
def beat_report() -> NumericalSolverReport:
    return CrankNicolsonEvolutionSolver().solve(BEAT)


def _with_column(
    report: NumericalSolverReport, table_name: str, name: str, values: tuple[float, ...]
) -> NumericalSolverReport:
    tables = tuple(
        replace(
            table,
            columns=tuple(
                replace(column, values=values) if column.name == name else column
                for column in table.columns
            ),
        )
        if table.name == table_name
        else table
        for table in report.tables
    )
    return replace(report, tables=tables)


@pytest.mark.numerical
def test_beat_from_the_solver_passes_every_check(beat_report: NumericalSolverReport) -> None:
    verification = VERIFIER.verify(BEAT, beat_report)

    assert verification.status is VerificationStatus.PASSED
    assert statuses(verification) == dict.fromkeys(BEAT_CHECKS, VerificationStatus.PASSED)
    assert [skipped.identifier for skipped in verification.not_performed] == [
        "spatial_discretization"
    ]


@pytest.mark.numerical
def test_norm_hidden_by_rescaling_is_caught_by_the_final_density(
    beat_report: NumericalSolverReport,
) -> None:
    density = beat_report.table(FINAL_DENSITY).column(DENSITY).values
    leaked = tuple(0.99 * value for value in density)

    found = statuses(
        VERIFIER.verify(BEAT, _with_column(beat_report, FINAL_DENSITY, DENSITY, leaked))
    )

    assert found["final_density_integral"] is VerificationStatus.FAILED
    assert found["norm_conservation"] is VerificationStatus.PASSED


@pytest.mark.numerical
def test_drifting_norm_fails_the_conservation_check(beat_report: NumericalSolverReport) -> None:
    norms = beat_report.table(OBSERVABLES).column(NORM).values
    drifting = tuple(norm * (1 + 1e-7 * index) for index, norm in enumerate(norms))

    verification = VERIFIER.verify(BEAT, _with_column(beat_report, OBSERVABLES, NORM, drifting))

    assert statuses(verification)["norm_conservation"] is VerificationStatus.FAILED
    assert verification.status is VerificationStatus.FAILED


@pytest.mark.numerical
def test_phase_that_lags_the_discrete_modes_fails_both_phase_checks(
    beat_report: NumericalSolverReport,
) -> None:
    phases = beat_report.table(OBSERVABLES).column(RELATIVE_PHASE).values
    lagging = tuple(phase + 5e-3 * index for index, phase in enumerate(phases))

    found = statuses(
        VERIFIER.verify(BEAT, _with_column(beat_report, OBSERVABLES, RELATIVE_PHASE, lagging))
    )

    assert found["relative_phase"] is VerificationStatus.FAILED
    assert found["scheme_dispersion"] is VerificationStatus.FAILED


@pytest.mark.numerical
def test_phase_accurate_to_a_milliradian_but_not_from_the_scheme_is_flagged(
    beat_report: NumericalSolverReport,
) -> None:
    phases = beat_report.table(OBSERVABLES).column(RELATIVE_PHASE).values
    nudged = tuple(phase + 1e-5 for phase in phases)

    found = statuses(
        VERIFIER.verify(BEAT, _with_column(beat_report, OBSERVABLES, RELATIVE_PHASE, nudged))
    )

    assert found["relative_phase"] is VerificationStatus.PASSED
    assert found["scheme_dispersion"] is VerificationStatus.FAILED


@pytest.mark.numerical
def test_refinement_errors_that_the_scheme_cannot_produce_fail_the_order_check(
    beat_report: NumericalSolverReport,
) -> None:
    errors = beat_report.table(TIME_REFINEMENT).column(PHASE_ERROR).values
    first_order = (4 * errors[2], 2 * errors[2], errors[2])

    found = statuses(
        VERIFIER.verify(BEAT, _with_column(beat_report, TIME_REFINEMENT, PHASE_ERROR, first_order))
    )

    assert found["temporal_order"] is VerificationStatus.FAILED


@pytest.mark.numerical
def test_step_too_long_for_the_asymptotic_regime_is_not_declared_second_order() -> None:
    coarse = well_evolution_problem(subintervals=64, steps=8, samples=3)

    verification = VERIFIER.verify(coarse, CrankNicolsonEvolutionSolver().solve(coarse))

    found = statuses(verification)
    assert found["temporal_order"] is VerificationStatus.INCONCLUSIVE
    assert found["relative_phase"] is VerificationStatus.FAILED
    assert found["norm_conservation"] is VerificationStatus.PASSED
    assert verification.status is VerificationStatus.FAILED


@pytest.mark.numerical
def test_stationary_state_skips_the_phase_checks_instead_of_passing_them() -> None:
    stationary = well_evolution_problem(
        (1 + 0j,), subintervals=64, steps=64, samples=5, normalize=False
    )

    verification = VERIFIER.verify(stationary, CrankNicolsonEvolutionSolver().solve(stationary))

    assert statuses(verification) == {
        "norm_conservation": VerificationStatus.PASSED,
        "final_density_integral": VerificationStatus.PASSED,
    }
    assert [skipped.identifier for skipped in verification.not_performed] == [
        "relative_phase",
        "scheme_dispersion",
        "temporal_order",
        "spatial_discretization",
    ]
