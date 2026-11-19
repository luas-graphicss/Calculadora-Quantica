import re
from dataclasses import dataclass
from fractions import Fraction

from quantum_calculator.domain.diagnostics import quote_user_text
from quantum_calculator.domain.dimensions import DIMENSIONLESS, Dimension
from quantum_calculator.domain.ports import UnitRegistry

UNIT_EXPRESSION_FORM = (
    "unidades do registro separadas por espaço, com expoente inteiro de um dígito e no "
    "máximo uma barra, como m/s^2, kg m^2/s^2, 1/s ou 1 para grandeza adimensional"
)

_FACTOR = re.compile(r"(?P<symbol>[^\s^/]+?)(?:\^(?P<exponent>-?\d))?")
_DIVISION = "/"
_UNITY = "1"


class UnitExpressionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class UnitMeasure:
    dimension: Dimension
    si_factor: Fraction

    def __mul__(self, other: "UnitMeasure") -> "UnitMeasure":
        return UnitMeasure(self.dimension * other.dimension, self.si_factor * other.si_factor)

    def __truediv__(self, other: "UnitMeasure") -> "UnitMeasure":
        return UnitMeasure(self.dimension / other.dimension, self.si_factor / other.si_factor)


_COHERENT = UnitMeasure(DIMENSIONLESS, Fraction(1))


def dimension_of_unit(expression: str, units: UnitRegistry) -> Dimension:
    return measure_of_unit(expression, units).dimension


def measure_of_unit(expression: str, units: UnitRegistry) -> UnitMeasure:
    numerator, division, denominator = expression.partition(_DIVISION)
    if _DIVISION in denominator:
        raise UnitExpressionError("há mais de uma barra de divisão")
    measure = _product(numerator, units)
    if not division:
        return measure
    return measure / _product(denominator, units)


def _product(factors: str, units: UnitRegistry) -> UnitMeasure:
    names = factors.split()
    if not names:
        raise UnitExpressionError("falta uma unidade de um dos lados da barra")
    measure = _COHERENT
    for name in names:
        if name != _UNITY:
            measure = measure * _factor(name, units)
    return measure


def _factor(text: str, units: UnitRegistry) -> UnitMeasure:
    match = _FACTOR.fullmatch(text)
    if match is None:
        raise UnitExpressionError(f"{quote_user_text(text)} não é uma unidade com expoente inteiro")
    unit = units.find(match["symbol"])
    if unit is None:
        raise UnitExpressionError(
            f"a unidade {quote_user_text(match['symbol'])} não consta do registro"
        )
    exponent = int(match["exponent"] or _UNITY)
    return UnitMeasure(unit.dimension**exponent, unit.si_factor**exponent)
