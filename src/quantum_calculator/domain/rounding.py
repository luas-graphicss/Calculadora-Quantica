from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, Inexact
from fractions import Fraction

DEFAULT_SIGNIFICANT_DIGITS = 10
MAX_SIGNIFICANT_DIGITS = 34
UNCERTAINTY_SIGNIFICANT_DIGITS = 2
ROUNDING_MODE = "half_even"
_SQUARE_ROOT_GUARD_DIGITS = 25


@dataclass(frozen=True, slots=True)
class RoundingPolicy:
    significant_digits: int


@dataclass(frozen=True, slots=True)
class DecimalRendering:
    decimal: Decimal
    is_exact: bool


def render_decimal(value: Fraction, significant_digits: int) -> DecimalRendering:
    context = _half_even_context(significant_digits)
    decimal = context.divide(Decimal(value.numerator), Decimal(value.denominator))
    return DecimalRendering(decimal, is_exact=not context.flags[Inexact])


def render_square_root(value: Fraction, significant_digits: int) -> Decimal:
    working = _half_even_context(significant_digits + _SQUARE_ROOT_GUARD_DIGITS)
    quotient = working.divide(Decimal(value.numerator), Decimal(value.denominator))
    return _half_even_context(significant_digits).plus(working.sqrt(quotient))


def _half_even_context(significant_digits: int) -> Context:
    return Context(prec=significant_digits, rounding=ROUND_HALF_EVEN)
