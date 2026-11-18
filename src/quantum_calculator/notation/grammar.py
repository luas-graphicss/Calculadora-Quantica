from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import replace
from fractions import Fraction

from quantum_calculator.domain.diagnostics import DiagnosticCode, quote_user_text
from quantum_calculator.domain.expressions import (
    BinaryOperation,
    BinaryOperator,
    ElementaryFunction,
    Equation,
    Expression,
    FunctionCall,
    Negation,
    Number,
    Pi,
    SourceSpan,
    Statement,
    Symbol,
    UnknownFunction,
)
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.domain.statements import BoundSymbol, SymbolRole
from quantum_calculator.notation.limits import MAX_DERIVATIVE_ORDER, MAX_NESTING_DEPTH
from quantum_calculator.notation.tokens import Token, TokenKind, join
from quantum_calculator.notation.vocabulary import DIFFERENTIAL, ELEMENTARY_FUNCTIONS, PI

FACTOR_EXPECTATION = "um número, um símbolo, uma função ou uma expressão entre parênteses"
ORDER_EXPECTATION = f"ordem inteira entre 1 e {MAX_DERIVATIVE_ORDER}"

_EXPLICIT_PRODUCT_OPERATORS = {
    TokenKind.STAR: BinaryOperator.MULTIPLY,
    TokenKind.SLASH: BinaryOperator.DIVIDE,
}
_SUM_OPERATORS = {TokenKind.PLUS: BinaryOperator.ADD, TokenKind.MINUS: BinaryOperator.SUBTRACT}
_DECIMAL_POINT_HINT = "o separador decimal é o ponto, como em 1.5"


class StatementParser(ABC):
    def __init__(self, tokens: Sequence[Token], symbols: Mapping[str, BoundSymbol]) -> None:
        self._tokens = tokens
        self._symbols = symbols
        self._position = 0
        self._depth = 0

    def parse(self) -> Statement:
        left = self._sum()
        statement: Statement = left
        if self._peek().kind is TokenKind.EQUALS:
            self._advance()
            right = self._sum()
            statement = Equation(left, right, join(left.span, right.span))
        self._expect(TokenKind.END, "o fim do enunciado")
        return statement

    @abstractmethod
    def _primary(self) -> Expression: ...

    @abstractmethod
    def _starts_factor(self, token: Token) -> bool: ...

    def _sum(self) -> Expression:
        left = self._term()
        while (operator := _SUM_OPERATORS.get(self._peek().kind)) is not None:
            self._advance()
            right = self._term()
            left = BinaryOperation(operator, left, right, join(left.span, right.span))
        return left

    def _term(self) -> Expression:
        sign = self._peek()
        if sign.kind is not TokenKind.MINUS:
            return self._product()
        self._advance()
        with self._nested(sign):
            operand = self._term()
        return Negation(operand, join(sign.span, operand.span))

    def _product(self) -> Expression:
        left = self._power()
        chain_start = left.span
        follows_division = False
        while True:
            token = self._peek()
            operator = _EXPLICIT_PRODUCT_OPERATORS.get(token.kind)
            if operator is None and not self._continues_product(token):
                return left
            if follows_division:
                raise StatementError(
                    DiagnosticCode.AMBIGUOUS_DIVISION,
                    join(chain_start, token.span),
                    "Depois de uma divisão, outro fator na mesma sequência admite duas leituras.",
                    "parênteses que fixem a leitura, como (a/b)*c ou a/(b*c)",
                )
            if operator is None:
                operator = BinaryOperator.MULTIPLY
            else:
                self._advance()
            right = self._power()
            left = BinaryOperation(operator, left, right, join(left.span, right.span))
            follows_division = operator is BinaryOperator.DIVIDE

    def _continues_product(self, token: Token) -> bool:
        if token.kind is TokenKind.NUMBER:
            raise StatementError(
                DiagnosticCode.AMBIGUOUS_JUXTAPOSITION,
                token.span,
                "Um número logo depois de outro fator não diz se é produto, potência ou índice.",
                "o operador explícito, como x*2 ou x^2, ou o subscrito x_2",
            )
        return self._starts_factor(token)

    def _power(self) -> Expression:
        base = self._primary()
        if self._peek().kind is not TokenKind.CARET:
            return base
        self._advance()
        exponent = self._exponent()
        following = self._peek()
        if following.kind is TokenKind.CARET:
            raise StatementError(
                DiagnosticCode.AMBIGUOUS_POWER,
                join(base.span, following.span),
                "Uma torre de potências sem agrupamento admite duas leituras.",
                "o agrupamento explícito, como (a^b)^c ou a^(b^c)",
            )
        return BinaryOperation(BinaryOperator.POWER, base, exponent, join(base.span, exponent.span))

    def _exponent(self) -> Expression:
        sign = self._peek()
        if sign.kind is not TokenKind.MINUS:
            return self._primary()
        self._advance()
        operand = self._primary()
        return Negation(operand, join(sign.span, operand.span))

    def _named(self, token: Token) -> Expression:
        if token.text == PI:
            return Pi(token.span)
        function = ELEMENTARY_FUNCTIONS.get(token.text)
        if function is not None:
            return self._function_call(function, token)
        symbol = self._symbols.get(token.text)
        if symbol is None:
            raise self._unknown_name(token)
        if symbol.role is SymbolRole.FUNCTION:
            return self._unknown_function(token, symbol)
        opening = self._peek()
        if opening.kind is TokenKind.LEFT_PARENTHESIS:
            raise StatementError(
                DiagnosticCode.AMBIGUOUS_APPLICATION,
                join(token.span, opening.span),
                f"{quote_user_text(token.text)} seguido de parêntese pode ser um produto ou a "
                "aplicação de uma função.",
                f"o produto explícito {token.text}*(...) ou a declaração de {token.text} com "
                'o papel "function"',
            )
        return Symbol(symbol.name, token.span)

    def _function_call(self, function: ElementaryFunction, name: Token) -> Expression:
        opening = self._peek()
        if opening.kind is not TokenKind.LEFT_PARENTHESIS:
            raise StatementError(
                DiagnosticCode.AMBIGUOUS_ARGUMENT,
                join(name.span, opening.span),
                f"O argumento de {function.value} não está delimitado, então não se sabe "
                "onde ele termina.",
                f"o argumento entre parênteses, como {function.value}(x)",
            )
        argument, span = self._delimited(TokenKind.RIGHT_PARENTHESIS)
        return FunctionCall(function, argument, join(name.span, span))

    def _unknown_function(self, name: Token, symbol: BoundSymbol) -> Expression:
        if symbol.argument is None:
            raise LookupError(f"function symbol {symbol.name} has no declared argument")
        end = name.span
        order = 0
        while self._peek().kind is TokenKind.PRIME:
            end = self._advance().span
            order += 1
        if order > MAX_DERIVATIVE_ORDER:
            raise StatementError(
                DiagnosticCode.NUMBER_OUT_OF_RANGE,
                join(name.span, end),
                f"A ordem de derivação {order} passa do limite.",
                ORDER_EXPECTATION,
            )
        if self._peek().kind is not TokenKind.LEFT_PARENTHESIS:
            argument: Expression = Symbol(symbol.argument, name.span)
            return UnknownFunction(symbol.name, order, argument, join(name.span, end))
        argument, span = self._delimited(TokenKind.RIGHT_PARENTHESIS)
        return UnknownFunction(symbol.name, order, argument, join(name.span, span))

    def _group(self, closing: TokenKind) -> Expression:
        inner, span = self._delimited(closing)
        return replace(inner, span=span)

    def _delimited(self, closing: TokenKind) -> tuple[Expression, SourceSpan]:
        opening = self._advance()
        with self._nested(opening):
            inner = self._sum()
        end = self._expect(closing, "o fechamento do grupo aberto")
        return inner, join(opening.span, end.span)

    def _declared_name(self) -> Token:
        token = self._expect(TokenKind.IDENTIFIER, "o nome de uma variável declarada")
        if token.text not in self._symbols:
            raise self._undeclared(token)
        return token

    def _number(self, token: Token) -> Number:
        return Number(Fraction(token.text), token.span)

    def _order(self, token: Token) -> int:
        order = Fraction(token.text)
        if order.denominator != 1 or not 1 <= order <= MAX_DERIVATIVE_ORDER:
            raise StatementError(
                DiagnosticCode.NUMBER_OUT_OF_RANGE,
                token.span,
                f"A ordem de derivação {quote_user_text(token.text)} não é aceita.",
                ORDER_EXPECTATION,
            )
        return order.numerator

    @contextmanager
    def _nested(self, opening: Token) -> Iterator[None]:
        self._depth += 1
        if self._depth > MAX_NESTING_DEPTH:
            raise StatementError(
                DiagnosticCode.EXPRESSION_TOO_DEEP,
                opening.span,
                f"A expressão tem mais de {MAX_NESTING_DEPTH} níveis de aninhamento.",
                f"até {MAX_NESTING_DEPTH} níveis de parênteses, sinais e funções aninhados",
            )
        yield
        self._depth -= 1

    def _peek(self) -> Token:
        return self._tokens[self._position]

    def _advance(self) -> Token:
        token = self._tokens[self._position]
        self._position += 1
        return token

    def _expect(self, kind: TokenKind, expected: str) -> Token:
        token = self._peek()
        if token.kind is not kind:
            raise self._unexpected(token, expected)
        return self._advance()

    def _unexpected(self, token: Token, expected: str) -> StatementError:
        if token.kind is TokenKind.END:
            return StatementError(
                DiagnosticCode.UNEXPECTED_END,
                token.span,
                "O enunciado termina antes de a expressão estar completa.",
                expected,
            )
        hint = f"{expected}; {_DECIMAL_POINT_HINT}" if token.kind is TokenKind.COMMA else expected
        return StatementError(
            DiagnosticCode.SYNTAX_ERROR,
            token.span,
            f"{quote_user_text(token.text)} não era esperado nesta posição.",
            hint,
        )

    def _unknown_name(self, token: Token) -> StatementError:
        if token.text == DIFFERENTIAL:
            return StatementError(
                DiagnosticCode.SYNTAX_ERROR,
                token.span,
                '"d" é reservado para diferenciais e não pode ser usado como símbolo.',
                "diff(f, x) ou integral(f, x) em texto; \\frac{d}{dx} ou \\int ... dx em LaTeX",
            )
        if self._peek().kind is TokenKind.LEFT_PARENTHESIS:
            return StatementError(
                DiagnosticCode.UNSUPPORTED_OPERATION,
                token.span,
                f"A função {quote_user_text(token.text)} não está entre as operações registradas.",
                f"uma destas funções: {', '.join(ELEMENTARY_FUNCTIONS)}",
            )
        return self._undeclared(token)

    def _undeclared(self, token: Token) -> StatementError:
        declared = ", ".join(self._symbols) or "nenhum"
        return StatementError(
            DiagnosticCode.UNDECLARED_SYMBOL,
            token.span,
            f"O símbolo {quote_user_text(token.text)} aparece no enunciado sem ter sido declarado.",
            f"a declaração do símbolo em symbols; declarados: {declared}",
        )
