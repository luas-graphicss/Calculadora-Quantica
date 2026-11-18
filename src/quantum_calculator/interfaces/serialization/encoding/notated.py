from quantum_calculator.domain.expressions import Statement
from quantum_calculator.domain.symbolic_solution import DomainCondition
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject
from quantum_calculator.notation.rendering.conditions import render_condition
from quantum_calculator.notation.rendering.latex import render_latex
from quantum_calculator.notation.rendering.structure import render_structure
from quantum_calculator.notation.rendering.text import render_text


def encode_notated(statement: Statement) -> JsonObject:
    return {
        "text": render_text(statement),
        "latex": render_latex(statement),
        "structure": render_structure(statement),
    }


def encode_condition(condition: DomainCondition) -> JsonObject:
    return {
        "relation": condition.relation.value,
        "scope": condition.scope.value,
        "expression": encode_notated(condition.expression),
        "text": render_condition(condition),
    }
