from quantum_calculator.domain.expression_traversal import walk
from quantum_calculator.domain.expressions import (
    BinaryOperation,
    BinaryOperator,
    ElementaryFunction,
    Expression,
    FunctionCall,
    Negation,
    Number,
    Statement,
)
from quantum_calculator.domain.symbolic_solution import ConditionRelation, DomainCondition

_ARGUMENT_REQUIREMENTS = {
    ElementaryFunction.LN: ConditionRelation.POSITIVE,
    ElementaryFunction.SQRT: ConditionRelation.NONNEGATIVE,
}
_ZERO_PRESERVING = (ElementaryFunction.ABS, ElementaryFunction.SQRT)


def definedness_conditions(*statements: Statement) -> tuple[DomainCondition, ...]:
    found: list[DomainCondition] = []
    for statement in statements:
        for node in walk(statement):
            condition = _condition_of(node)
            if condition is not None and condition not in found:
                found.append(condition)
    strict = {item.expression for item in found if item.relation is ConditionRelation.POSITIVE}
    return tuple(
        item
        for item in found
        if item.relation is ConditionRelation.POSITIVE or item.expression not in strict
    )


def _condition_of(node: Statement) -> DomainCondition | None:
    if isinstance(node, BinaryOperation):
        return _operation_condition(node)
    if isinstance(node, FunctionCall):
        return _function_condition(node)
    return None


def _operation_condition(node: BinaryOperation) -> DomainCondition | None:
    if node.operator is BinaryOperator.DIVIDE:
        return DomainCondition(ConditionRelation.NONZERO, _vanishing_core(node.right))
    if node.operator is not BinaryOperator.POWER:
        return None
    exponent = node.right
    if _is_integer_literal(exponent):
        return None
    if isinstance(exponent, Negation) and _is_integer_literal(exponent.operand):
        return DomainCondition(ConditionRelation.NONZERO, _vanishing_core(node.left))
    return DomainCondition(ConditionRelation.POSITIVE, node.left)


def _function_condition(node: FunctionCall) -> DomainCondition | None:
    if node.function is ElementaryFunction.TAN:
        cosine = FunctionCall(ElementaryFunction.COS, node.argument)
        return DomainCondition(ConditionRelation.NONZERO, cosine)
    relation = _ARGUMENT_REQUIREMENTS.get(node.function)
    if relation is None:
        return None
    if relation is ConditionRelation.POSITIVE and _is_modulus(node.argument):
        return DomainCondition(ConditionRelation.NONZERO, _vanishing_core(node.argument))
    return DomainCondition(relation, node.argument)


def _is_integer_literal(expression: Expression) -> bool:
    return isinstance(expression, Number) and expression.value.denominator == 1


def _vanishing_core(expression: Expression) -> Expression:
    while True:
        inner = _same_zeros(expression)
        if inner is None:
            return expression
        expression = inner


def _same_zeros(expression: Expression) -> Expression | None:
    if isinstance(expression, Negation):
        return expression.operand
    if isinstance(expression, FunctionCall) and expression.function in _ZERO_PRESERVING:
        return expression.argument
    if not isinstance(expression, BinaryOperation):
        return None
    if expression.operator is BinaryOperator.POWER and _is_positive_integer(expression.right):
        return expression.left
    if expression.operator is BinaryOperator.DIVIDE:
        return expression.left
    if expression.operator is BinaryOperator.MULTIPLY:
        if _is_nonzero_literal(expression.left):
            return expression.right
        if _is_nonzero_literal(expression.right):
            return expression.left
    return None


def _is_positive_integer(expression: Expression) -> bool:
    return _is_integer_literal(expression) and _is_nonzero_literal(expression)


def _is_nonzero_literal(expression: Expression) -> bool:
    return isinstance(expression, Number) and expression.value != 0


def _is_modulus(expression: Expression) -> bool:
    return isinstance(expression, FunctionCall) and expression.function is ElementaryFunction.ABS
