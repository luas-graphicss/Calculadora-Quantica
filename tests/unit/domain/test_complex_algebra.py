import math

import pytest

from quantum_calculator.domain.numerical.complex_algebra import (
    hermiticity_defect,
    inner_product,
    is_square,
    norm,
    orthonormality_defect,
)

PAULI_Y = ((0j, -1j), (1j, 0j))
RAISING = ((0j, 1 + 0j), (0j, 0j))
ROOT_HALF = math.sqrt(0.5)
X_BASIS = ((ROOT_HALF + 0j, ROOT_HALF + 0j), (ROOT_HALF + 0j, -ROOT_HALF + 0j))


def test_norm_is_the_euclidean_length_of_the_complex_components() -> None:
    assert norm((3 + 0j, 4j)) == pytest.approx(5.0, abs=1e-15)


def test_inner_product_conjugates_its_left_argument() -> None:
    assert inner_product((1j, 0j), (1 + 0j, 0j)) == -1j


def test_pauli_matrix_equals_its_conjugate_transpose() -> None:
    assert hermiticity_defect(PAULI_Y) == 0.0


def test_raising_operator_differs_from_its_conjugate_transpose() -> None:
    assert hermiticity_defect(RAISING) == 1.0


def test_x_basis_vectors_are_orthonormal_to_rounding() -> None:
    assert orthonormality_defect(X_BASIS) < 1e-15


def test_unnormalized_vectors_are_not_an_orthonormal_basis() -> None:
    assert orthonormality_defect(((1 + 0j, 1 + 0j), (1 + 0j, -1 + 0j))) == pytest.approx(1.0)


def test_matrix_with_a_short_row_is_not_square() -> None:
    assert is_square(PAULI_Y, 2)
    assert not is_square(((0j, 1j), (1j,)), 2)
