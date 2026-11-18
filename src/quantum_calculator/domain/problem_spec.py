from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class SourceDocument:
    text: str
    sha256: str


@dataclass(frozen=True, slots=True)
class ExactNumber:
    value: Fraction
    literal: str


@dataclass(frozen=True, slots=True)
class QuantityInput:
    number: ExactNumber
    unit: str


@dataclass(frozen=True, slots=True)
class ConstantInput:
    identifier: str


type ParameterContent = ExactNumber | QuantityInput | ConstantInput


@dataclass(frozen=True, slots=True)
class ParameterInput:
    name: str
    content: ParameterContent


@dataclass(frozen=True, slots=True)
class HypothesisInput:
    key: str
    value: str


@dataclass(frozen=True, slots=True)
class RequestedOutput:
    quantity: str
    unit: str
    significant_digits: ExactNumber | None


@dataclass(frozen=True, slots=True)
class UncertaintyInput:
    parameter: str
    quantity: QuantityInput


@dataclass(frozen=True, slots=True)
class UncertaintyDeclaration:
    covariance: str
    standard_uncertainties: tuple[UncertaintyInput, ...]


@dataclass(frozen=True, slots=True)
class ProblemSpec:
    source: SourceDocument
    schema_version: str
    card_identifier: str
    description: str | None
    hypotheses: tuple[HypothesisInput, ...]
    parameters: tuple[ParameterInput, ...]
    requested: RequestedOutput
    uncertainty: UncertaintyDeclaration | None
