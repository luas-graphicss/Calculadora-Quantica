from dataclasses import dataclass
from fractions import Fraction

from quantum_calculator.domain.dimensions import Dimension


@dataclass(frozen=True, slots=True)
class Quantity:
    magnitude: Fraction
    dimension: Dimension
