from dataclasses import dataclass
from enum import StrEnum

from quantum_calculator.domain.cards import HypothesisRule, PositiveQuantityRule
from quantum_calculator.domain.methods import MethodDescription


class NumericalFamily(StrEnum):
    QUADRATURE = "quadrature"
    INITIAL_VALUE = "initial_value"
    FINITE_BASIS = "finite_basis"
    WELL_SPECTRUM = "well_spectrum"
    OSCILLATOR_SPECTRUM = "oscillator_spectrum"
    WELL_EVOLUTION = "well_evolution"


class InputSection(StrEnum):
    HYPOTHESES = "hypotheses"
    PARAMETERS = "parameters"
    NOTATION = "notation"
    SYMBOLS = "symbols"
    STATEMENT = "statement"
    EQUATIONS = "equations"
    CONDITIONS = "conditions"
    STATE = "state"
    OBSERVABLE = "observable"
    BASIS = "basis"
    INITIAL_STATE = "initial_state"
    REQUESTED = "requested"


@dataclass(frozen=True, slots=True)
class NumericalCard:
    identifier: str
    version: str
    area: str
    problem_type: str
    title: str
    domain: tuple[str, ...]
    family: NumericalFamily
    required_sections: frozenset[InputSection]
    optional_sections: frozenset[InputSection]
    hypotheses: tuple[HypothesisRule, ...]
    quantities: tuple[PositiveQuantityRule, ...]
    method: MethodDescription
    limitations: tuple[str, ...]
    example: str
