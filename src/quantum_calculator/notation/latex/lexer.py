from quantum_calculator.domain.diagnostics import DiagnosticCode, quote_user_text
from quantum_calculator.domain.expressions import SourceSpan
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.notation.numbers import PLAIN_NUMBER, scan_number
from quantum_calculator.notation.tokens import Token, TokenKind, end_token
from quantum_calculator.notation.vocabulary import (
    GREEK_LETTERS,
    NAME_EXPECTATION,
    PI,
    canonical_symbol_name,
)

FRACTION = "frac"
SQUARE_ROOT = "sqrt"
INTEGRAL = "int"
PARTIAL = "partial"

_OPERATORS = {
    "+": TokenKind.PLUS,
    "-": TokenKind.MINUS,
    "/": TokenKind.SLASH,
    "^": TokenKind.CARET,
    "_": TokenKind.UNDERSCORE,
    "(": TokenKind.LEFT_PARENTHESIS,
    ")": TokenKind.RIGHT_PARENTHESIS,
    "{": TokenKind.LEFT_BRACE,
    "}": TokenKind.RIGHT_BRACE,
    ",": TokenKind.COMMA,
    "=": TokenKind.EQUALS,
    "'": TokenKind.PRIME,
}
_BAR_BY_SIZE_COMMAND = {"left": TokenKind.LEFT_BAR, "right": TokenKind.RIGHT_BAR}
_STRUCTURAL_COMMANDS = frozenset({FRACTION, SQUARE_ROOT, INTEGRAL, PARTIAL})
_FUNCTION_COMMANDS = frozenset({"sin", "cos", "tan", "exp", "ln"})
_SPACING_COMMANDS = frozenset({"quad", "qquad"})
_SPACING_SYMBOLS = frozenset(",;:! ")
_MULTIPLICATION = "cdot"
_ROMAN = "mathrm"
_ESCAPE = "\\"
_BAR = "|"
_GROUP_OPEN = "{"
_GROUP_CLOSE = "}"
_SUBSCRIPT_MARK = "_"
_DIGITS = frozenset("0123456789")
_COMMANDS_EXPECTATION = (
    "um destes comandos: \\frac, \\sqrt, \\int, \\partial, \\cdot, \\pi, \\sin, \\cos, \\tan, "
    "\\exp, \\ln, \\left, \\right, \\mathrm e letras gregas"
)
_ALPHABET = "números, letras, comandos aceitos, + - / ^ _ ( ) { } = e '"


def tokenize_latex(text: str) -> tuple[Token, ...]:
    tokens: list[Token] = []
    position = 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        token, position = _scan(text, position)
        if token is not None:
            tokens.append(token)
    tokens.append(end_token(text))
    return tuple(tokens)


def _scan(text: str, position: int) -> tuple[Token | None, int]:
    character = text[position]
    if character == _ESCAPE:
        return _command(text, position)
    if character in _DIGITS:
        number = scan_number(text, position, PLAIN_NUMBER)
        return number, number.span.end
    if character.isalpha():
        return _name(text, position, position + 1, character)
    span = SourceSpan(position, position + 1)
    kind = _OPERATORS.get(character)
    if kind is None:
        expected = "\\left| e \\right| para o módulo" if character == _BAR else _ALPHABET
        raise StatementError(
            DiagnosticCode.UNEXPECTED_CHARACTER,
            span,
            f"O caractere {quote_user_text(character)} não faz parte do subconjunto de LaTeX.",
            expected,
        )
    return Token(kind, character, span), position + 1


def _command(text: str, position: int) -> tuple[Token | None, int]:
    start = position + 1
    if text[start : start + 1] in _SPACING_SYMBOLS and start < len(text):
        return None, start + 1
    end = start
    while end < len(text) and text[end].isascii() and text[end].isalpha():
        end += 1
    name = text[start:end]
    span = SourceSpan(position, min(len(text), max(end, start + 1)))
    if name in _SPACING_COMMANDS:
        return None, end
    bar = _BAR_BY_SIZE_COMMAND.get(name)
    if bar is not None:
        if text[end : end + 1] == _BAR:
            return Token(bar, text[position : end + 1], SourceSpan(position, end + 1)), end + 1
        return None, end
    if name == _MULTIPLICATION:
        return Token(TokenKind.STAR, name, span), end
    if name == PI or name in _FUNCTION_COMMANDS:
        return Token(TokenKind.IDENTIFIER, name, span), end
    if name in _STRUCTURAL_COMMANDS:
        return Token(TokenKind.COMMAND, name, span), end
    if name in GREEK_LETTERS:
        return _name(text, position, end, GREEK_LETTERS[name])
    if name == _ROMAN:
        return _roman_name(text, position, end)
    raise StatementError(
        DiagnosticCode.UNSUPPORTED_OPERATION,
        span,
        f"O comando {quote_user_text(text[position : span.end])} está fora do subconjunto de "
        "LaTeX aceito.",
        _COMMANDS_EXPECTATION,
    )


def _roman_name(text: str, position: int, end: int) -> tuple[Token, int]:
    closing = text.find(_GROUP_CLOSE, end)
    if text[end : end + 1] != _GROUP_OPEN or closing < 0:
        raise StatementError(
            DiagnosticCode.SYNTAX_ERROR,
            SourceSpan(position, end),
            "\\mathrm precisa de um nome entre chaves.",
            "\\mathrm{nome}",
        )
    return _name(text, position, closing + 1, text[end + 1 : closing])


def _name(text: str, start: int, end: int, base: str) -> tuple[Token, int]:
    subscript, end = _subscript(text, end)
    span = SourceSpan(start, end)
    name = canonical_symbol_name(f"{base}{subscript}")
    if name is None:
        raise StatementError(
            DiagnosticCode.INVALID_SYMBOL_NAME,
            span,
            f"{quote_user_text(text[start:end])} não é um nome de símbolo válido.",
            NAME_EXPECTATION,
        )
    return Token(TokenKind.IDENTIFIER, name, span), end


def _subscript(text: str, position: int) -> tuple[str, int]:
    if text[position : position + 1] != _SUBSCRIPT_MARK:
        return "", position
    start = position + 1
    if text[start : start + 1] == _GROUP_OPEN:
        closing = text.find(_GROUP_CLOSE, start)
        if closing > start:
            return f"{_SUBSCRIPT_MARK}{text[start + 1 : closing]}", closing + 1
    elif text[start : start + 1].isalnum():
        return f"{_SUBSCRIPT_MARK}{text[start]}", start + 1
    raise StatementError(
        DiagnosticCode.SYNTAX_ERROR,
        SourceSpan(position, min(len(text), start + 1)),
        "O subscrito está incompleto.",
        "um subscrito como x_0 ou x_{in}",
    )
