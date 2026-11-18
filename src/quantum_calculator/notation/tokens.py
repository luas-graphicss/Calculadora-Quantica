from dataclasses import dataclass
from enum import StrEnum

from quantum_calculator.domain.expressions import SourceSpan


class TokenKind(StrEnum):
    NUMBER = "number"
    IDENTIFIER = "identifier"
    COMMAND = "command"
    PLUS = "plus"
    MINUS = "minus"
    STAR = "star"
    SLASH = "slash"
    CARET = "caret"
    UNDERSCORE = "underscore"
    LEFT_PARENTHESIS = "left_parenthesis"
    RIGHT_PARENTHESIS = "right_parenthesis"
    LEFT_BRACE = "left_brace"
    RIGHT_BRACE = "right_brace"
    LEFT_BAR = "left_bar"
    RIGHT_BAR = "right_bar"
    COMMA = "comma"
    EQUALS = "equals"
    PRIME = "prime"
    END = "end"


@dataclass(frozen=True, slots=True)
class Token:
    kind: TokenKind
    text: str
    span: SourceSpan


def join(first: SourceSpan, last: SourceSpan) -> SourceSpan:
    return SourceSpan(first.start, last.end)


def end_token(text: str) -> Token:
    return Token(TokenKind.END, "", SourceSpan(len(text), len(text)))
