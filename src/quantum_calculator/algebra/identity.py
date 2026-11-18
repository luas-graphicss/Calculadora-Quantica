from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import StrEnum

import sympy

SAMPLE_COUNT = 4

_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)
_WORKING_DIGITS = 40
_ZERO_THRESHOLD = sympy.Float("1e-25")
_SHOWN_DIGITS = 6


class IdentityOutcome(StrEnum):
    PROVEN = "proven"
    REFUTED_EXACTLY = "refuted_exactly"
    REFUTED_NUMERICALLY = "refuted_numerically"
    UNDECIDED = "undecided"


@dataclass(frozen=True, slots=True)
class IdentityVerdict:
    outcome: IdentityOutcome
    residual: sympy.Expr
    witness: str | None = None
    value_at_witness: str | None = None


class IdentityTester:
    def __init__(self, simplify: Callable[[sympy.Expr], sympy.Expr] = sympy.simplify) -> None:
        self._simplify = simplify

    def test(self, residual: sympy.Expr) -> IdentityVerdict:
        without_sign = residual.replace(sympy.sign, lambda argument: argument / sympy.Abs(argument))
        simplified = self._simplify(without_sign)
        if simplified.is_zero:
            return IdentityVerdict(IdentityOutcome.PROVEN, simplified)
        if simplified.is_zero is False:
            return IdentityVerdict(IdentityOutcome.REFUTED_EXACTLY, simplified)
        for point in _sample_points(simplified):
            refutation = _refutation_at(simplified, point)
            if refutation is not None:
                return refutation
        return IdentityVerdict(IdentityOutcome.UNDECIDED, simplified)


def _refutation_at(
    residual: sympy.Expr, point: dict[sympy.Symbol, sympy.Rational]
) -> IdentityVerdict | None:
    value = residual.subs(point)
    witness = ", ".join(f"{symbol.name} = {sympy.sstr(chosen)}" for symbol, chosen in point.items())
    if value.is_zero is False and value.is_finite:
        return IdentityVerdict(
            IdentityOutcome.REFUTED_EXACTLY, residual, witness, str(sympy.sstr(value))
        )
    approximation = value.evalf(_WORKING_DIGITS)
    if not approximation.is_Float or abs(approximation) <= _ZERO_THRESHOLD:
        return None
    shown = str(sympy.sstr(approximation.evalf(_SHOWN_DIGITS)))
    return IdentityVerdict(IdentityOutcome.REFUTED_NUMERICALLY, residual, witness, shown)


def _sample_points(residual: sympy.Expr) -> Iterator[dict[sympy.Symbol, sympy.Rational]]:
    symbols = sorted(residual.free_symbols, key=lambda symbol: symbol.name)
    for shift in range(SAMPLE_COUNT):
        yield {symbol: _sample(symbol, index, shift) for index, symbol in enumerate(symbols)}


def _sample(symbol: sympy.Symbol, index: int, shift: int) -> sympy.Rational:
    magnitude = sympy.Rational(_PRIMES[(index + shift) % len(_PRIMES)], shift + 1)
    if symbol.is_negative:
        return -magnitude
    if symbol.is_nonnegative or (index + shift) % 2 == 0:
        return magnitude
    return -magnitude
