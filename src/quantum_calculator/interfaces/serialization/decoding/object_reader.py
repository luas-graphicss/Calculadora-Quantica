from fractions import Fraction
from typing import Self

from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    json_pointer,
    quote_user_text,
)
from quantum_calculator.domain.problem_spec import ExactNumber
from quantum_calculator.interfaces.serialization.decoding.json_document import NumberToken
from quantum_calculator.interfaces.serialization.decoding.number_literals import (
    NUMBER_EXPECTATION,
    NumberLiteralError,
    parse_exact_number,
)

MAX_TEXT_LENGTH = 256

_MISSING = object()
_PLACEHOLDER_NUMBER = ExactNumber(Fraction(0), "0")


class ObjectReader:
    def __init__(
        self, content: dict[str, object], pointer: str, diagnostics: list[Diagnostic]
    ) -> None:
        self._content = content
        self._pointer = pointer
        self._diagnostics = diagnostics
        self._read: set[str] = set()

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(self._content)

    def holds_object_with(self, key: str, field: str) -> bool:
        content = self._content.get(key)
        return isinstance(content, dict) and field in content

    def holds_object(self, key: str) -> bool:
        return isinstance(self._content.get(key), dict)

    def report(self, code: DiagnosticCode, key: str, message: str, expected: str) -> None:
        self._diagnostics.append(Diagnostic(code, self._pointer_to(key), message, expected))

    def text(self, key: str, expected: str) -> str:
        return self._as_text(key, self._required(key, expected), expected)

    def optional_text(self, key: str, expected: str) -> str | None:
        value = self._optional(key)
        return None if value is None else self._as_text(key, value, expected)

    def number(self, key: str, expected: str) -> ExactNumber:
        return self._as_number(key, self._required(key, expected), expected)

    def optional_number(self, key: str, expected: str) -> ExactNumber | None:
        value = self._optional(key)
        return None if value is None else self._as_number(key, value, expected)

    def nested(self, key: str, expected: str) -> Self:
        return self._as_reader(key, self._required(key, expected), expected)

    def optional_nested(self, key: str, expected: str) -> Self | None:
        value = self._optional(key)
        return None if value is None else self._as_reader(key, value, expected)

    def reject_unknown_fields(self) -> None:
        known = ", ".join(sorted(self._read))
        for key in self._content:
            if key not in self._read:
                self.report(
                    DiagnosticCode.UNEXPECTED_FIELD,
                    key,
                    f"O campo {quote_user_text(key)} não é reconhecido.",
                    f"um destes campos: {known}",
                )

    def _required(self, key: str, expected: str) -> object:
        self._read.add(key)
        if key not in self._content:
            self.report(
                DiagnosticCode.MISSING_FIELD,
                key,
                f"O campo obrigatório {quote_user_text(key)} está ausente.",
                expected,
            )
            return _MISSING
        return self._content[key]

    def _optional(self, key: str) -> object | None:
        self._read.add(key)
        return self._content.get(key)

    def _as_text(self, key: str, value: object, expected: str) -> str:
        if value is _MISSING:
            return ""
        if not isinstance(value, str) or not value or len(value) > MAX_TEXT_LENGTH:
            self.report(
                DiagnosticCode.INVALID_TYPE,
                key,
                f"O campo deve ser um texto não vazio de até {MAX_TEXT_LENGTH} caracteres.",
                expected,
            )
            return ""
        return value

    def _as_number(self, key: str, value: object, expected: str) -> ExactNumber:
        if value is _MISSING:
            return _PLACEHOLDER_NUMBER
        if isinstance(value, NumberToken):
            literal = value.literal
        elif isinstance(value, str):
            literal = value
        else:
            self.report(DiagnosticCode.INVALID_TYPE, key, "O campo deve ser um número.", expected)
            return _PLACEHOLDER_NUMBER
        try:
            return ExactNumber(parse_exact_number(literal), literal)
        except NumberLiteralError as error:
            self.report(
                error.code,
                key,
                f"O valor {quote_user_text(literal)} não foi aceito: {error.reason}.",
                NUMBER_EXPECTATION,
            )
            return _PLACEHOLDER_NUMBER

    def _as_reader(self, key: str, value: object, expected: str) -> Self:
        if isinstance(value, dict):
            return type(self)(value, self._pointer_to(key), self._diagnostics)
        if value is not _MISSING:
            self.report(DiagnosticCode.INVALID_TYPE, key, "O campo deve ser um objeto.", expected)
        return type(self)({}, self._pointer_to(key), [])

    def _pointer_to(self, key: str) -> str:
        return self._pointer + json_pointer(key)
