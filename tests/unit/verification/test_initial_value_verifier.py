from dataclasses import replace

import pytest

from quantum_calculator.domain.numerical.layout import TRAJECTORY
from quantum_calculator.domain.numerical.report import NumericalSolverReport, SampleColumn
from quantum_calculator.domain.verification import EvidenceKind, VerificationStatus
from quantum_calculator.solvers.ode.explicit_runge_kutta import ExplicitRungeKuttaSolver
from quantum_calculator.verification.numerical.initial_value import InitialValueVerifier
from support.numerical import initial_value_problem, statuses

DECAY = initial_value_problem({"y": "-k*y"}, {"y": 1.0}, end=5.0, samples=51, values={"k": 1.0})
VERIFIER = InitialValueVerifier()


def _with_trajectory(
    report: NumericalSolverReport, values: tuple[float, ...]
) -> NumericalSolverReport:
    table = report.table(TRAJECTORY)
    columns = tuple(
        replace(column, values=values) if column.name == "y" else column for column in table.columns
    )
    return replace(report, tables=(replace(table, columns=columns),))


def _reported() -> tuple[NumericalSolverReport, SampleColumn]:
    report = ExplicitRungeKuttaSolver().solve(DECAY)
    return report, report.table(TRAJECTORY).column("y")


@pytest.mark.numerical
def test_trajectory_from_the_integrator_passes_both_checks() -> None:
    report, _ = _reported()

    verification = VERIFIER.verify(DECAY, report)

    assert verification.status is VerificationStatus.PASSED
    assert statuses(verification) == {
        "initial_condition": VerificationStatus.PASSED,
        "tolerance_refinement": VerificationStatus.PASSED,
    }
    assert {skipped.identifier for skipped in verification.not_performed} == {
        "closed_form_solution",
        "stiffness_detection",
    }


@pytest.mark.numerical
def test_refinement_is_numerical_evidence_not_a_proof() -> None:
    report, _ = _reported()

    kinds = {check.identifier: check.kind for check in VERIFIER.verify(DECAY, report).checks}

    assert kinds["tolerance_refinement"] is EvidenceKind.NUMERICAL_EVIDENCE


@pytest.mark.numerical
def test_trajectory_that_drifts_from_the_refined_one_fails_the_refinement() -> None:
    report, values = _reported()
    drifting = tuple(value * (1 + 1e-6) for value in values.values)

    verification = VERIFIER.verify(DECAY, _with_trajectory(report, drifting))

    assert statuses(verification)["tolerance_refinement"] is VerificationStatus.FAILED
    assert verification.status is VerificationStatus.FAILED


@pytest.mark.numerical
def test_trajectory_that_starts_elsewhere_fails_the_initial_condition() -> None:
    report, values = _reported()
    displaced = (values.values[0] + 1e-3, *values.values[1:])

    verification = VERIFIER.verify(DECAY, _with_trajectory(report, displaced))

    assert statuses(verification)["initial_condition"] is VerificationStatus.FAILED
