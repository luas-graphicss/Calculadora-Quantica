import pytest

from quantum_calculator.domain.definedness import definedness_conditions
from quantum_calculator.domain.statements import Notation
from quantum_calculator.notation.rendering.conditions import render_condition
from support.notation import read

NOT_ZERO = "\N{NOT EQUAL TO} 0"
NOT_NEGATIVE = "\N{GREATER-THAN OR EQUAL TO} 0"


def _conditions(expression: str) -> list[str]:
    return [
        render_condition(item) for item in definedness_conditions(read(Notation.TEXT, expression))
    ]


@pytest.mark.parametrize(
    ("expression", "conditions"),
    [
        ("x^2 + sin(x)*exp(y)", []),
        ("a/(x - 1)", [f"x - 1 {NOT_ZERO}"]),
        ("x^-2", [f"x {NOT_ZERO}"]),
        ("x^3", []),
        ("x^y", ["x > 0"]),
        ("x^(1/2)", ["x > 0", f"2 {NOT_ZERO}"]),
        ("ln(x - a)", ["x - a > 0"]),
        ("sqrt(x - a)", [f"x - a {NOT_NEGATIVE}"]),
        ("tan(x)", [f"cos(x) {NOT_ZERO}"]),
    ],
)
def test_each_partial_operation_states_where_it_is_defined(
    expression: str, conditions: list[str]
) -> None:
    assert _conditions(expression) == conditions


@pytest.mark.parametrize(
    ("expression", "conditions"),
    [
        ("1/(2*sqrt(x))", [f"x {NOT_ZERO}", f"x {NOT_NEGATIVE}"]),
        ("1/(3*abs(x)^2)", [f"x {NOT_ZERO}"]),
        ("1/(-x)", [f"x {NOT_ZERO}"]),
        ("ln(abs(x - a))", [f"x - a {NOT_ZERO}"]),
        ("ln(x)/x", ["x > 0"]),
        ("sqrt(x)*ln(x)", ["x > 0"]),
        ("1/x + 2/x", [f"x {NOT_ZERO}"]),
    ],
)
def test_conditions_are_reduced_to_the_expression_that_must_not_vanish(
    expression: str, conditions: list[str]
) -> None:
    assert _conditions(expression) == conditions


def test_cancelled_factor_keeps_its_exclusion() -> None:
    assert _conditions("(x^2 - 1)/(x - 1)") == [f"x - 1 {NOT_ZERO}"]
