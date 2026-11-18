from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.domain.definedness import definedness_conditions
from quantum_calculator.domain.expression_traversal import symbol_names
from quantum_calculator.domain.expressions import Expression, Integral, Statement
from quantum_calculator.domain.symbolic_solution import (
    ConditionRelation,
    ConditionScope,
    DomainCondition,
)


class ConditionStatus(StrEnum):
    HOLDS = "holds"
    VIOLATED = "violated"
    OPEN = "open"


@dataclass(frozen=True, slots=True)
class DomainAnalysis:
    validity: tuple[DomainCondition, ...]
    assumptions: tuple[DomainCondition, ...]


@dataclass(frozen=True, slots=True)
class Singularity:
    condition: DomainCondition
    location: str


@dataclass(frozen=True, slots=True)
class IntervalAnalysis:
    singularities: tuple[Singularity, ...]
    assumptions: tuple[DomainCondition, ...]


class UndefinedExpressionError(ValueError):
    def __init__(self, condition: DomainCondition) -> None:
        super().__init__(f"{condition.relation.value} condition never holds")
        self.condition = condition


_PROPERTIES: dict[ConditionRelation, Callable[[sympy.Expr], bool | None]] = {
    ConditionRelation.NONZERO: lambda value: value.is_nonzero,
    ConditionRelation.POSITIVE: lambda value: value.is_positive,
    ConditionRelation.NONNEGATIVE: lambda value: value.is_nonnegative,
}
_VIOLATIONS: dict[ConditionRelation, Callable[[sympy.Expr], sympy.Basic]] = {
    ConditionRelation.NONZERO: lambda value: sympy.Eq(value, 0),
    ConditionRelation.POSITIVE: lambda value: value <= 0,
    ConditionRelation.NONNEGATIVE: lambda value: value < 0,
}
_LOCATED_SETS = (sympy.FiniteSet, sympy.Interval, sympy.Union)


def condition_status(condition: DomainCondition, builder: ExpressionBuilder) -> ConditionStatus:
    verdict = _PROPERTIES[condition.relation](builder.build(condition.expression))
    if verdict is None:
        return ConditionStatus.OPEN
    return ConditionStatus.HOLDS if verdict else ConditionStatus.VIOLATED


def analyze_domain(
    builder: ExpressionBuilder, variables: frozenset[str], *statements: Statement
) -> DomainAnalysis:
    validity: list[DomainCondition] = []
    assumptions: list[DomainCondition] = []
    for condition in _distinct(definedness_conditions(*statements), builder):
        status = condition_status(condition, builder)
        if status is ConditionStatus.VIOLATED:
            raise UndefinedExpressionError(condition)
        if status is ConditionStatus.OPEN:
            involves_variable = symbol_names(condition.expression) & variables
            (validity if involves_variable else assumptions).append(condition)
    return DomainAnalysis(tuple(validity), tuple(assumptions))


def analyze_interval(
    builder: ExpressionBuilder, integral: Integral, *expressions: Expression
) -> IntervalAnalysis:
    if integral.bounds is None:
        raise ValueError("interval analysis needs a definite integral")
    variable = builder.symbol(integral.variable)
    lower = builder.build(integral.bounds.lower)
    upper = builder.build(integral.bounds.upper)
    singularities: list[Singularity] = []
    assumptions: list[DomainCondition] = []
    for condition in _distinct(definedness_conditions(*expressions), builder):
        status = condition_status(condition, builder)
        if status is ConditionStatus.HOLDS:
            continue
        if integral.variable not in symbol_names(condition.expression):
            if status is ConditionStatus.VIOLATED:
                raise UndefinedExpressionError(condition)
            assumptions.append(condition)
            continue
        location = _violation_set(condition, builder, variable, lower, upper)
        if location is None:
            assumptions.append(
                DomainCondition(
                    condition.relation, condition.expression, ConditionScope.INTEGRATION_INTERVAL
                )
            )
        elif location:
            singularities.append(Singularity(condition, location))
    return IntervalAnalysis(tuple(singularities), tuple(assumptions))


def _distinct(
    conditions: tuple[DomainCondition, ...], builder: ExpressionBuilder
) -> tuple[DomainCondition, ...]:
    seen: set[tuple[ConditionRelation, sympy.Expr]] = set()
    distinct: list[DomainCondition] = []
    for condition in conditions:
        value = builder.build(condition.expression)
        if (condition.relation, value) in seen:
            continue
        seen.add((condition.relation, value))
        if condition.relation is ConditionRelation.NONZERO:
            seen.add((condition.relation, -value))
        distinct.append(condition)
    return tuple(distinct)


def _violation_set(
    condition: DomainCondition,
    builder: ExpressionBuilder,
    variable: sympy.Symbol,
    lower: sympy.Expr,
    upper: sympy.Expr,
) -> str | None:
    value = builder.build(condition.expression)
    if value.free_symbols - {variable} or not (lower.is_number and upper.is_number):
        return None
    interval = sympy.Interval(sympy.Min(lower, upper), sympy.Max(lower, upper))
    try:
        offending = sympy.solveset(_VIOLATIONS[condition.relation](value), variable, interval)
    except NotImplementedError:
        return None
    if offending.is_empty:
        return ""
    if isinstance(offending, _LOCATED_SETS):
        return str(sympy.sstr(offending))
    return None
