from decimal import Decimal
from fractions import Fraction

import pytest

from quantum_calculator.domain.rounding import render_decimal, render_square_root


@pytest.mark.parametrize(
    ("value", "digits", "expected"),
    [
        (Fraction(1, 8), 2, "0.12"),
        (Fraction(3, 8), 2, "0.38"),
        (Fraction(27, 200), 2, "0.14"),
        (Fraction(2, 3), 5, "0.66667"),
        (Fraction(-2, 3), 5, "-0.66667"),
        (Fraction(602466739, 10**28), 4, "6.025E-20"),
    ],
)
def test_rounding_is_half_even_on_significant_digits(
    value: Fraction, digits: int, expected: str
) -> None:
    assert str(render_decimal(value, digits).decimal) == expected


def test_terminating_decimal_within_the_precision_is_reported_exact() -> None:
    rendering = render_decimal(Fraction(1, 10**9), 34)

    assert rendering.is_exact
    assert str(rendering.decimal) == "1E-9"


def test_non_terminating_decimal_is_reported_rounded() -> None:
    assert not render_decimal(Fraction(1, 3), 34).is_exact


def test_trailing_zeros_are_not_added_to_fill_the_precision() -> None:
    assert str(render_decimal(Fraction(1, 4), 10).decimal) == "0.25"


@pytest.mark.parametrize(
    ("value", "digits", "expected"),
    [(Fraction(2), 10, "1.414213562"), (Fraction(4, 9), 2, "0.67"), (Fraction(0), 2, "0")],
)
def test_square_root_is_rounded_to_the_requested_digits(
    value: Fraction, digits: int, expected: str
) -> None:
    assert render_square_root(value, digits) == Decimal(expected)
