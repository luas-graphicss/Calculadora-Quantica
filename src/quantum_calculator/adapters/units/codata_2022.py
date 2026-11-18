from fractions import Fraction

from quantum_calculator.domain.constants import (
    ELECTRON_MASS,
    ELECTRON_VOLT,
    PLANCK_CONSTANT,
    PhysicalConstant,
)
from quantum_calculator.domain.dimensions import ACTION, ENERGY, MASS, Dimension
from quantum_calculator.domain.quantities import Quantity

EDITION = "CODATA 2022"
_NIST_VALUE_PAGE = "https://physics.nist.gov/cgi-bin/cuu/Value?"

_CONSTANTS = (
    PhysicalConstant(
        identifier=PLANCK_CONSTANT,
        symbol="h",
        name="constante de Planck",
        value=Quantity(Fraction("6.62607015e-34"), ACTION),
        standard_uncertainty=None,
        edition=EDITION,
        source=f"{_NIST_VALUE_PAGE}h",
    ),
    PhysicalConstant(
        identifier=ELECTRON_VOLT,
        symbol="eV",
        name="elétron-volt em joules",
        value=Quantity(Fraction("1.602176634e-19"), ENERGY),
        standard_uncertainty=None,
        edition=EDITION,
        source=f"{_NIST_VALUE_PAGE}evj",
    ),
    PhysicalConstant(
        identifier=ELECTRON_MASS,
        symbol="m_e",
        name="massa do elétron",
        value=Quantity(Fraction("9.1093837139e-31"), MASS),
        standard_uncertainty=Fraction("2.8e-40"),
        edition=EDITION,
        source=f"{_NIST_VALUE_PAGE}me",
    ),
)


class Codata2022Constants:
    def __init__(self) -> None:
        self._by_identifier = {constant.identifier: constant for constant in _CONSTANTS}

    @property
    def label(self) -> str:
        return EDITION

    def find(self, identifier: str) -> PhysicalConstant | None:
        return self._by_identifier.get(identifier)

    def identifiers_for(self, dimension: Dimension) -> tuple[str, ...]:
        return tuple(
            constant.identifier for constant in _CONSTANTS if constant.value.dimension == dimension
        )
