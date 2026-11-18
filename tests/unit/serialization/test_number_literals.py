from fractions import Fraction

import pytest

from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.interfaces.serialization.decoding.number_literals import (
    NumberLiteralError,
    parse_exact_number,
)


@pytest.mark.algebraic
@pytest.mark.parametrize(
    ("literal", "expected"),
    [
        ("1", Fraction(1)),
        ("-3", Fraction(-3)),
        ("0.1", Fraction(1, 10)),
        ("1e-9", Fraction(1, 10**9)),
        ("9.1093837139E-31", Fraction(91093837139, 10**41)),
        ("1e99", Fraction(10**99)),
        ("1e-99", Fraction(1, 10**99)),
        ("1/3", Fraction(1, 3)),
        ("-2/6", Fraction(-1, 3)),
        (".5", Fraction(1, 2)),
        ("2.", Fraction(2)),
    ],
)
def test_literals_keep_their_exact_rational_value(literal: str, expected: Fraction) -> None:
    assert parse_exact_number(literal) == expected


@pytest.mark.parametrize("literal", ["NaN", "nan", "Infinity", "-Infinity", "inf", "+INF"])
def test_non_finite_words_are_refused(literal: str) -> None:
    with pytest.raises(NumberLiteralError) as refusal:
        parse_exact_number(literal)

    assert refusal.value.code is DiagnosticCode.NON_FINITE_NUMBER


@pytest.mark.parametrize("literal", ["", "abc", "1,5", "1e", "1/", "1/2/3", " 1", "0x10", "1_000"])
def test_text_outside_the_literal_grammar_is_refused(literal: str) -> None:
    with pytest.raises(NumberLiteralError) as refusal:
        parse_exact_number(literal)

    assert refusal.value.code is DiagnosticCode.MALFORMED_NUMBER


def test_fraction_with_zero_denominator_is_refused() -> None:
    with pytest.raises(NumberLiteralError, match="denominador"):
        parse_exact_number("1/0")


@pytest.mark.parametrize("literal", ["1e100", "1e-100", "1e1000", "1" * 65])
def test_literals_that_would_expand_without_bound_are_refused(literal: str) -> None:
    with pytest.raises(NumberLiteralError) as refusal:
        parse_exact_number(literal)

    assert refusal.value.code is DiagnosticCode.NUMBER_OUT_OF_RANGE
