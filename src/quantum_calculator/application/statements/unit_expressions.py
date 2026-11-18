import re

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


def dimension_of_unit(expression: str, units: UnitRegistry) -> Dimension:
    numerator, division, denominator = expression.partition(_DIVISION)
    if _DIVISION in denominator:
        raise UnitExpressionError("há mais de uma barra de divisão")
    dimension = _product(numerator, units)
    if not division:
        return dimension
    return dimension / _product(denominator, units)


def _product(factors: str, units: UnitRegistry) -> Dimension:
    names = factors.split()
    if not names:
        raise UnitExpressionError("falta uma unidade de um dos lados da barra")
    dimension = DIMENSIONLESS
    for name in names:
        if name != _UNITY:
            dimension = dimension * _factor(name, units)
    return dimension


def _factor(text: str, units: UnitRegistry) -> Dimension:
    match = _FACTOR.fullmatch(text)
    if match is None:
        raise UnitExpressionError(f"{quote_user_text(text)} não é uma unidade com expoente inteiro")
    unit = units.find(match["symbol"])
    if unit is None:
        raise UnitExpressionError(
            f"a unidade {quote_user_text(match['symbol'])} não consta do registro"
        )
    return unit.dimension ** int(match["exponent"] or _UNITY)
