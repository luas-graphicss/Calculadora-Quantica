from fractions import Fraction

import pytest

from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.domain.constants import ELECTRON_VOLT
from quantum_calculator.domain.dimensions import ENERGY, LENGTH, MASS, TIME
from quantum_calculator.domain.units import Unit

ANGSTROM = "\N{LATIN CAPITAL LETTER A WITH RING ABOVE}"


def _unit(units: SiUnitRegistry, symbol: str) -> Unit:
    unit = units.find(symbol)
    assert unit is not None
    return unit


@pytest.mark.algebraic
def test_ten_angstrom_are_exactly_one_nanometer(units: SiUnitRegistry) -> None:
    ten_angstrom = _unit(units, ANGSTROM).to_si(Fraction(10))

    assert ten_angstrom == _unit(units, "nm").to_si(Fraction(1))


@pytest.mark.algebraic
def test_electron_volt_factor_is_the_exact_catalog_constant(
    units: SiUnitRegistry, constants: Codata2022Constants
) -> None:
    electron_volt = constants.find(ELECTRON_VOLT)
    assert electron_volt is not None

    unit = _unit(units, "eV")

    assert unit.si_factor == electron_volt.value.magnitude
    assert unit.defining_constants == (ELECTRON_VOLT,)
    assert _unit(units, "meV").si_factor == unit.si_factor / 1000


@pytest.mark.parametrize(
    ("spelling", "canonical"),
    [
        ("angstrom", ANGSTROM),
        ("\N{ANGSTROM SIGN}", ANGSTROM),
        ("um", "\N{GREEK SMALL LETTER MU}m"),
        ("\N{MICRO SIGN}m", "\N{GREEK SMALL LETTER MU}m"),
    ],
)
def test_alternative_spellings_resolve_to_the_canonical_unit(
    units: SiUnitRegistry, spelling: str, canonical: str
) -> None:
    assert _unit(units, spelling).symbol == canonical


def test_unknown_symbol_is_not_resolved(units: SiUnitRegistry) -> None:
    assert units.find("furlong") is None


def test_symbols_are_listed_by_dimension(units: SiUnitRegistry) -> None:
    lengths = units.symbols_for(LENGTH)

    assert {"m", "nm", ANGSTROM} <= set(lengths)
    assert "s" not in lengths
    assert units.symbols_for(TIME)[0] == "s"


def test_coherent_symbol_prefers_named_si_units(units: SiUnitRegistry) -> None:
    assert units.coherent_symbol(ENERGY) == "J"
    assert units.coherent_symbol(MASS * LENGTH) == "kg m"
