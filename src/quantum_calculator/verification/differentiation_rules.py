import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.algebra.reader import read_expression
from quantum_calculator.domain.expression_traversal import symbol_names
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


def derive_by_rules(derivative: Derivative, builder: ExpressionBuilder) -> sympy.Expr:
    current = derivative.body
    result = _derive(current, derivative.variable, builder)
    for _ in range(derivative.order - 1):
        current = read_expression(result)
        result = _derive(current, derivative.variable, builder)
    return result


def _derive(expression: Expression, variable: str, builder: ExpressionBuilder) -> sympy.Expr:
    match expression:
        case Number() | Pi():
            return sympy.Integer(0)
        case Symbol():
            return sympy.Integer(1 if expression.name == variable else 0)
        case Negation():
            return -_derive(expression.operand, variable, builder)
        case BinaryOperation():
            return _operation(expression, variable, builder)
        case FunctionCall():
            return _chain(expression, variable, builder)
        case UnknownFunction() | Derivative() | Integral():
            raise TypeError("the differentiation rules apply to explicit expressions only")


def _operation(operation: BinaryOperation, variable: str, builder: ExpressionBuilder) -> sympy.Expr:
    left = builder.build(operation.left)
    right = builder.build(operation.right)
    left_rate = _derive(operation.left, variable, builder)
    right_rate = _derive(operation.right, variable, builder)
    if operation.operator is BinaryOperator.ADD:
        return left_rate + right_rate
    if operation.operator is BinaryOperator.SUBTRACT:
        return left_rate - right_rate
    if operation.operator is BinaryOperator.MULTIPLY:
        return left_rate * right + left * right_rate
    if operation.operator is BinaryOperator.DIVIDE:
        return (left_rate * right - left * right_rate) / right**2
    if variable not in symbol_names(operation.right):
        return right * left ** (right - 1) * left_rate
    return left**right * (right_rate * sympy.log(left) + right * left_rate / left)


def _chain(call: FunctionCall, variable: str, builder: ExpressionBuilder) -> sympy.Expr:
    inner = builder.build(call.argument)
    inner_rate = _derive(call.argument, variable, builder)
    if call.function is ElementaryFunction.SIN:
        return sympy.cos(inner) * inner_rate
    if call.function is ElementaryFunction.COS:
        return -sympy.sin(inner) * inner_rate
    if call.function is ElementaryFunction.TAN:
        return (1 + sympy.tan(inner) ** 2) * inner_rate
    if call.function is ElementaryFunction.EXP:
        return sympy.exp(inner) * inner_rate
    if call.function is ElementaryFunction.LN:
        return inner_rate / inner
    if call.function is ElementaryFunction.SQRT:
        return inner_rate / (2 * sympy.sqrt(inner))
    return inner / sympy.Abs(inner) * inner_rate
