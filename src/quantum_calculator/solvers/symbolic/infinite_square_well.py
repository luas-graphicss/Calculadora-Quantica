from fractions import Fraction

import sympy

from quantum_calculator.domain.constants import PLANCK_CONSTANT
from quantum_calculator.domain.methods import INDEPENDENT_COVARIANCE, ResultNature
from quantum_calculator.domain.ports import ConstantsEdition, require_constant
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.solution import (
    CalculationStep,
    NonFiniteResultError,
    SolverReport,
    SymbolicExpression,
    UncertaintyContribution,
    UncertaintyEvaluation,
)
from quantum_calculator.domain.validated_problem import DeclaredUncertainty, ValidatedProblem

_LEVEL = sympy.Symbol("n", integer=True, positive=True)
_PLANCK = sympy.Symbol("h", positive=True)
_MASS = sympy.Symbol("m", positive=True)
_WIDTH = sympy.Symbol("L", positive=True)
_NUMERATOR = _LEVEL**2 * _PLANCK**2
_DENOMINATOR = 8 * _MASS * _WIDTH**2
_ENERGY = _NUMERATOR / _DENOMINATOR
_SYMBOL_BY_PARAMETER = {"mass": _MASS, "width": _WIDTH}

EXPRESSION = SymbolicExpression(
    plain=f"E_n = {sympy.sstr(_ENERGY)}",
    latex=f"E_n = {sympy.latex(_ENERGY)}",
)

type _Substitutions = dict[sympy.Symbol, sympy.Rational]


class InfiniteSquareWellSolver:
    def __init__(self, constants: ConstantsEdition) -> None:
        self._planck = require_constant(constants, PLANCK_CONSTANT)

    def solve(self, problem: ValidatedProblem) -> SolverReport:
        mass = problem.quantity("mass").quantity
        width = problem.quantity("width").quantity
        planck = self._planck.value
        values: _Substitutions = {
            _LEVEL: sympy.Integer(problem.count("level").value),
            _PLANCK: _to_rational(planck.magnitude),
            _MASS: _to_rational(mass.magnitude),
            _WIDTH: _to_rational(width.magnitude),
        }
        numerator = Quantity(_evaluate(_NUMERATOR, values), planck.dimension**2)
        denominator = Quantity(_evaluate(_DENOMINATOR, values), mass.dimension * width.dimension**2)
        energy = Quantity(_evaluate(_ENERGY, values), numerator.dimension / denominator.dimension)
        return SolverReport(
            expression=EXPRESSION,
            nature=ResultNature.EXACT,
            value=energy,
            constants=(self._planck,),
            steps=(
                CalculationStep("Expressão fechada dos níveis de energia", EXPRESSION.plain, None),
                CalculationStep(
                    "Numerador em unidades coerentes do SI", sympy.sstr(_NUMERATOR), numerator
                ),
                CalculationStep(
                    "Denominador em unidades coerentes do SI", sympy.sstr(_DENOMINATOR), denominator
                ),
                CalculationStep("Energia em unidades coerentes do SI", sympy.sstr(_ENERGY), energy),
            ),
            uncertainty=_propagate(problem, energy, values),
        )


def _propagate(
    problem: ValidatedProblem, energy: Quantity, values: _Substitutions
) -> UncertaintyEvaluation | None:
    model = problem.uncertainty
    if model is None:
        return None
    if model.covariance != INDEPENDENT_COVARIANCE:
        raise ValueError(f"no propagation rule for covariance model {model.covariance!r}")
    contributions = tuple(
        _contribution(problem, energy, declared, values)
        for declared in model.standard_uncertainties
    )
    variance = sum(
        (contribution.variance.magnitude for contribution in contributions), start=Fraction(0)
    )
    return UncertaintyEvaluation(
        covariance=model.covariance,
        contributions=contributions,
        variance=Quantity(variance, energy.dimension**2),
    )


def _contribution(
    problem: ValidatedProblem,
    energy: Quantity,
    declared: DeclaredUncertainty,
    values: _Substitutions,
) -> UncertaintyContribution:
    bound = problem.quantity(declared.parameter)
    derivative = sympy.diff(_ENERGY, _SYMBOL_BY_PARAMETER[declared.parameter])
    sensitivity = _evaluate(derivative, values)
    uncertainty = declared.given.to_si()
    return UncertaintyContribution(
        parameter=declared.parameter,
        symbol=bound.symbol,
        sensitivity=Quantity(sensitivity, energy.dimension / bound.quantity.dimension),
        standard_uncertainty=uncertainty,
        variance=Quantity((sensitivity * uncertainty.magnitude) ** 2, energy.dimension**2),
    )


def _to_rational(value: Fraction) -> sympy.Rational:
    return sympy.Rational(value.numerator, value.denominator)


def _evaluate(expression: sympy.Expr, values: _Substitutions) -> Fraction:
    value = expression.subs(values)
    if not value.is_Rational:
        raise NonFiniteResultError(
            f"{sympy.sstr(expression)} did not reduce to a rational number: {sympy.sstr(value)}"
        )
    return Fraction(int(value.p), int(value.q))
