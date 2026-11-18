from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import partial

from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode, SourceExcerpt
from quantum_calculator.domain.expressions import Statement
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.domain.statements import BoundSymbol, Notation
from quantum_calculator.notation.limits import MAX_STATEMENT_LENGTH
from quantum_calculator.notation.reader import read_statement


@dataclass(frozen=True, slots=True)
class ReadField:
    pointer: str
    text: str
    statement: Statement


class FieldReader:
    def __init__(
        self,
        notation: Notation,
        symbols: Mapping[str, BoundSymbol],
        diagnostics: list[Diagnostic],
    ) -> None:
        self._notation = notation
        self._symbols = symbols
        self._diagnostics = diagnostics

    def read(self, pointer: str, text: str) -> ReadField | None:
        statement = self._guard(
            pointer, text, partial(read_statement, self._notation, text, self._symbols)
        )
        return None if statement is None else ReadField(pointer, text, statement)

    def check[Checked](self, field: ReadField, rule: Callable[[], Checked]) -> Checked | None:
        return self._guard(field.pointer, field.text, rule)

    def report(self, field: ReadField, code: DiagnosticCode, message: str, expected: str) -> None:
        self._diagnostics.append(Diagnostic(code, field.pointer, message, expected))

    def _guard[Checked](
        self, pointer: str, text: str, rule: Callable[[], Checked]
    ) -> Checked | None:
        try:
            return rule()
        except StatementError as error:
            self._diagnostics.append(_diagnostic(error, pointer, text))
            return None


def _diagnostic(error: StatementError, pointer: str, text: str) -> Diagnostic:
    excerpt = None
    if len(text) <= MAX_STATEMENT_LENGTH:
        start = min(error.span.start, len(text))
        excerpt = SourceExcerpt(text, start, min(max(error.span.end, start), len(text)))
    return Diagnostic(error.code, pointer, error.message, error.expected, excerpt)
