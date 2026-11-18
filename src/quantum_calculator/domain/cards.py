from dataclasses import dataclass

from quantum_calculator.domain.dimensions import Dimension
from quantum_calculator.domain.methods import MethodDescription


@dataclass(frozen=True, slots=True)
class PositiveQuantityRule:
    name: str
    symbol: str
    label: str
    dimension: Dimension


@dataclass(frozen=True, slots=True)
class PositiveIntegerRule:
    name: str
    symbol: str
    label: str


@dataclass(frozen=True, slots=True)
class HypothesisRule:
    key: str
    required_value: str
    statement: str


@dataclass(frozen=True, slots=True)
class OutputRule:
    quantity: str
    symbol: str
    label: str
    dimension: Dimension


@dataclass(frozen=True, slots=True)
class ProblemCard:
    identifier: str
    version: str
    area: str
    title: str
    scope: tuple[str, ...]
    quantities: tuple[PositiveQuantityRule, ...]
    counts: tuple[PositiveIntegerRule, ...]
    hypotheses: tuple[HypothesisRule, ...]
    outputs: tuple[OutputRule, ...]
    method: MethodDescription
    limitations: tuple[str, ...]
    example: str
