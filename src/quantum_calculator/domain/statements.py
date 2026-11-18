from dataclasses import dataclass
from enum import StrEnum

from quantum_calculator.domain.dimensions import Dimension
from quantum_calculator.domain.expression_traversal import unknown_functions
from quantum_calculator.domain.expressions import Equation, Statement
from quantum_calculator.domain.problem_spec import SourceDocument
from quantum_calculator.domain.statement_cards import StatementCard


class Notation(StrEnum):
    TEXT = "text"
    LATEX = "latex"


class SymbolRole(StrEnum):
    VARIABLE = "variable"
    PARAMETER = "parameter"
    FUNCTION = "function"


class SymbolDomain(StrEnum):
    REAL = "real"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NONNEGATIVE = "nonnegative"
    NONZERO = "nonzero"


class CardSelection(StrEnum):
    CONFIRMED = "confirmed"
    SUGGESTED = "suggested"


@dataclass(frozen=True, slots=True)
class SymbolDeclaration:
    name: str
    role: str
    domain: str
    unit: str
    argument: str | None


@dataclass(frozen=True, slots=True)
class StatementSpec:
    source: SourceDocument
    schema_version: str
    notation: str
    statement: str
    symbols: tuple[SymbolDeclaration, ...]
    card_identifier: str | None
    conditions: tuple[str, ...]
    candidate: str | None
    description: str | None


@dataclass(frozen=True, slots=True)
class BoundSymbol:
    name: str
    role: SymbolRole
    domain: SymbolDomain
    dimension: Dimension
    unit: str
    argument: str | None

    def require_argument(self) -> str:
        if self.argument is None:
            raise LookupError(f"symbol {self.name} was not declared as a function of a variable")
        return self.argument


@dataclass(frozen=True, slots=True)
class ValidatedStatement:
    spec: StatementSpec
    notation: Notation
    card: StatementCard
    selection: CardSelection
    symbols: tuple[BoundSymbol, ...]
    statement: Statement
    conditions: tuple[Equation, ...]
    candidate: Equation | None
    result_dimension: Dimension

    def symbol(self, name: str) -> BoundSymbol:
        for bound in self.symbols:
            if bound.name == name:
                return bound
        raise KeyError(name)

    @property
    def variable_names(self) -> frozenset[str]:
        return frozenset(bound.name for bound in self.symbols if bound.role is SymbolRole.VARIABLE)

    @property
    def unknown(self) -> BoundSymbol:
        references = unknown_functions(self.statement)
        if not references:
            raise LookupError("the statement has no unknown function")
        return self.symbol(references[0].name)
