import math

import pytest

from quantum_calculator.domain.numerical.scalar_evaluation import (
    UndefinedValueError,
    evaluate_scalar,
)
from support.notation import SYMBOLS, read_expression_text


def _value(expression: str, **values: float) -> float:
    return evaluate_scalar(read_expression_text(expression, SYMBOLS), values)


@pytest.mark.numerical
@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("pi", math.pi),
        ("2*pi/a", math.pi),
        ("-a^2 + 1/4", -3.75),
        ("sqrt(a) + abs(-a)", math.sqrt(2.0) + 2.0),
        ("exp(ln(a))", 2.0),
        ("sin(pi/2) - cos(0) + tan(0)", 0.0),
    ],
)
def test_explicit_expression_has_the_value_of_its_registered_operations(
    expression: str, expected: float
) -> None:
    assert _value(expression, a=2.0) == pytest.approx(expected, abs=1e-15)


@pytest.mark.parametrize(
    "expression", ["1/a", "ln(a)", "sqrt(a - 1)", "(a - 8)^(1/3)", "exp(1000)", "10^400"]
)
def test_expression_without_a_finite_real_value_is_refused(expression: str) -> None:
    with pytest.raises(UndefinedValueError):
        _value(expression, a=0.0)


def test_unknown_function_has_no_scalar_value() -> None:
    with pytest.raises(TypeError, match="explicit"):
        _value("u(t)", t=0.0)
