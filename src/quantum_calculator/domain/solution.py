from dataclasses import dataclass

from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.rounding import RoundingPolicy


class NonFiniteResultError(ArithmeticError):
    pass


@dataclass(frozen=True, slots=True)
class SolvePlan:
    method: MethodDescription
    rounding: RoundingPolicy


@dataclass(frozen=True, slots=True)
class SymbolicExpression:
    plain: str
    latex: str


@dataclass(frozen=True, slots=True)
class CalculationStep:
    description: str
    expression: str
    value: Quantity | None


@dataclass(frozen=True, slots=True)
class UncertaintyContribution:
    parameter: str
    symbol: str
    sensitivity: Quantity
    standard_uncertainty: Quantity
    variance: Quantity


@dataclass(frozen=True, slots=True)
class UncertaintyEvaluation:
    covariance: str
    contributions: tuple[UncertaintyContribution, ...]
    variance: Quantity


@dataclass(frozen=True, slots=True)
class SolverReport:
    expression: SymbolicExpression
    nature: ResultNature
    value: Quantity
    constants: tuple[PhysicalConstant, ...]
    steps: tuple[CalculationStep, ...]
    uncertainty: UncertaintyEvaluation | None
