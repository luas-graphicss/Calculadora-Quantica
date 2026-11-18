from quantum_calculator.domain.expressions import (
    BinaryOperation,
    Derivative,
    Equation,
    FunctionCall,
    Integral,
    Negation,
    Number,
    Pi,
    Statement,
    Symbol,
    UnknownFunction,
)


def render_structure(statement: Statement) -> str:
    match statement:
        case Equation():
            sides = f"{render_structure(statement.left)} {render_structure(statement.right)}"
            return f"(equation {sides})"
        case Number():
            return f"(number {statement.value})"
        case Pi():
            return "pi"
        case Symbol():
            return f"(symbol {statement.name})"
        case Negation():
            return f"(negate {render_structure(statement.operand)})"
        case BinaryOperation():
            operands = f"{render_structure(statement.left)} {render_structure(statement.right)}"
            return f"({statement.operator.value} {operands})"
        case FunctionCall():
            return f"({statement.function.value} {render_structure(statement.argument)})"
        case UnknownFunction():
            argument = render_structure(statement.argument)
            return f"(unknown {statement.name} {statement.order} {argument})"
        case Derivative():
            body = render_structure(statement.body)
            head = f"derivative {statement.kind.value} {statement.variable} {statement.order}"
            return f"({head} {body})"
        case Integral():
            return _integral(statement)


def _integral(integral: Integral) -> str:
    body = render_structure(integral.body)
    if integral.bounds is None:
        return f"(integral {integral.variable} {body})"
    lower = render_structure(integral.bounds.lower)
    upper = render_structure(integral.bounds.upper)
    return f"(integral {integral.variable} {body} {lower} {upper})"
