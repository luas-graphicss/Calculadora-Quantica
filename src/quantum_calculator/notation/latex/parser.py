from quantum_calculator.domain.diagnostics import DiagnosticCode, quote_user_text
from quantum_calculator.domain.expressions import (
    BinaryOperation,
    BinaryOperator,
    Derivative,
    DerivativeKind,
    ElementaryFunction,
    Expression,
    FunctionCall,
    Integral,
    IntegrationBounds,
    Symbol,
    UnknownFunction,
)
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.domain.statements import SymbolRole
from quantum_calculator.notation.grammar import FACTOR_EXPECTATION, StatementParser
from quantum_calculator.notation.latex.lexer import FRACTION, INTEGRAL, PARTIAL, SQUARE_ROOT
from quantum_calculator.notation.tokens import Token, TokenKind, join
from quantum_calculator.notation.vocabulary import DIFFERENTIAL

_GROUP_OPEN = "{ abrindo o grupo"
_GROUP_CLOSE = "} fechando o grupo"
_DIFFERENTIAL_EXPECTATION = "o diferencial, como dx, fechando a integral"
_OPERATOR_FORM = "\\frac{d}{dx}\\left( ... \\right), ou \\frac{dy}{dt} para uma função declarada"
_FACTOR_COMMANDS = frozenset({FRACTION, SQUARE_ROOT, INTEGRAL})
_FACTOR_STARTS = (TokenKind.LEFT_PARENTHESIS, TokenKind.LEFT_BRACE, TokenKind.LEFT_BAR)


class LatexStatementParser(StatementParser):
    def _starts_factor(self, token: Token) -> bool:
        if token.kind is TokenKind.IDENTIFIER:
            return token.text != DIFFERENTIAL
        if token.kind is TokenKind.COMMAND:
            return token.text in _FACTOR_COMMANDS
        return token.kind in _FACTOR_STARTS

    def _primary(self) -> Expression:
        token = self._peek()
        if token.kind is TokenKind.NUMBER:
            return self._number(self._advance())
        if token.kind is TokenKind.LEFT_PARENTHESIS:
            return self._group(TokenKind.RIGHT_PARENTHESIS)
        if token.kind is TokenKind.LEFT_BRACE:
            return self._group(TokenKind.RIGHT_BRACE)
        if token.kind is TokenKind.LEFT_BAR:
            argument, span = self._delimited(TokenKind.RIGHT_BAR)
            return FunctionCall(ElementaryFunction.ABS, argument, span)
        if token.kind is TokenKind.IDENTIFIER:
            return self._named(self._advance())
        if token.kind is not TokenKind.COMMAND or token.text == PARTIAL:
            raise self._unexpected(token, FACTOR_EXPECTATION)
        self._advance()
        if token.text == FRACTION:
            return self._fraction(token)
        if token.text == SQUARE_ROOT:
            return self._square_root(token)
        return self._integral(token)

    def _fraction(self, command: Token) -> Expression:
        opening = self._expect(TokenKind.LEFT_BRACE, _GROUP_OPEN)
        if self._differential_kind(self._peek()) is not None:
            return self._leibniz(command)
        with self._nested(opening):
            numerator = self._sum()
            self._expect(TokenKind.RIGHT_BRACE, _GROUP_CLOSE)
            self._expect(TokenKind.LEFT_BRACE, _GROUP_OPEN)
            denominator = self._sum()
        closing = self._expect(TokenKind.RIGHT_BRACE, _GROUP_CLOSE)
        span = join(command.span, closing.span)
        return BinaryOperation(BinaryOperator.DIVIDE, numerator, denominator, span)

    def _leibniz(self, command: Token) -> Expression:
        kind = self._expect_differential()
        order = self._optional_order()
        target = self._advance() if self._peek().kind is TokenKind.IDENTIFIER else None
        self._expect(TokenKind.RIGHT_BRACE, _GROUP_CLOSE)
        self._expect(TokenKind.LEFT_BRACE, _GROUP_OPEN)
        denominator_kind = self._expect_differential()
        variable = self._declared_name()
        denominator_order = self._optional_order()
        closing = self._expect(TokenKind.RIGHT_BRACE, _GROUP_CLOSE)
        operator_span = join(command.span, closing.span)
        if kind is not denominator_kind or order != denominator_order:
            raise StatementError(
                DiagnosticCode.SYNTAX_ERROR,
                operator_span,
                "O numerador e o denominador do operador de derivação não combinam.",
                _OPERATOR_FORM,
            )
        if target is None:
            return self._operator_derivative(kind, variable, order, command)
        return self._function_derivative(kind, target, variable, order, command, closing)

    def _operator_derivative(
        self, kind: DerivativeKind, variable: Token, order: int, command: Token
    ) -> Expression:
        opening = self._peek()
        if opening.kind is not TokenKind.LEFT_PARENTHESIS:
            raise StatementError(
                DiagnosticCode.AMBIGUOUS_ARGUMENT,
                join(command.span, opening.span),
                "O operando da derivada não está delimitado, então não se sabe onde ele termina.",
                _OPERATOR_FORM,
            )
        body, span = self._delimited(TokenKind.RIGHT_PARENTHESIS)
        return Derivative(kind, body, variable.text, order, join(command.span, span))

    def _function_derivative(
        self,
        kind: DerivativeKind,
        target: Token,
        variable: Token,
        order: int,
        command: Token,
        closing: Token,
    ) -> Expression:
        symbol = self._symbols.get(target.text)
        if symbol is None:
            raise self._undeclared(target)
        if symbol.role is not SymbolRole.FUNCTION or kind is DerivativeKind.PARTIAL:
            raise StatementError(
                DiagnosticCode.NOT_A_FUNCTION,
                target.span,
                f"{quote_user_text(target.text)} não pode ser derivado nesta forma: ela vale "
                "para a derivada ordinária de um símbolo declarado como função.",
                _OPERATOR_FORM,
            )
        if symbol.argument != variable.text:
            raise StatementError(
                DiagnosticCode.NOT_A_VARIABLE,
                variable.span,
                f"{symbol.name} foi declarada como função de {symbol.argument}, não de "
                f"{variable.text}.",
                f"a derivada em relação a {symbol.argument}",
            )
        argument = Symbol(variable.text, variable.span)
        return UnknownFunction(symbol.name, order, argument, join(command.span, closing.span))

    def _square_root(self, command: Token) -> Expression:
        if self._peek().kind is not TokenKind.LEFT_BRACE:
            raise self._unexpected(self._peek(), _GROUP_OPEN)
        argument, span = self._delimited(TokenKind.RIGHT_BRACE)
        return FunctionCall(ElementaryFunction.SQRT, argument, join(command.span, span))

    def _integral(self, command: Token) -> Expression:
        bounds = None
        if self._peek().kind is TokenKind.UNDERSCORE:
            self._advance()
            lower = self._bound()
            self._expect(TokenKind.CARET, "o limite superior, como ^{b}")
            bounds = IntegrationBounds(lower, self._bound())
        with self._nested(command):
            body = self._sum()
        marker = self._peek()
        if marker.kind is not TokenKind.IDENTIFIER or marker.text != DIFFERENTIAL:
            raise self._unexpected(marker, _DIFFERENTIAL_EXPECTATION)
        self._advance()
        variable = self._declared_name()
        return Integral(body, variable.text, bounds, join(command.span, variable.span))

    def _bound(self) -> Expression:
        if self._peek().kind is TokenKind.LEFT_BRACE:
            return self._group(TokenKind.RIGHT_BRACE)
        return self._primary()

    def _expect_differential(self) -> DerivativeKind:
        token = self._peek()
        kind = self._differential_kind(token)
        if kind is None:
            raise self._unexpected(token, _OPERATOR_FORM)
        self._advance()
        return kind

    def _differential_kind(self, token: Token) -> DerivativeKind | None:
        if token.kind is TokenKind.IDENTIFIER and token.text == DIFFERENTIAL:
            return DerivativeKind.ORDINARY
        if token.kind is TokenKind.COMMAND and token.text == PARTIAL:
            return DerivativeKind.PARTIAL
        return None

    def _optional_order(self) -> int:
        if self._peek().kind is not TokenKind.CARET:
            return 1
        self._advance()
        if self._peek().kind is not TokenKind.LEFT_BRACE:
            return self._order(self._expect(TokenKind.NUMBER, "a ordem da derivada"))
        self._advance()
        order = self._order(self._expect(TokenKind.NUMBER, "a ordem da derivada"))
        self._expect(TokenKind.RIGHT_BRACE, _GROUP_CLOSE)
        return order
