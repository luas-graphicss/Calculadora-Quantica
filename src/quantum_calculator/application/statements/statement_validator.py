from quantum_calculator.application.statements.card_selection import CardSelector
from quantum_calculator.application.statements.field_reader import FieldReader
from quantum_calculator.application.statements.semantics import SemanticChecker
from quantum_calculator.application.statements.symbols import SymbolBinder
from quantum_calculator.catalog.statement_catalog import StatementCatalog
from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    ProblemRejectedError,
    json_pointer,
    quote_user_text,
)
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.statements import Notation, StatementSpec, ValidatedStatement

_STATEMENT_POINTER = "/statement"
_CANDIDATE_POINTER = "/candidate"
_CONDITIONS = "conditions"


class StatementValidator:
    def __init__(self, catalog: StatementCatalog, units: UnitRegistry) -> None:
        self._selector = CardSelector(catalog)
        self._binder = SymbolBinder(units)

    def validate(self, spec: StatementSpec) -> ValidatedStatement:
        diagnostics: list[Diagnostic] = []
        notation = _notation(spec, diagnostics)
        symbols = self._binder.bind(spec.symbols, diagnostics)
        if notation is None or diagnostics:
            raise ProblemRejectedError(tuple(diagnostics))
        reader = FieldReader(notation, symbols, diagnostics)
        statement = reader.read(_STATEMENT_POINTER, spec.statement)
        conditions = [
            reader.read(json_pointer(_CONDITIONS, str(index)), text)
            for index, text in enumerate(spec.conditions)
        ]
        candidate = None
        if spec.candidate is not None:
            candidate = reader.read(_CANDIDATE_POINTER, spec.candidate)
        if statement is None or diagnostics:
            raise ProblemRejectedError(tuple(diagnostics))
        selected = self._selector.select(spec, statement.statement, diagnostics)
        if selected is None:
            raise ProblemRejectedError(tuple(diagnostics))
        semantics = SemanticChecker(symbols, reader).check(
            selected.card.shape,
            statement,
            tuple(condition for condition in conditions if condition is not None),
            candidate,
        )
        if semantics is None or diagnostics:
            raise ProblemRejectedError(tuple(diagnostics))
        return ValidatedStatement(
            spec=spec,
            notation=notation,
            card=selected.card,
            selection=selected.selection,
            symbols=tuple(symbols.values()),
            statement=statement.statement,
            conditions=semantics.conditions,
            candidate=semantics.candidate,
            result_dimension=semantics.result_dimension,
        )


def _notation(spec: StatementSpec, diagnostics: list[Diagnostic]) -> Notation | None:
    for notation in Notation:
        if notation.value == spec.notation:
            return notation
    diagnostics.append(
        Diagnostic(
            DiagnosticCode.UNKNOWN_OPTION,
            "/notation",
            f"{quote_user_text(spec.notation)} não é uma notação aceita.",
            f"uma destas notações: {', '.join(notation.value for notation in Notation)}",
        )
    )
    return None
