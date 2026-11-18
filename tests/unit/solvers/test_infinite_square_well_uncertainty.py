from dataclasses import replace
from fractions import Fraction

import pytest

from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.domain.dimensions import ENERGY, LENGTH, MASS
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.solution import NonFiniteResultError, UncertaintyEvaluation
from quantum_calculator.domain.validated_problem import ValidatedProblem
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem
from quantum_calculator.solvers.symbolic.infinite_square_well import InfiniteSquareWellSolver
from support.documents import ProblemDocument

MASS_UNCERTAINTY = Fraction("2.8e-40")
WIDTH_UNCERTAINTY = Fraction(1, 10**11)


def _validated(validator: ProblemValidator, document: ProblemDocument) -> ValidatedProblem:
    return validator.validate(decode_problem(document.encode()))


def _evaluation(
    validator: ProblemValidator, solver: InfiniteSquareWellSolver, document: ProblemDocument
) -> tuple[Fraction, UncertaintyEvaluation]:
    report = solver.solve(_validated(validator, document))
    assert report.uncertainty is not None
    return report.value.magnitude, report.uncertainty


@pytest.mark.algebraic
def test_sensitivities_equal_the_analytic_derivatives(
    validator: ProblemValidator,
    solver: InfiniteSquareWellSolver,
    uncertain_electron_box: ProblemDocument,
) -> None:
    problem = _validated(validator, uncertain_electron_box)
    mass = problem.quantity("mass").quantity.magnitude
    width = problem.quantity("width").quantity.magnitude

    energy, evaluation = _evaluation(validator, solver, uncertain_electron_box)

    by_parameter = {item.parameter: item for item in evaluation.contributions}
    assert by_parameter["mass"].sensitivity == Quantity(-energy / mass, ENERGY / MASS)
    assert by_parameter["width"].sensitivity == Quantity(-2 * energy / width, ENERGY / LENGTH)
    assert by_parameter["mass"].standard_uncertainty == Quantity(MASS_UNCERTAINTY, MASS)
    assert by_parameter["width"].standard_uncertainty == Quantity(WIDTH_UNCERTAINTY, LENGTH)


@pytest.mark.algebraic
def test_independent_inputs_add_their_variances(
    validator: ProblemValidator,
    solver: InfiniteSquareWellSolver,
    uncertain_electron_box: ProblemDocument,
) -> None:
    problem = _validated(validator, uncertain_electron_box)
    mass = problem.quantity("mass").quantity.magnitude
    width = problem.quantity("width").quantity.magnitude

    energy, evaluation = _evaluation(validator, solver, uncertain_electron_box)

    relative_variance = (MASS_UNCERTAINTY / mass) ** 2 + (2 * WIDTH_UNCERTAINTY / width) ** 2
    assert evaluation.covariance == "independent"
    assert evaluation.variance == Quantity(energy**2 * relative_variance, ENERGY**2)


@pytest.mark.algebraic
def test_inputs_declared_exact_contribute_no_variance(
    validator: ProblemValidator,
    solver: InfiniteSquareWellSolver,
    uncertain_electron_box: ProblemDocument,
) -> None:
    document = uncertain_electron_box.with_value(
        "/uncertainty/standard_uncertainties/mass", {"value": 0, "unit": "kg"}
    ).with_value("/uncertainty/standard_uncertainties/width", {"value": 0, "unit": "nm"})

    _, evaluation = _evaluation(validator, solver, document)

    assert evaluation.variance.magnitude == 0


def test_no_error_bar_is_invented_when_no_uncertainty_was_declared(
    validator: ProblemValidator, solver: InfiniteSquareWellSolver, electron_box: ProblemDocument
) -> None:
    report = solver.solve(_validated(validator, electron_box))

    assert report.uncertainty is None


def test_covariance_model_without_a_propagation_rule_is_refused(
    validator: ProblemValidator,
    solver: InfiniteSquareWellSolver,
    uncertain_electron_box: ProblemDocument,
) -> None:
    problem = _validated(validator, uncertain_electron_box)
    assert problem.uncertainty is not None
    correlated = replace(problem, uncertainty=replace(problem.uncertainty, covariance="correlated"))

    with pytest.raises(ValueError, match="correlated"):
        solver.solve(correlated)


def test_width_that_escaped_validation_does_not_yield_an_infinite_energy(
    validator: ProblemValidator, solver: InfiniteSquareWellSolver, electron_box: ProblemDocument
) -> None:
    problem = _validated(validator, electron_box)
    zero_width = replace(problem.quantity("width"), quantity=Quantity(Fraction(0), LENGTH))
    corrupted = replace(problem, quantities=(problem.quantity("mass"), zero_width))

    with pytest.raises(NonFiniteResultError):
        solver.solve(corrupted)
