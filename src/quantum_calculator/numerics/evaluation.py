import math
from collections.abc import Callable, Mapping

import numpy
from numpy.typing import NDArray

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

type Samples = NDArray[numpy.float64]
type Binding = float | Samples

_FUNCTIONS: dict[ElementaryFunction, Callable[[Samples], Samples]] = {
    ElementaryFunction.SIN: numpy.sin,
    ElementaryFunction.COS: numpy.cos,
    ElementaryFunction.TAN: numpy.tan,
    ElementaryFunction.EXP: numpy.exp,
    ElementaryFunction.LN: numpy.log,
    ElementaryFunction.SQRT: numpy.sqrt,
    ElementaryFunction.ABS: numpy.abs,
}
_OPERATIONS: dict[BinaryOperator, Callable[[Samples, Samples], Samples]] = {
    BinaryOperator.ADD: numpy.add,
    BinaryOperator.SUBTRACT: numpy.subtract,
    BinaryOperator.MULTIPLY: numpy.multiply,
    BinaryOperator.DIVIDE: numpy.divide,
    BinaryOperator.POWER: numpy.power,
}


class NonFiniteValueError(ArithmeticError):
    pass


def evaluate(expression: Expression, bindings: Mapping[str, Binding]) -> Samples:
    with numpy.errstate(all="ignore"):
        values = _values(expression, bindings)
    if not numpy.all(numpy.isfinite(values)):
        raise NonFiniteValueError("the expression is not finite at a sampled point")
    return values


def _values(expression: Expression, bindings: Mapping[str, Binding]) -> Samples:
    match expression:
        case Number():
            return _constant(float(expression.value))
        case Pi():
            return _constant(math.pi)
        case Symbol():
            return numpy.asarray(bindings[expression.name], dtype=numpy.float64)
        case Negation():
            return numpy.negative(_values(expression.operand, bindings))
        case BinaryOperation():
            left = _values(expression.left, bindings)
            return _OPERATIONS[expression.operator](left, _values(expression.right, bindings))
        case FunctionCall():
            return _FUNCTIONS[expression.function](_values(expression.argument, bindings))
        case UnknownFunction():
            return _unknown(expression, bindings)
        case Derivative() | Integral():
            raise TypeError("derivatives and integrals have no pointwise numerical value")


def _unknown(reference: UnknownFunction, bindings: Mapping[str, Binding]) -> Samples:
    if reference.order != 0:
        raise TypeError(f"the derivative of {reference.name} has no pointwise numerical value")
    return numpy.asarray(bindings[reference.name], dtype=numpy.float64)


def _constant(value: float) -> Samples:
    return numpy.asarray(value, dtype=numpy.float64)
