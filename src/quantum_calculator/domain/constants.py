from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from quantum_calculator.domain.quantities import Quantity

PLANCK_CONSTANT = "planck_constant"
ELECTRON_VOLT = "electron_volt"
ELECTRON_MASS = "electron_mass"


class ConstantExactness(StrEnum):
    EXACT = "exact"
    MEASURED = "measured"


@dataclass(frozen=True, slots=True)
class PhysicalConstant:
    identifier: str
    symbol: str
    name: str
    value: Quantity
    standard_uncertainty: Fraction | None
    edition: str
    source: str

    @property
    def exactness(self) -> ConstantExactness:
        if self.standard_uncertainty is None:
            return ConstantExactness.EXACT
        return ConstantExactness.MEASURED
