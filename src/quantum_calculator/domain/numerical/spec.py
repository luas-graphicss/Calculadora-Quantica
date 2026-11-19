from dataclasses import dataclass

from quantum_calculator.domain.numerical.cards import InputSection
from quantum_calculator.domain.problem_spec import (
    ExactNumber,
    HypothesisInput,
    ParameterInput,
    SourceDocument,
)
from quantum_calculator.domain.statements import SymbolDeclaration


@dataclass(frozen=True, slots=True)
class ComplexInput:
    real: ExactNumber
    imaginary: ExactNumber | None


type VectorInput = tuple[ComplexInput, ...]
type MatrixInput = tuple[VectorInput, ...]


@dataclass(frozen=True, slots=True)
class StateInput:
    components: VectorInput
    normalize: bool


@dataclass(frozen=True, slots=True)
class ObservableInput:
    matrix: MatrixInput
    unit: str


@dataclass(frozen=True, slots=True)
class SymbolInput:
    declaration: SymbolDeclaration
    value: ExactNumber | None


@dataclass(frozen=True, slots=True)
class SettingInput:
    name: str
    number: ExactNumber


@dataclass(frozen=True, slots=True)
class RequestedDisplay:
    unit: str | None
    significant_digits: ExactNumber | None


@dataclass(frozen=True, slots=True)
class NumericalSpec:
    source: SourceDocument
    schema_version: str
    card_identifier: str
    description: str | None
    hypotheses: tuple[HypothesisInput, ...] | None
    parameters: tuple[ParameterInput, ...] | None
    notation: str | None
    symbols: tuple[SymbolInput, ...] | None
    statement: str | None
    equations: tuple[str, ...] | None
    conditions: tuple[str, ...] | None
    state: StateInput | None
    observable: ObservableInput | None
    basis: MatrixInput | None
    initial_state: StateInput | None
    numerics: tuple[SettingInput, ...] | None
    requested: RequestedDisplay | None

    @property
    def provided_sections(self) -> frozenset[InputSection]:
        contents: dict[InputSection, object | None] = {
            InputSection.HYPOTHESES: self.hypotheses,
            InputSection.PARAMETERS: self.parameters,
            InputSection.NOTATION: self.notation,
            InputSection.SYMBOLS: self.symbols,
            InputSection.STATEMENT: self.statement,
            InputSection.EQUATIONS: self.equations,
            InputSection.CONDITIONS: self.conditions,
            InputSection.STATE: self.state,
            InputSection.OBSERVABLE: self.observable,
            InputSection.BASIS: self.basis,
            InputSection.INITIAL_STATE: self.initial_state,
            InputSection.REQUESTED: self.requested,
        }
        return frozenset(section for section, content in contents.items() if content is not None)
