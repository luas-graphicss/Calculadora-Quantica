import math
import operator
from collections.abc import Callable, Mapping

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

_FUNCTIONS: dict[ElementaryFunction, Callable[[float], float]] = {
    ElementaryFunction.SIN: math.sin,
    ElementaryFunction.COS: math.cos,
    ElementaryFunction.TAN: math.tan,
    ElementaryFunction.EXP: math.exp,
    ElementaryFunction.LN: math.log,
    ElementaryFunction.SQRT: math.sqrt,
    ElementaryFunction.ABS: math.fabs,
}
_OPERATIONS: dict[BinaryOperator, Callable[[float, float], float]] = {
    BinaryOperator.ADD: operator.add,
    BinaryOperator.SUBTRACT: operator.sub,
    BinaryOperator.MULTIPLY: operator.mul,
    BinaryOperator.DIVIDE: operator.truediv,
    BinaryOperator.POWER: math.pow,
}


class UndefinedValueError(ArithmeticError):
    pass


def evaluate_scalar(expression: Expression, values: Mapping[str, float]) -> float:
    try:
        value = _value(expression, values)
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise UndefinedValueError("the expression has no finite value") from error
    if not math.isfinite(value):
        raise UndefinedValueError("the expression has no finite value")
    return value


def _value(expression: Expression, values: Mapping[str, float]) -> float:
    match expression:
        case Number():
            return float(expression.value)
        case Pi():
            return math.pi
        case Symbol():
            return values[expression.name]
        case Negation():
            return -_value(expression.operand, values)
        case BinaryOperation():
            left = _value(expression.left, values)
            return _OPERATIONS[expression.operator](left, _value(expression.right, values))
        case FunctionCall():
            return _FUNCTIONS[expression.function](_value(expression.argument, values))
        case UnknownFunction() | Derivative() | Integral():
            raise TypeError("only explicit expressions have a scalar value")
