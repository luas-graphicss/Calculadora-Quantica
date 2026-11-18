from dataclasses import dataclass
from typing import Protocol

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
    problem_type: str
    title: str
    domain: tuple[str, ...]
    scope: tuple[str, ...]
    quantities: tuple[PositiveQuantityRule, ...]
    counts: tuple[PositiveIntegerRule, ...]
    hypotheses: tuple[HypothesisRule, ...]
    outputs: tuple[OutputRule, ...]
    method: MethodDescription
    limitations: tuple[str, ...]
    example: str


class CatalogEntry(Protocol):
    @property
    def identifier(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def area(self) -> str: ...

    @property
    def problem_type(self) -> str: ...

    @property
    def title(self) -> str: ...

    @property
    def domain(self) -> tuple[str, ...]: ...

    @property
    def method(self) -> MethodDescription: ...

    @property
    def limitations(self) -> tuple[str, ...]: ...

    @property
    def example(self) -> str: ...


@dataclass(frozen=True, slots=True)
class CatalogListing:
    version: str
    entries: tuple[CatalogEntry, ...]
