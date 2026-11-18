from dataclasses import replace
from fractions import Fraction

import pytest

from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.domain.dimensions import ENERGY, LENGTH
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.solution import SolverReport, SymbolicExpression
from quantum_calculator.domain.validated_problem import ValidatedProblem
from quantum_calculator.domain.verification import VerificationReport, VerificationStatus
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem
from quantum_calculator.verification.infinite_square_well import InfiniteSquareWellVerifier
from support.documents import ProblemDocument

PLANCK = Fraction("6.62607015e-34")
ELECTRON_MASS = Fraction("9.1093837139e-31")
GROUND_STATE_ENERGY = PLANCK**2 / (8 * ELECTRON_MASS * Fraction(1, 10**18))


def _validated(validator: ProblemValidator, document: ProblemDocument) -> ValidatedProblem:
    return validator.validate(decode_problem(document.encode()))


def _claim(energy: Quantity) -> SolverReport:
    return SolverReport(
        expression=SymbolicExpression(plain="claimed", latex="claimed"),
        nature=ResultNature.EXACT,
        value=energy,
        constants=(),
        steps=(),
        uncertainty=None,
    )


def _statuses(report: VerificationReport) -> dict[str, VerificationStatus]:
    return {check.identifier: check.status for check in report.checks}


def test_energy_derived_by_hand_passes_every_check(
    validator: ProblemValidator, verifier: InfiniteSquareWellVerifier, electron_box: ProblemDocument
) -> None:
    problem = _validated(validator, electron_box)

    report = verifier.verify(problem, _claim(Quantity(GROUND_STATE_ENERGY, ENERGY)))

    assert report.status is VerificationStatus.PASSED
    assert _statuses(report) == {
        "dimensional_consistency": VerificationStatus.PASSED,
        "stationary_schrodinger_residual": VerificationStatus.PASSED,
        "dirichlet_boundary": VerificationStatus.PASSED,
        "normalizable_mode": VerificationStatus.PASSED,
    }
    assert [skipped.identifier for skipped in report.not_performed] == [
        "independent_discrete_solution"
    ]
    assert report.references


@pytest.mark.parametrize("factor", [Fraction(2), Fraction(4), Fraction(999_999_999, 10**9)])
def test_energy_that_is_not_the_eigenvalue_fails_the_residual_check(
    validator: ProblemValidator,
    verifier: InfiniteSquareWellVerifier,
    electron_box: ProblemDocument,
    factor: Fraction,
) -> None:
    problem = _validated(validator, electron_box)

    report = verifier.verify(problem, _claim(Quantity(factor * GROUND_STATE_ENERGY, ENERGY)))

    statuses = _statuses(report)
    assert report.status is VerificationStatus.FAILED
    assert statuses["stationary_schrodinger_residual"] is VerificationStatus.FAILED
    assert statuses["dirichlet_boundary"] is VerificationStatus.PASSED


def test_energy_of_the_second_level_is_accepted_only_for_the_second_level(
    validator: ProblemValidator, verifier: InfiniteSquareWellVerifier, electron_box: ProblemDocument
) -> None:
    second_level_energy = _claim(Quantity(4 * GROUND_STATE_ENERGY, ENERGY))
    first = _validated(validator, electron_box)
    second = _validated(validator, electron_box.with_value("/parameters/level", 2))

    assert verifier.verify(first, second_level_energy).status is VerificationStatus.FAILED
    assert verifier.verify(second, second_level_energy).status is VerificationStatus.PASSED


def test_value_with_the_wrong_dimension_fails_the_consistency_check(
    validator: ProblemValidator, verifier: InfiniteSquareWellVerifier, electron_box: ProblemDocument
) -> None:
    problem = _validated(validator, electron_box)

    report = verifier.verify(problem, _claim(Quantity(GROUND_STATE_ENERGY, LENGTH)))

    assert _statuses(report)["dimensional_consistency"] is VerificationStatus.FAILED
    assert report.status is VerificationStatus.FAILED


def test_width_given_as_a_non_terminating_fraction_is_still_verified_exactly(
    validator: ProblemValidator, verifier: InfiniteSquareWellVerifier, electron_box: ProblemDocument
) -> None:
    problem = _validated(
        validator, electron_box.with_value("/parameters/width", {"value": "1/3", "unit": "nm"})
    )
    width = problem.quantity("width").quantity.magnitude
    energy = PLANCK**2 / (8 * ELECTRON_MASS * width**2)

    report = verifier.verify(problem, _claim(Quantity(energy, ENERGY)))

    assert report.status is VerificationStatus.PASSED


def test_wrong_energy_for_a_very_high_level_is_refused_without_expanding_trigonometry(
    validator: ProblemValidator, verifier: InfiniteSquareWellVerifier, electron_box: ProblemDocument
) -> None:
    level = 10**12
    problem = _validated(validator, electron_box.with_value("/parameters/level", level))
    energy = level**2 * GROUND_STATE_ENERGY

    assert verifier.verify(problem, _claim(Quantity(energy, ENERGY))).status is (
        VerificationStatus.PASSED
    )
    assert verifier.verify(problem, _claim(Quantity(2 * energy, ENERGY))).status is (
        VerificationStatus.FAILED
    )


def test_verifier_does_not_read_the_solver_calculation_memory(
    validator: ProblemValidator, verifier: InfiniteSquareWellVerifier, electron_box: ProblemDocument
) -> None:
    problem = _validated(validator, electron_box)
    claim = _claim(Quantity(GROUND_STATE_ENERGY, ENERGY))
    misleading = replace(claim, expression=SymbolicExpression(plain="E = 0", latex="E = 0"))

    assert verifier.verify(problem, misleading).status is VerificationStatus.PASSED
