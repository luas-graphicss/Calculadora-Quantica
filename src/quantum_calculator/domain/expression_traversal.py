from collections.abc import Iterator

from quantum_calculator.domain.expressions import (
    BinaryOperation,
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


def children(node: Statement) -> tuple[Expression, ...]:
    match node:
        case Number() | Pi() | Symbol():
            return ()
        case Negation():
            return (node.operand,)
        case BinaryOperation() | Equation():
            return (node.left, node.right)
        case FunctionCall() | UnknownFunction():
            return (node.argument,)
        case Derivative():
            return (node.body,)
        case Integral():
            if node.bounds is None:
                return (node.body,)
            return (node.body, node.bounds.lower, node.bounds.upper)


def walk(node: Statement) -> Iterator[Statement]:
    pending: list[Statement] = [node]
    while pending:
        current = pending.pop()
        yield current
        pending.extend(reversed(children(current)))


def node_count(node: Statement) -> int:
    return sum(1 for _ in walk(node))


def symbol_names(node: Statement) -> frozenset[str]:
    return frozenset(item.name for item in walk(node) if isinstance(item, Symbol))


def unknown_functions(node: Statement) -> tuple[UnknownFunction, ...]:
    return tuple(item for item in walk(node) if isinstance(item, UnknownFunction))


def is_explicit(node: Statement) -> bool:
    return not any(isinstance(item, UnknownFunction | Derivative | Integral) for item in walk(node))
