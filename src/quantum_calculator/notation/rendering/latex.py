from quantum_calculator.domain.expressions import (
    BinaryOperation,
    BinaryOperator,
    Derivative,
    DerivativeKind,
    ElementaryFunction,
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
    DIFFERENTIAL,
    GREEK_NAMES,
    PRIME,
    symbol_parts,
)

_SUMS = (BinaryOperator.ADD, BinaryOperator.SUBTRACT)
_SUM_SIGNS = {BinaryOperator.ADD: " + ", BinaryOperator.SUBTRACT: " - "}
_DIFFERENTIALS = {DerivativeKind.ORDINARY: DIFFERENTIAL, DerivativeKind.PARTIAL: "\\partial "}


def render_latex(statement: Statement) -> str:
    if isinstance(statement, Equation):
        return f"{_render(statement.left)} = {_render(statement.right)}"
    return _render(statement)


def _render(expression: Expression) -> str:
    match expression:
        case Number():
            return decimal_literal(expression.value)
        case Pi():
            return "\\pi"
        case Symbol():
            return _name(expression.name)
        case Negation():
            return f"-{_grouped(expression.operand, _is_sum_or_negation(expression.operand))}"
        case BinaryOperation():
            return _operation(expression)
        case FunctionCall():
            return _function(expression)
        case UnknownFunction():
            primes = PRIME * expression.order
            return f"{_name(expression.name)}{primes}({_render(expression.argument)})"
        case Derivative():
            return _derivative(expression)
        case Integral():
            return _integral(expression)


def _name(name: str) -> str:
    base, digits, subscript = symbol_parts(name)
    spelled = GREEK_NAMES.get(base)
    if digits or (spelled is None and len(base) > 1):
        rendered = f"\\mathrm{{{spelled or base}{digits}}}"
    elif spelled is not None:
        rendered = f"\\{spelled}"
    else:
        rendered = base
    return rendered if subscript is None else f"{rendered}_{{{subscript}}}"


def _function(call: FunctionCall) -> str:
    argument = _render(call.argument)
    if call.function is ElementaryFunction.SQRT:
        return f"\\sqrt{{{argument}}}"
    if call.function is ElementaryFunction.ABS:
        return f"\\left|{argument}\\right|"
    return f"\\{call.function.value}\\left({argument}\\right)"


def _derivative(derivative: Derivative) -> str:
    marker = _DIFFERENTIALS[derivative.kind]
    order = "" if derivative.order == 1 else f"^{{{derivative.order}}}"
    variable = _name(derivative.variable)
    operator = f"\\frac{{{marker.strip()}{order}}}{{{marker}{variable}{order}}}"
    return f"{operator}\\left({_render(derivative.body)}\\right)"


def _integral(integral: Integral) -> str:
    bounds = ""
    if integral.bounds is not None:
        lower = _render(integral.bounds.lower)
        upper = _render(integral.bounds.upper)
        bounds = f"_{{{lower}}}^{{{upper}}}"
    body = _grouped(integral.body, _is_sum_or_negation(integral.body))
    return f"\\int{bounds} {body} \\, {DIFFERENTIAL}{_name(integral.variable)}"


def _operation(operation: BinaryOperation) -> str:
    operator = operation.operator
    if operator in _SUMS:
        right = _grouped(operation.right, _is_sum_or_negation(operation.right))
        return f"{_render(operation.left)}{_SUM_SIGNS[operator]}{right}"
    if operator is BinaryOperator.DIVIDE:
        return f"\\frac{{{_render(operation.left)}}}{{{_render(operation.right)}}}"
    if operator is BinaryOperator.MULTIPLY:
        left = _grouped(operation.left, _is_sum_or_negation(operation.left))
        splits_right = _is_sum_or_negation(operation.right) or _is_multiplication(operation.right)
        return f"{left} \\cdot {_grouped(operation.right, splits_right)}"
    base = _grouped(operation.left, isinstance(operation.left, Negation | BinaryOperation))
    return f"{base}^{{{_render(operation.right)}}}"


def _grouped(expression: Expression, needs_parentheses: bool) -> str:
    rendered = _render(expression)
    return f"\\left({rendered}\\right)" if needs_parentheses else rendered


def _is_sum_or_negation(expression: Expression) -> bool:
    if isinstance(expression, Negation):
        return True
    return isinstance(expression, BinaryOperation) and expression.operator in _SUMS


def _is_multiplication(expression: Expression) -> bool:
    return (
        isinstance(expression, BinaryOperation) and expression.operator is BinaryOperator.MULTIPLY
    )
