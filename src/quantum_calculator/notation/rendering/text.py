from quantum_calculator.domain.expressions import (
    BinaryOperation,
    BinaryOperator,
    Derivative,
    Equation,
    Expression,
    FunctionCall,
    Integral,
    Negation,
    Number,
    Pi,
    Statement,
    Symbol,
    UnknownFunction,
)
from quantum_calculator.notation.numbers import decimal_literal
from quantum_calculator.notation.vocabulary import (
    INTEGRAL_OPERATOR,
    OPERATOR_BY_DERIVATIVE_KIND,
    PI,
    PRIME,
)

_SUMS = (BinaryOperator.ADD, BinaryOperator.SUBTRACT)
_PRODUCTS = (BinaryOperator.MULTIPLY, BinaryOperator.DIVIDE)
_SIGNS = {
    BinaryOperator.ADD: " + ",
    BinaryOperator.SUBTRACT: " - ",
    BinaryOperator.MULTIPLY: "*",
    BinaryOperator.DIVIDE: "/",
    BinaryOperator.POWER: "^",
}


def render_text(statement: Statement) -> str:
    if isinstance(statement, Equation):
        return f"{_render(statement.left)} = {_render(statement.right)}"
    return _render(statement)


def _render(expression: Expression) -> str:
    match expression:
        case Number():
            return decimal_literal(expression.value)
        case Pi():
            return PI
        case Symbol():
            return expression.name
        case Negation():
            return f"-{_grouped(expression.operand, _is_sum_or_negation(expression.operand))}"
        case BinaryOperation():
            return _operation(expression)
        case FunctionCall():
            return f"{expression.function.value}({_render(expression.argument)})"
        case UnknownFunction():
            primes = PRIME * expression.order
            return f"{expression.name}{primes}({_render(expression.argument)})"
        case Derivative():
            operator = OPERATOR_BY_DERIVATIVE_KIND[expression.kind]
            order = "" if expression.order == 1 else f", {expression.order}"
            return f"{operator}({_render(expression.body)}, {expression.variable}{order})"
        case Integral():
            return _integral(expression)


def _integral(integral: Integral) -> str:
    arguments = [_render(integral.body), integral.variable]
    if integral.bounds is not None:
        arguments += [_render(integral.bounds.lower), _render(integral.bounds.upper)]
    return f"{INTEGRAL_OPERATOR}({', '.join(arguments)})"


def _operation(operation: BinaryOperation) -> str:
    operator = operation.operator
    sign = _SIGNS[operator]
    if operator in _SUMS:
        right = _grouped(operation.right, _is_sum_or_negation(operation.right))
        return f"{_render(operation.left)}{sign}{right}"
    if operator in _PRODUCTS:
        splits_left = _is_sum_or_negation(operation.left) or _is_division(operation.left)
        splits_right = _is_sum_or_negation(operation.right) or _is_product(operation.right)
        left = _grouped(operation.left, splits_left)
        return f"{left}{sign}{_grouped(operation.right, splits_right)}"
    base = _grouped(operation.left, not _is_primary(operation.left))
    return f"{base}{sign}{_exponent(operation.right)}"


def _exponent(exponent: Expression) -> str:
    if isinstance(exponent, Negation) and _is_primary(exponent.operand):
        return f"-{_render(exponent.operand)}"
    return _grouped(exponent, not _is_primary(exponent))


def _grouped(expression: Expression, needs_parentheses: bool) -> str:
    rendered = _render(expression)
    return f"({rendered})" if needs_parentheses else rendered


def _is_sum_or_negation(expression: Expression) -> bool:
    if isinstance(expression, Negation):
        return True
    return isinstance(expression, BinaryOperation) and expression.operator in _SUMS


def _is_product(expression: Expression) -> bool:
    return isinstance(expression, BinaryOperation) and expression.operator in _PRODUCTS


def _is_division(expression: Expression) -> bool:
    return isinstance(expression, BinaryOperation) and expression.operator is BinaryOperator.DIVIDE


def _is_primary(expression: Expression) -> bool:
    return not isinstance(expression, Negation | BinaryOperation)
