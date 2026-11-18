from fractions import Fraction

from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.rounding import MAX_SIGNIFICANT_DIGITS, render_decimal

type JsonObject = dict[str, object]


def encode_exact(
    value: Fraction, unit: str, significant_digits: int = MAX_SIGNIFICANT_DIGITS
) -> JsonObject:
    rendering = render_decimal(value, significant_digits)
    return {
        "decimal": str(rendering.decimal),
        "is_exact": rendering.is_exact,
        "numerator": str(value.numerator),
        "denominator": str(value.denominator),
        "unit": unit,
    }


class QuantityEncoder:
    def __init__(self, units: UnitRegistry) -> None:
        self._units = units

    def unit_of(self, quantity: Quantity) -> str:
        return self._units.coherent_symbol(quantity.dimension)

    def encode(
        self, quantity: Quantity, significant_digits: int = MAX_SIGNIFICANT_DIGITS
    ) -> JsonObject:
        return encode_exact(quantity.magnitude, self.unit_of(quantity), significant_digits)
