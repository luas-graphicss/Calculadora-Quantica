from dataclasses import dataclass

from quantum_calculator.domain.cards import OutputRule, ProblemCard
from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.domain.problem_spec import ExactNumber, ProblemSpec
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.rounding import RoundingPolicy
from quantum_calculator.domain.units import Unit


@dataclass(frozen=True, slots=True)
class UserQuantity:
    number: ExactNumber
    unit: Unit

    def to_si(self) -> Quantity:
        return self.unit.to_si(self.number.value)


type QuantityOrigin = UserQuantity | PhysicalConstant


@dataclass(frozen=True, slots=True)
class BoundQuantity:
    name: str
    symbol: str
    quantity: Quantity
    origin: QuantityOrigin


@dataclass(frozen=True, slots=True)
class BoundCount:
    name: str
    symbol: str
    value: int


@dataclass(frozen=True, slots=True)
class ConfirmedHypothesis:
    key: str
    value: str
    statement: str


@dataclass(frozen=True, slots=True)
class BoundOutput:
    rule: OutputRule
    unit: Unit
    rounding: RoundingPolicy


@dataclass(frozen=True, slots=True)
class DeclaredUncertainty:
    parameter: str
    given: UserQuantity


@dataclass(frozen=True, slots=True)
class UncertaintyModel:
    covariance: str
    standard_uncertainties: tuple[DeclaredUncertainty, ...]


@dataclass(frozen=True, slots=True)
class ValidatedProblem:
    spec: ProblemSpec
    card: ProblemCard
    hypotheses: tuple[ConfirmedHypothesis, ...]
    quantities: tuple[BoundQuantity, ...]
    counts: tuple[BoundCount, ...]
    output: BoundOutput
    uncertainty: UncertaintyModel | None

    def quantity(self, name: str) -> BoundQuantity:
        for bound in self.quantities:
            if bound.name == name:
                return bound
        raise KeyError(name)

    def count(self, name: str) -> BoundCount:
        for bound in self.counts:
            if bound.name == name:
                return bound
        raise KeyError(name)
