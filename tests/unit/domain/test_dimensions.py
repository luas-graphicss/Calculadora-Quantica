import pytest

from quantum_calculator.domain.dimensions import ACTION, ENERGY, LENGTH, MASS, TIME, Dimension

pytestmark = pytest.mark.algebraic


def test_energy_is_mass_times_length_squared_per_time_squared() -> None:
    assert Dimension(mass=1, length=2, time=-2) == ENERGY


def test_infinite_well_formula_has_the_dimension_of_energy() -> None:
    assert ACTION**2 / (MASS * LENGTH**2) == ENERGY


def test_dividing_a_dimension_by_itself_leaves_no_base_unit() -> None:
    assert (TIME / TIME).base_si_unit() == "1"


@pytest.mark.parametrize(
    ("dimension", "expected"),
    [(MASS, "kg"), (ENERGY, "kg m^2 s^-2"), (ENERGY / LENGTH, "kg m s^-2")],
)
def test_base_si_unit_lists_non_zero_exponents(dimension: Dimension, expected: str) -> None:
    assert dimension.base_si_unit() == expected
