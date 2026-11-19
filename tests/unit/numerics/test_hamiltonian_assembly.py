import math

import numpy
import pytest

from quantum_calculator.domain.numerical.problems import PotentialModel, ScaledGrid
from quantum_calculator.numerics.grid import (
    interior_positions,
    node_positions,
    spacing,
    weighted_norm,
    widened,
    with_boundary_nodes,
)
from quantum_calculator.numerics.hamiltonian import discrete_hamiltonian

UNIT_WELL = ScaledGrid(left=0.0, right=1.0, subintervals=8)
OSCILLATOR_DOMAIN = ScaledGrid(left=-2.0, right=2.0, subintervals=8)


def test_grid_with_n_subintervals_has_n_minus_one_interior_unknowns() -> None:
    assert spacing(UNIT_WELL) == 0.125
    assert len(node_positions(UNIT_WELL)) == 9
    assert len(interior_positions(UNIT_WELL)) == 7
    assert interior_positions(UNIT_WELL)[0] == 0.125
    assert interior_positions(UNIT_WELL)[-1] == 0.875


def test_free_particle_operator_has_the_second_difference_stencil() -> None:
    operator = discrete_hamiltonian(UNIT_WELL, PotentialModel.ZERO)

    assert operator.diagonal == pytest.approx(numpy.full(7, 64.0), rel=1e-15)
    assert operator.off_diagonal == pytest.approx(numpy.full(6, -32.0), rel=1e-15)


def test_harmonic_potential_only_adds_half_the_squared_position_to_the_diagonal() -> None:
    free = discrete_hamiltonian(OSCILLATOR_DOMAIN, PotentialModel.ZERO)
    bound = discrete_hamiltonian(OSCILLATOR_DOMAIN, PotentialModel.HARMONIC)
    positions = interior_positions(OSCILLATOR_DOMAIN)

    assert bound.diagonal - free.diagonal == pytest.approx(positions**2 / 2, rel=1e-15)
    assert bound.off_diagonal == pytest.approx(free.off_diagonal, rel=1e-15)


@pytest.mark.numerical
def test_operator_applied_to_a_parabola_vanishing_at_the_walls_is_exact() -> None:
    positions = interior_positions(UNIT_WELL)
    parabola = positions * (1.0 - positions)

    applied = discrete_hamiltonian(UNIT_WELL, PotentialModel.ZERO).apply(parabola)

    assert applied == pytest.approx(numpy.ones(7), abs=1e-13)


@pytest.mark.numerical
@pytest.mark.parametrize("mode", [1, 2, 5])
def test_sampled_sine_is_an_eigenvector_with_the_discrete_eigenvalue(mode: int) -> None:
    step = spacing(UNIT_WELL)
    sine = numpy.sin(mode * math.pi * interior_positions(UNIT_WELL))
    discrete_eigenvalue = (1.0 - math.cos(mode * math.pi * step)) / step**2

    applied = discrete_hamiltonian(UNIT_WELL, PotentialModel.ZERO).apply(sine)

    assert applied == pytest.approx(discrete_eigenvalue * sine, abs=1e-12)


def test_operator_acts_on_each_column_and_on_complex_amplitudes() -> None:
    operator = discrete_hamiltonian(UNIT_WELL, PotentialModel.ZERO)
    columns = numpy.arange(14, dtype=numpy.float64).reshape(7, 2)

    applied = operator.apply(columns.astype(numpy.complex128) * 1j)

    assert applied[:, 0] == pytest.approx(1j * operator.apply(columns[:, 0].copy()))
    assert applied[:, 1] == pytest.approx(1j * operator.apply(columns[:, 1].copy()))


def test_infinity_norm_is_the_largest_absolute_row_sum() -> None:
    assert discrete_hamiltonian(UNIT_WELL, PotentialModel.ZERO).infinity_norm() == 128.0


@pytest.mark.numerical
@pytest.mark.parametrize("level", [1, 2, 3, 7])
def test_inertia_count_places_each_discrete_level_without_diagonalizing(level: int) -> None:
    step = spacing(UNIT_WELL)
    operator = discrete_hamiltonian(UNIT_WELL, PotentialModel.ZERO)
    eigenvalue = (1.0 - math.cos(level * math.pi * step)) / step**2

    assert operator.eigenvalues_below(eigenvalue * (1 - 1e-9)) == level - 1
    assert operator.eigenvalues_below(eigenvalue * (1 + 1e-9)) == level


def test_dirichlet_values_are_restored_as_zeros_at_both_walls() -> None:
    restored = with_boundary_nodes(numpy.ones((7, 2)))

    assert restored.shape == (9, 2)
    assert restored[0].tolist() == [0.0, 0.0]
    assert restored[-1].tolist() == [0.0, 0.0]


@pytest.mark.numerical
def test_norm_integrates_over_the_grid_instead_of_summing_components() -> None:
    fine = ScaledGrid(left=0.0, right=1.0, subintervals=512)
    mode = math.sqrt(2.0) * numpy.sin(math.pi * interior_positions(fine))

    assert weighted_norm(fine, mode) == pytest.approx(1.0, abs=1e-12)
    assert numpy.linalg.norm(mode) == pytest.approx(math.sqrt(512.0), rel=1e-12)


def test_widening_keeps_the_spacing_and_the_center() -> None:
    wider = widened(OSCILLATOR_DOMAIN, 5, 4)

    assert (wider.left, wider.right, wider.subintervals) == (-2.5, 2.5, 10)
    assert spacing(wider) == spacing(OSCILLATOR_DOMAIN)
