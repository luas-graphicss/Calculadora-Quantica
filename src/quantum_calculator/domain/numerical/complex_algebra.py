import math
from itertools import product

from quantum_calculator.domain.numerical.problems import ComplexMatrix, ComplexVector


def norm(vector: ComplexVector) -> float:
    return math.sqrt(sum(abs(component) ** 2 for component in vector))


def inner_product(left: ComplexVector, right: ComplexVector) -> complex:
    return sum(
        (first.conjugate() * second for first, second in zip(left, right, strict=True)),
        start=0j,
    )


def is_square(matrix: ComplexMatrix, dimension: int) -> bool:
    return len(matrix) == dimension and all(len(row) == dimension for row in matrix)


def hermiticity_defect(matrix: ComplexMatrix) -> float:
    indices = range(len(matrix))
    return max(
        abs(matrix[row][column] - matrix[column][row].conjugate())
        for row, column in product(indices, indices)
    )


def orthonormality_defect(vectors: ComplexMatrix) -> float:
    indices = range(len(vectors))
    return max(
        abs(inner_product(vectors[first], vectors[second]) - (1.0 if first == second else 0.0))
        for first, second in product(indices, indices)
    )
