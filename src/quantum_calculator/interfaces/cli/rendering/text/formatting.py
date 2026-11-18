from fractions import Fraction

from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.rounding import MAX_SIGNIFICANT_DIGITS, render_decimal

_UNPRINTABLE_REPLACEMENT = "?"


def printable(text: str) -> str:
    return "".join(
        character if character.isprintable() else _UNPRINTABLE_REPLACEMENT for character in text
    )


def section(title: str, lines: list[str]) -> list[str]:
    return ["", title, *(f"  {line}" for line in lines)]


class QuantityFormatter:
    def __init__(self, units: UnitRegistry) -> None:
        self._units = units

    def unit_of(self, quantity: Quantity) -> str:
        return self._units.coherent_symbol(quantity.dimension)

    def exact(
        self, value: Fraction, unit: str, significant_digits: int = MAX_SIGNIFICANT_DIGITS
    ) -> str:
        rendering = render_decimal(value, significant_digits)
        marker = "" if rendering.is_exact else " (arredondado)"
        return f"{rendering.decimal} {unit}{marker}"

    def quantity(self, quantity: Quantity, significant_digits: int = MAX_SIGNIFICANT_DIGITS) -> str:
        return self.exact(quantity.magnitude, self.unit_of(quantity), significant_digits)
