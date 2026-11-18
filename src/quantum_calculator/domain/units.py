from dataclasses import dataclass
from fractions import Fraction

from quantum_calculator.domain.dimensions import Dimension
from quantum_calculator.domain.quantities import Quantity


class DimensionMismatchError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Unit:
    symbol: str
    dimension: Dimension
    si_factor: Fraction
    defining_constants: tuple[str, ...] = ()

    def to_si(self, value: Fraction) -> Quantity:
        return Quantity(value * self.si_factor, self.dimension)

    def from_si(self, quantity: Quantity) -> Fraction:
        if quantity.dimension != self.dimension:
            raise DimensionMismatchError(
                f"cannot express {quantity.dimension.base_si_unit()} in {self.symbol}"
            )
        return quantity.magnitude / self.si_factor
