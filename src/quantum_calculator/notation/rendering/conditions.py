from quantum_calculator.domain.symbolic_solution import (
    ConditionRelation,
    ConditionScope,
    DomainCondition,
)
from quantum_calculator.notation.rendering.text import render_text

_RELATIONS = {
    ConditionRelation.NONZERO: "\N{NOT EQUAL TO} 0",
    ConditionRelation.POSITIVE: "> 0",
    ConditionRelation.NONNEGATIVE: "\N{GREATER-THAN OR EQUAL TO} 0",
}
_SCOPES = {
    ConditionScope.POINTWISE: "",
    ConditionScope.INTEGRATION_INTERVAL: " em todo o intervalo de integração",
}


def render_condition(condition: DomainCondition) -> str:
    relation = _RELATIONS[condition.relation]
    return f"{render_text(condition.expression)} {relation}{_SCOPES[condition.scope]}"


def render_conditions(conditions: tuple[DomainCondition, ...]) -> str:
    return "; ".join(render_condition(condition) for condition in conditions)
