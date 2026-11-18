import operator
from collections.abc import Callable, Iterable

import sympy

from quantum_calculator.domain.expressions import (
    BinaryOperation,
    BinaryOperator,
    Derivative,
    ElementaryFunction,
    Expression,
    FunctionCall,
    Integral,
    Negation,
    Number,
    Pi,
    Symbol,
    UnknownFunction,
)
from quantum_calculator.domain.statements import BoundSymbol, SymbolDomain, SymbolRole

_ASSUMPTIONS: dict[SymbolDomain, dict[str, bool]] = {
    SymbolDomain.REAL: {"real": True},
    SymbolDomain.POSITIVE: {"positive": True},
    SymbolDomain.NEGATIVE: {"negative": True},
    SymbolDomain.NONNEGATIVE: {"nonnegative": True},
    SymbolDomain.NONZERO: {"real": True, "nonzero": True},
}
_FUNCTIONS: dict[ElementaryFunction, Callable[[sympy.Expr], sympy.Expr]] = {
    ElementaryFunction.SIN: sympy.sin,
    ElementaryFunction.COS: sympy.cos,
    ElementaryFunction.TAN: sympy.tan,
    ElementaryFunction.EXP: sympy.exp,
    ElementaryFunction.LN: sympy.log,
    ElementaryFunction.SQRT: sympy.sqrt,
    ElementaryFunction.ABS: sympy.Abs,
}
_OPERATIONS: dict[BinaryOperator, Callable[[sympy.Expr, sympy.Expr], sympy.Expr]] = {
    BinaryOperator.ADD: operator.add,
    BinaryOperator.SUBTRACT: operator.sub,
    BinaryOperator.MULTIPLY: operator.mul,
    BinaryOperator.DIVIDE: operator.truediv,
    BinaryOperator.POWER: operator.pow,
}


class ExpressionBuilder:
    def __init__(self, symbols: Iterable[BoundSymbol], constants: Iterable[str] = ()) -> None:
        self._symbols: dict[str, sympy.Symbol] = {}
        self._functions: dict[str, tuple[sympy.Function, str]] = {}
        for symbol in symbols:
            assumptions = _ASSUMPTIONS[symbol.domain]
            if symbol.role is SymbolRole.FUNCTION and symbol.argument is not None:
                function = sympy.Function(symbol.name, **assumptions)
                self._functions[symbol.name] = (function, symbol.argument)
            else:
                self._symbols[symbol.name] = sympy.Symbol(symbol.name, **assumptions)
        for name in constants:
            self._symbols[name] = sympy.Symbol(name, real=True)

    def symbol(self, name: str) -> sympy.Symbol:
        return self._symbols[name]

    def unknown(self, name: str) -> sympy.Expr:
        function, argument = self._functions[name]
        return function(self._symbols[argument])

    def build(self, expression: Expression) -> sympy.Expr:
        match expression:
            case Number():
                return sympy.Rational(expression.value.numerator, expression.value.denominator)
            case Pi():
                return sympy.pi
            case Symbol():
                return self._symbols[expression.name]
            case Negation():
                return -self.build(expression.operand)
            case BinaryOperation():
                left = self.build(expression.left)
                return _OPERATIONS[expression.operator](left, self.build(expression.right))
            case FunctionCall():
                return _FUNCTIONS[expression.function](self.build(expression.argument))
            case UnknownFunction():
                return self._unknown_function(expression)
            case Derivative():
                variable = self._symbols[expression.variable]
                return sympy.Derivative(self.build(expression.body), (variable, expression.order))
            case Integral():
                return self._integral(expression)

    def _unknown_function(self, reference: UnknownFunction) -> sympy.Expr:
        function, argument = self._functions[reference.name]
        variable = self._symbols[argument]
        applied = function(variable)
        if reference.order > 0:
            applied = sympy.Derivative(applied, (variable, reference.order))
        point = self.build(reference.argument)
        return applied if point == variable else applied.subs(variable, point)

    def _integral(self, integral: Integral) -> sympy.Expr:
        variable = self._symbols[integral.variable]
        body = self.build(integral.body)
        if integral.bounds is None:
            return sympy.Integral(body, variable)
        lower = self.build(integral.bounds.lower)
        return sympy.Integral(body, (variable, lower, self.build(integral.bounds.upper)))
