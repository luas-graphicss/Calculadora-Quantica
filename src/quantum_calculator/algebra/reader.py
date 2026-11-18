from fractions import Fraction

import sympy
from sympy.core.function import AppliedUndef

from quantum_calculator.domain.expressions import (
    BinaryOperation,
    BinaryOperator,
    ElementaryFunction,
    Expression,
    FunctionCall,
    Negation,
    Number,
    Pi,
    Symbol,
    UnknownFunction,
)

_FUNCTIONS = {
    sympy.sin: ElementaryFunction.SIN,
    sympy.cos: ElementaryFunction.COS,
    sympy.tan: ElementaryFunction.TAN,
    sympy.exp: ElementaryFunction.EXP,
    sympy.log: ElementaryFunction.LN,
    sympy.Abs: ElementaryFunction.ABS,
}
_HALF = sympy.Rational(1, 2)
_ONE = Number(Fraction(1))


class UnregisteredOperationError(ValueError):
    def __init__(self, operation: str) -> None:
        super().__init__(f"{operation} is not a registered operation")
        self.operation = operation


def read_expression(value: sympy.Expr) -> Expression:
    if value.is_Rational:
        return _rational(value)
    if value is sympy.pi:
        return Pi()
    if value is sympy.E:
        return FunctionCall(ElementaryFunction.EXP, _ONE)
    if value.is_Symbol:
        return Symbol(value.name)
    if value.is_Add:
        return _sum(value)
    if value.is_Mul:
        return _product(value)
    function = _FUNCTIONS.get(value.func)
    if function is not None:
        return FunctionCall(function, read_expression(value.args[0]))
    if value.is_Pow:
        return _power(value)
    if isinstance(value, AppliedUndef):
        return UnknownFunction(value.func.__name__, 0, read_expression(value.args[0]))
    if value.func is sympy.sign:
        argument = read_expression(value.args[0])
        modulus = FunctionCall(ElementaryFunction.ABS, argument)
        return BinaryOperation(BinaryOperator.DIVIDE, argument, modulus)
    raise UnregisteredOperationError(value.func.__name__)


def _rational(value: sympy.Rational) -> Expression:
    numerator, denominator = abs(int(value.p)), int(value.q)
    magnitude: Expression = Number(Fraction(numerator))
    if denominator != 1:
        magnitude = BinaryOperation(BinaryOperator.DIVIDE, magnitude, Number(Fraction(denominator)))
    return Negation(magnitude) if value.is_negative else magnitude


def _sum(value: sympy.Add) -> Expression:
    first, *others = value.as_ordered_terms()
    total = read_expression(first)
    for term in others:
        if term.could_extract_minus_sign():
            total = BinaryOperation(BinaryOperator.SUBTRACT, total, read_expression(-term))
        else:
            total = BinaryOperation(BinaryOperator.ADD, total, read_expression(term))
    return total


def _product(value: sympy.Mul) -> Expression:
    coefficient, _ = value.as_coeff_Mul()
    if coefficient.is_negative:
        return Negation(read_expression(-value))
    numerator: list[Expression] = []
    denominator: list[Expression] = []
    for factor in value.as_ordered_factors():
        if factor.is_Rational:
            numerator += [] if factor.p == 1 else [Number(Fraction(int(factor.p)))]
            denominator += [] if factor.q == 1 else [Number(Fraction(int(factor.q)))]
        elif _is_reciprocal_power(factor):
            denominator.append(read_expression(factor.base ** (-factor.exp)))
        else:
            numerator.append(read_expression(factor))
    top = _multiply(numerator) if numerator else _ONE
    if not denominator:
        return top
    return BinaryOperation(BinaryOperator.DIVIDE, top, _multiply(denominator))


def _power(value: sympy.Pow) -> Expression:
    base, exponent = value.as_base_exp()
    if exponent == _HALF:
        return FunctionCall(ElementaryFunction.SQRT, read_expression(base))
    if _is_reciprocal_power(value):
        return BinaryOperation(BinaryOperator.DIVIDE, _ONE, read_expression(base ** (-exponent)))
    return BinaryOperation(BinaryOperator.POWER, read_expression(base), read_expression(exponent))


def _is_reciprocal_power(value: sympy.Expr) -> bool:
    return bool(value.is_Pow and value.exp.is_Rational and value.exp.is_negative)


def _multiply(factors: list[Expression]) -> Expression:
    product = factors[0]
    for factor in factors[1:]:
        product = BinaryOperation(BinaryOperator.MULTIPLY, product, factor)
    return product
