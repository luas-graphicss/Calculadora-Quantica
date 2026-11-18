from quantum_calculator.domain.expressions import (
    Derivative,
    DerivativeKind,
    Expression,
    Integral,
    IntegrationBounds,
)
from quantum_calculator.notation.grammar import FACTOR_EXPECTATION, StatementParser
from quantum_calculator.notation.tokens import Token, TokenKind, join
from quantum_calculator.notation.vocabulary import DERIVATIVE_OPERATORS, INTEGRAL_OPERATOR

_OPENING = "( depois do nome do operador"
_SEPARATOR = "uma vírgula entre os argumentos"
_CLOSING = ") no fim dos argumentos"
_FACTOR_STARTS = (TokenKind.IDENTIFIER, TokenKind.LEFT_PARENTHESIS)


class TextStatementParser(StatementParser):
    def _starts_factor(self, token: Token) -> bool:
        return token.kind in _FACTOR_STARTS

    def _primary(self) -> Expression:
        token = self._peek()
        if token.kind is TokenKind.NUMBER:
            return self._number(self._advance())
        if token.kind is TokenKind.LEFT_PARENTHESIS:
            return self._group(TokenKind.RIGHT_PARENTHESIS)
        if token.kind is not TokenKind.IDENTIFIER:
            raise self._unexpected(token, FACTOR_EXPECTATION)
        self._advance()
        kind = DERIVATIVE_OPERATORS.get(token.text)
        if kind is not None:
            return self._derivative(kind, token)
        if token.text == INTEGRAL_OPERATOR:
            return self._integral(token)
        return self._named(token)

    def _derivative(self, kind: DerivativeKind, operator: Token) -> Expression:
        opening = self._expect(TokenKind.LEFT_PARENTHESIS, _OPENING)
        with self._nested(opening):
            body = self._sum()
            self._expect(TokenKind.COMMA, _SEPARATOR)
            variable = self._declared_name()
            order = 1
            if self._peek().kind is TokenKind.COMMA:
                self._advance()
                order = self._order(self._expect(TokenKind.NUMBER, "a ordem da derivada"))
        closing = self._expect(TokenKind.RIGHT_PARENTHESIS, _CLOSING)
        return Derivative(kind, body, variable.text, order, join(operator.span, closing.span))

    def _integral(self, operator: Token) -> Expression:
        opening = self._expect(TokenKind.LEFT_PARENTHESIS, _OPENING)
        with self._nested(opening):
            body = self._sum()
            self._expect(TokenKind.COMMA, _SEPARATOR)
            variable = self._declared_name()
            bounds = None
            if self._peek().kind is TokenKind.COMMA:
                self._advance()
                lower = self._sum()
                self._expect(TokenKind.COMMA, "o limite superior depois do inferior")
                bounds = IntegrationBounds(lower, self._sum())
        closing = self._expect(TokenKind.RIGHT_PARENTHESIS, _CLOSING)
        return Integral(body, variable.text, bounds, join(operator.span, closing.span))
