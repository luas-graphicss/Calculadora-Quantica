import unicodedata
from fractions import Fraction

from quantum_calculator.domain.constants import ELECTRON_VOLT
from quantum_calculator.domain.dimensions import ACTION, ENERGY, LENGTH, MASS, TIME, Dimension
from quantum_calculator.domain.ports import ConstantsEdition, require_constant
from quantum_calculator.domain.units import Unit

REGISTRY_VERSION = "1.0.0"

_MICRO = "\N{GREEK SMALL LETTER MU}"
_ANGSTROM = "\N{LATIN CAPITAL LETTER A WITH RING ABOVE}"

_DECIMAL_UNITS: tuple[tuple[str, Dimension, int], ...] = (
    ("kg", MASS, 0),
    ("g", MASS, -3),
    ("mg", MASS, -6),
    ("m", LENGTH, 0),
    ("mm", LENGTH, -3),
    (f"{_MICRO}m", LENGTH, -6),
    ("nm", LENGTH, -9),
    (_ANGSTROM, LENGTH, -10),
    ("pm", LENGTH, -12),
    ("s", TIME, 0),
    ("ms", TIME, -3),
    (f"{_MICRO}s", TIME, -6),
    ("ns", TIME, -9),
    ("ps", TIME, -12),
    ("fs", TIME, -15),
    ("J", ENERGY, 0),
)
_ELECTRON_VOLT_MULTIPLES = (("eV", 0), ("meV", -3), ("keV", 3), ("MeV", 6))
_ASCII_ALIASES = {"angstrom": _ANGSTROM, "um": f"{_MICRO}m", "us": f"{_MICRO}s"}
_COHERENT_SYMBOLS = {
    MASS: "kg",
    LENGTH: "m",
    TIME: "s",
    ENERGY: "J",
    ACTION: "J s",
    ENERGY**2: "J^2",
    ACTION**2: "J^2 s^2",
    ENERGY / MASS: "J/kg",
    ENERGY / LENGTH: "J/m",
}


class SiUnitRegistry:
    def __init__(self, constants: ConstantsEdition) -> None:
        electron_volt = require_constant(constants, ELECTRON_VOLT).value.magnitude
        units = [
            Unit(symbol, dimension, Fraction(10) ** exponent)
            for symbol, dimension, exponent in _DECIMAL_UNITS
        ]
        units += [
            Unit(symbol, ENERGY, electron_volt * Fraction(10) ** exponent, (ELECTRON_VOLT,))
            for symbol, exponent in _ELECTRON_VOLT_MULTIPLES
        ]
        self._units = {unit.symbol: unit for unit in units}

    @property
    def version(self) -> str:
        return REGISTRY_VERSION

    def find(self, symbol: str) -> Unit | None:
        normalized = unicodedata.normalize("NFKC", symbol)
        return self._units.get(_ASCII_ALIASES.get(normalized, normalized))

    def symbols_for(self, dimension: Dimension) -> tuple[str, ...]:
        return tuple(unit.symbol for unit in self._units.values() if unit.dimension == dimension)

    def coherent_symbol(self, dimension: Dimension) -> str:
        return _COHERENT_SYMBOLS.get(dimension, dimension.base_si_unit())
