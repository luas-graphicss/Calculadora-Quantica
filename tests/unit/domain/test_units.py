from fractions import Fraction

import pytest

from quantum_calculator.domain.dimensions import ENERGY, LENGTH
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.units import DimensionMismatchError, Unit

NANOMETER = Unit("nm", LENGTH, Fraction(1, 10**9))


@pytest.mark.algebraic
def test_conversion_to_si_and_back_is_exact() -> None:
    value = Fraction(1, 3)

    assert NANOMETER.from_si(NANOMETER.to_si(value)) == value


@pytest.mark.algebraic
def test_one_nanometer_is_exactly_one_billionth_of_a_meter() -> None:
    assert NANOMETER.to_si(Fraction(1)) == Quantity(Fraction(1, 10**9), LENGTH)


def test_expressing_an_energy_in_a_length_unit_is_refused() -> None:
    with pytest.raises(DimensionMismatchError, match="nm"):
        NANOMETER.from_si(Quantity(Fraction(1), ENERGY))
