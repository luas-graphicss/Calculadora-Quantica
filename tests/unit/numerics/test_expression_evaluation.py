import math

import numpy
import pytest

from quantum_calculator.numerics.evaluation import NonFiniteValueError, evaluate
from support.notation import SYMBOLS, read_expression_text


def _value(expression: str, **bindings: float) -> float:
    return float(evaluate(read_expression_text(expression, SYMBOLS), bindings))


@pytest.mark.numerical
@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2*x + 1/4", 6.25),
        ("x^2 - x", 6.0),
        ("-x^2", -9.0),
        ("sin(pi/2) + cos(0)", 2.0),
        ("exp(ln(x))", 3.0),
        ("sqrt(x + 1) + abs(-x)", 5.0),
        ("tan(pi/4)", 1.0),
    ],
)
def test_registered_operations_are_evaluated_in_double_precision(
    expression: str, expected: float
) -> None:
    assert _value(expression, x=3.0) == pytest.approx(expected, rel=1e-15)


@pytest.mark.numerical
def test_expression_is_evaluated_over_every_sample_at_once() -> None:
    positions = numpy.linspace(0.0, 1.0, 5)

    values = evaluate(read_expression_text("a*x^2", SYMBOLS), {"a": 2.0, "x": positions})

    assert values == pytest.approx(2.0 * positions**2, rel=1e-15)


def test_unknown_function_reads_its_current_value_from_the_bindings() -> None:
    assert _value("k*u(t)", k=-2.0, u=1.5, t=0.0) == -3.0


@pytest.mark.parametrize("expression", ["1/x", "ln(x)", "sqrt(x - 1)", "(x - 1)^(1/2)"])
def test_value_that_is_not_finite_is_refused_instead_of_returned(expression: str) -> None:
    with pytest.raises(NonFiniteValueError):
        _value(expression, x=0.0)


def test_derivative_of_the_unknown_has_no_pointwise_value() -> None:
    with pytest.raises(TypeError, match="derivative of u"):
        _value("u'", u=1.0, t=0.0)


def test_pi_is_the_double_closest_to_the_constant() -> None:
    assert _value("pi") == math.pi
