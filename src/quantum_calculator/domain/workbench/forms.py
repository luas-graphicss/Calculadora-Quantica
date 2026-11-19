from dataclasses import dataclass
from enum import StrEnum


class Presence(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"


class InputKind(StrEnum):
    PROBLEM = "problem"
    STATEMENT = "statement"
    NUMERICAL = "numerical"


@dataclass(frozen=True, slots=True)
class Confirmation:
    key: str
    value: str
    statement: str


@dataclass(frozen=True, slots=True)
class ConstantChoice:
    identifier: str
    symbol: str
    name: str


@dataclass(frozen=True, slots=True)
class QuantityField:
    name: str
    symbol: str
    label: str
    dimension: str
    units: tuple[str, ...]
    constants: tuple[ConstantChoice, ...]


@dataclass(frozen=True, slots=True)
class CountField:
    name: str
    symbol: str
    label: str


@dataclass(frozen=True, slots=True)
class SettingField:
    name: str
    label: str


@dataclass(frozen=True, slots=True)
class NotationFields:
    has_statement: bool
    has_equations: bool
    has_conditions: bool
    has_candidate: bool
    symbols_carry_values: bool


@dataclass(frozen=True, slots=True)
class ArrayField:
    section: str
    member: str | None
    label: str
    rank: int
    presence: Presence
    is_normalizable: bool
    has_unit: bool


@dataclass(frozen=True, slots=True)
class RequestedFields:
    quantity: str | None
    label: str
    units: tuple[str, ...]
    presence: Presence


@dataclass(frozen=True, slots=True)
class CardForm:
    kind: InputKind
    confirmations: tuple[Confirmation, ...]
    quantities: tuple[QuantityField, ...]
    counts: tuple[CountField, ...]
    notation: NotationFields | None
    arrays: tuple[ArrayField, ...]
    settings: tuple[SettingField, ...]
    requested: RequestedFields | None
    covariance_models: tuple[str, ...]
