from quantum_calculator.domain.diagnostics import DiagnosticCode, quote_user_text
from quantum_calculator.domain.expressions import ElementaryFunction, SourceSpan
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.notation.numbers import DECIMAL_POINT, SCIENTIFIC_NUMBER, scan_number
from quantum_calculator.notation.tokens import Token, TokenKind, end_token
from quantum_calculator.notation.vocabulary import NAME_EXPECTATION, canonical_symbol_name

_OPERATORS = {
    "+": TokenKind.PLUS,
    "-": TokenKind.MINUS,
    "\N{MINUS SIGN}": TokenKind.MINUS,
    "*": TokenKind.STAR,
    "\N{MIDDLE DOT}": TokenKind.STAR,
    "\N{DOT OPERATOR}": TokenKind.STAR,
    "/": TokenKind.SLASH,
    "^": TokenKind.CARET,
    "(": TokenKind.LEFT_PARENTHESIS,
    ")": TokenKind.RIGHT_PARENTHESIS,
    ",": TokenKind.COMMA,
    "=": TokenKind.EQUALS,
    "'": TokenKind.PRIME,
    "\N{PRIME}": TokenKind.PRIME,
}
_SUPERSCRIPT_DIGITS = {
    "\N{SUPERSCRIPT ZERO}": "0",
    "\N{SUPERSCRIPT ONE}": "1",
    "\N{SUPERSCRIPT TWO}": "2",
    "\N{SUPERSCRIPT THREE}": "3",
    "\N{SUPERSCRIPT FOUR}": "4",
    "\N{SUPERSCRIPT FIVE}": "5",
    "\N{SUPERSCRIPT SIX}": "6",
    "\N{SUPERSCRIPT SEVEN}": "7",
    "\N{SUPERSCRIPT EIGHT}": "8",
    "\N{SUPERSCRIPT NINE}": "9",
}
_SQUARE_ROOT = "\N{SQUARE ROOT}"
_DIGITS = frozenset("0123456789")
_SUBSCRIPT_MARK = "_"
_ALPHABET = "números, nomes, + - * / ^ ( ) , = e '"


def tokenize_text(text: str) -> tuple[Token, ...]:
    tokens: list[Token] = []
    position = 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        scanned = _scan(text, position)
        tokens.extend(scanned)
        position = scanned[-1].span.end
    tokens.append(end_token(text))
    return tuple(tokens)


def _scan(text: str, position: int) -> tuple[Token, ...]:
    character = text[position]
    if character in _DIGITS or character == DECIMAL_POINT:
        return (scan_number(text, position, SCIENTIFIC_NUMBER),)
    if character.isalpha():
        return (_identifier(text, position),)
    if character in _SUPERSCRIPT_DIGITS:
        return _superscript(text, position)
    span = SourceSpan(position, position + 1)
    if character == _SQUARE_ROOT:
        return (Token(TokenKind.IDENTIFIER, ElementaryFunction.SQRT.value, span),)
    kind = _OPERATORS.get(character)
    if kind is None:
        raise StatementError(
            DiagnosticCode.UNEXPECTED_CHARACTER,
            span,
            f"O caractere {quote_user_text(character)} não faz parte da notação.",
            _ALPHABET,
        )
    return (Token(kind, character, span),)


def _identifier(text: str, position: int) -> Token:
    end = position
    while end < len(text) and _continues_name(text[end]):
        end += 1
    span = SourceSpan(position, end)
    name = canonical_symbol_name(text[position:end])
    if name is None:
        raise StatementError(
            DiagnosticCode.INVALID_SYMBOL_NAME,
            span,
            f"{quote_user_text(text[position:end])} não é um nome de símbolo válido.",
            NAME_EXPECTATION,
        )
    return Token(TokenKind.IDENTIFIER, name, span)


def _continues_name(character: str) -> bool:
    return character.isalpha() or character in _DIGITS or character == _SUBSCRIPT_MARK


def _superscript(text: str, position: int) -> tuple[Token, ...]:
    end = position
    while end < len(text) and text[end] in _SUPERSCRIPT_DIGITS:
        end += 1
    span = SourceSpan(position, end)
    digits = "".join(_SUPERSCRIPT_DIGITS[character] for character in text[position:end])
    return (Token(TokenKind.CARET, "^", span), Token(TokenKind.NUMBER, digits, span))
