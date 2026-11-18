import math

import pytest

from quantum_calculator.domain.numerical.tolerance import Tolerance

ENERGY_TOLERANCE = Tolerance(absolute=1e-12, relative=1e-9)


def test_bound_adds_the_absolute_term_to_the_relative_share_of_the_scale() -> None:
    assert ENERGY_TOLERANCE.bound(2.0) == pytest.approx(1e-12 + 2e-9, rel=1e-15)


def test_value_near_zero_is_judged_by_the_absolute_term() -> None:
    assert ENERGY_TOLERANCE.allows(5e-13, scale=0.0)
    assert not ENERGY_TOLERANCE.allows(5e-12, scale=0.0)


def test_error_is_compared_by_magnitude_whatever_its_sign() -> None:
    assert ENERGY_TOLERANCE.allows(-1e-9, scale=-1.0)
    assert not ENERGY_TOLERANCE.allows(-3e-9, scale=-1.0)


@pytest.mark.parametrize("error", [math.nan, math.inf])
def test_non_finite_error_is_never_within_tolerance(error: float) -> None:
    assert not ENERGY_TOLERANCE.allows(error, scale=1.0)
