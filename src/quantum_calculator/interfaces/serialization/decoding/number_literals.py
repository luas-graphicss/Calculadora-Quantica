import re
from fractions import Fraction

from quantum_calculator.domain.diagnostics import DiagnosticCode

MAX_LITERAL_LENGTH = 64
MAX_EXPONENT_MAGNITUDE = 99
NUMBER_EXPECTATION = (
    f"número finito, decimal ou fração p/q, com até {MAX_LITERAL_LENGTH} caracteres "
    f"e expoente de módulo até {MAX_EXPONENT_MAGNITUDE}"
)

_DECIMAL = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE](?P<exponent>[+-]?\d+))?")
_RATIONAL = re.compile(r"(?P<numerator>[+-]?\d+)/(?P<denominator>\d+)")
_NON_FINITE_WORDS = frozenset({"nan", "inf", "infinity"})


class NumberLiteralError(ValueError):
    def __init__(self, code: DiagnosticCode, reason: str) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason


def parse_exact_number(literal: str) -> Fraction:
    if len(literal) > MAX_LITERAL_LENGTH:
        raise NumberLiteralError(
            DiagnosticCode.NUMBER_OUT_OF_RANGE,
            f"o literal tem mais de {MAX_LITERAL_LENGTH} caracteres",
        )
    if literal.lstrip("+-").lower() in _NON_FINITE_WORDS:
        raise NumberLiteralError(DiagnosticCode.NON_FINITE_NUMBER, "o valor não é finito")
    rational = _RATIONAL.fullmatch(literal)
    if rational is not None:
        return _parse_rational(rational)
    decimal = _DECIMAL.fullmatch(literal)
    if decimal is None:
        raise NumberLiteralError(
            DiagnosticCode.MALFORMED_NUMBER,
            "o texto não é um número decimal nem uma fração p/q",
        )
    exponent = decimal.group("exponent")
    if exponent is not None and abs(int(exponent)) > MAX_EXPONENT_MAGNITUDE:
        raise NumberLiteralError(
            DiagnosticCode.NUMBER_OUT_OF_RANGE,
            f"o expoente passa de {MAX_EXPONENT_MAGNITUDE} em módulo",
        )
    return Fraction(literal)


def _parse_rational(rational: re.Match[str]) -> Fraction:
    denominator = int(rational.group("denominator"))
    if denominator == 0:
        raise NumberLiteralError(DiagnosticCode.MALFORMED_NUMBER, "o denominador da fração é zero")
    return Fraction(int(rational.group("numerator")), denominator)
