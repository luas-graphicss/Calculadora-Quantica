import sys
from dataclasses import dataclass

import numpy
from numpy.typing import NDArray

from quantum_calculator.domain.numerical.problems import PotentialModel, ScaledGrid
from quantum_calculator.numerics.evaluation import Samples
from quantum_calculator.numerics.grid import interior_positions, spacing

_BELOW_ZERO = -sys.float_info.min


@dataclass(frozen=True, slots=True)
class TridiagonalOperator:
    diagonal: Samples
    off_diagonal: Samples

    def apply[Scalar: (numpy.float64, numpy.complex128)](
        self, vectors: NDArray[Scalar]
    ) -> NDArray[Scalar]:
        diagonal = self.diagonal.reshape(-1, *([1] * (vectors.ndim - 1)))
        coupling = self.off_diagonal.reshape(-1, *([1] * (vectors.ndim - 1)))
        applied = diagonal * vectors
        applied[:-1] += coupling * vectors[1:]
        applied[1:] += coupling * vectors[:-1]
        return applied

    def infinity_norm(self) -> float:
        row_sums = numpy.abs(self.diagonal)
        row_sums[:-1] += numpy.abs(self.off_diagonal)
        row_sums[1:] += numpy.abs(self.off_diagonal)
        return float(numpy.max(row_sums))

    def eigenvalues_below(self, threshold: float) -> int:
        shifted: list[float] = (self.diagonal - threshold).tolist()
        couplings: list[float] = [0.0, *(self.off_diagonal**2).tolist()]
        count = 0
        pivot = 1.0
        for entry, coupling in zip(shifted, couplings, strict=True):
            pivot = entry - coupling / pivot
            if pivot == 0.0:
                pivot = _BELOW_ZERO
            count += pivot < 0.0
        return count


def potential_samples(model: PotentialModel, positions: Samples) -> Samples:
    if model is PotentialModel.HARMONIC:
        return positions**2 / 2
    return numpy.zeros_like(positions)


def discrete_hamiltonian(grid: ScaledGrid, potential: PotentialModel) -> TridiagonalOperator:
    step = spacing(grid)
    positions = interior_positions(grid)
    return TridiagonalOperator(
        diagonal=1.0 / step**2 + potential_samples(potential, positions),
        off_diagonal=numpy.full(len(positions) - 1, -0.5 / step**2),
    )
