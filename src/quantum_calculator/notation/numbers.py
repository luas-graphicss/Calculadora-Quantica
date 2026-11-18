import re
from fractions import Fraction

from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.expressions import SourceSpan
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.notation.limits import MAX_EXPONENT_MAGNITUDE, MAX_NUMBER_LENGTH
from quantum_calculator.notation.tokens import Token, TokenKind

SCIENTIFIC_NUMBER = re.compile(r"\d+(?:\.\d+)?(?:[eE](?P<exponent>[+-]?\d+))?", re.ASCII)
PLAIN_NUMBER = re.compile(r"\d+(?:\.\d+)?", re.ASCII)
DECIMAL_POINT = "."

_NUMBER_EXPECTATION = (
    f"número decimal com ponto, como 1.5 ou 0.25, com até {MAX_NUMBER_LENGTH} caracteres e "
    f"expoente de módulo até {MAX_EXPONENT_MAGNITUDE}"
)


def scan_number(text: str, position: int, pattern: re.Pattern[str]) -> Token:
    match = pattern.match(text, position)
    if match is None:
        raise _malformed(SourceSpan(position, position + 1))
    end = match.end()
    if text[end : end + 1] == DECIMAL_POINT:
        raise _malformed(SourceSpan(position, end + 1))
    span = SourceSpan(position, end)
    exponent = match.groupdict().get("exponent")
    is_too_long = end - position > MAX_NUMBER_LENGTH
    if is_too_long or (exponent is not None and abs(int(exponent)) > MAX_EXPONENT_MAGNITUDE):
        raise StatementError(
            DiagnosticCode.NUMBER_OUT_OF_RANGE,
            span,
            "O número passa do tamanho ou do expoente aceitos.",
            _NUMBER_EXPECTATION,
        )
    return Token(TokenKind.NUMBER, match.group(), span)


def decimal_literal(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    places = 0
    scale = 1
    while scale % value.denominator:
        places += 1
        scale *= 10
        if places > MAX_EXPONENT_MAGNITUDE + MAX_NUMBER_LENGTH:
            raise ValueError(f"{value} has no terminating decimal expansion")
    digits = str(value.numerator * scale // value.denominator).rjust(places + 1, "0")
    return f"{digits[:-places]}.{digits[-places:]}"


def _malformed(span: SourceSpan) -> StatementError:
    return StatementError(
        DiagnosticCode.MALFORMED_NUMBER,
        span,
        "O número está malformado: o ponto decimal precisa de dígitos dos dois lados.",
        _NUMBER_EXPECTATION,
    )
