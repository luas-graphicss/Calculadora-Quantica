import math
from dataclasses import dataclass

import numpy
from scipy import linalg

from quantum_calculator.domain.numerical.problems import PotentialModel, ScaledGrid
from quantum_calculator.numerics.evaluation import Samples
from quantum_calculator.numerics.failures import method_not_converged, non_finite_result
from quantum_calculator.numerics.grid import spacing
from quantum_calculator.numerics.hamiltonian import discrete_hamiltonian

EIGENSOLVER = "scipy.linalg.eigh_tridiagonal"

_SIGNIFICANT_FRACTION = 1e-6
_ENERGIES = "O espectro discreto"


@dataclass(frozen=True, slots=True)
class DiscreteEigenstates:
    energies: Samples
    modes: Samples


def lowest_eigenstates(
    grid: ScaledGrid, potential: PotentialModel, count: int
) -> DiscreteEigenstates:
    operator = discrete_hamiltonian(grid, potential)
    try:
        energies, vectors = linalg.eigh_tridiagonal(
            operator.diagonal, operator.off_diagonal, select="i", select_range=(0, count - 1)
        )
    except numpy.linalg.LinAlgError as error:
        raise method_not_converged(EIGENSOLVER, f"{error}.") from error
    modes = numpy.asarray(vectors, dtype=numpy.float64) / math.sqrt(spacing(grid))
    return DiscreteEigenstates(_finite(energies), modes * _orientations(modes))


def lowest_energies(grid: ScaledGrid, potential: PotentialModel, count: int) -> Samples:
    operator = discrete_hamiltonian(grid, potential)
    try:
        energies = linalg.eigvalsh_tridiagonal(
            operator.diagonal, operator.off_diagonal, select="i", select_range=(0, count - 1)
        )
    except numpy.linalg.LinAlgError as error:
        raise method_not_converged(EIGENSOLVER, f"{error}.") from error
    return _finite(energies)


def _finite(energies: object) -> Samples:
    values = numpy.asarray(energies, dtype=numpy.float64)
    if not numpy.all(numpy.isfinite(values)):
        raise non_finite_result(_ENERGIES)
    return values


def _orientations(modes: Samples) -> Samples:
    significant = numpy.abs(modes) > _SIGNIFICANT_FRACTION * numpy.max(numpy.abs(modes), axis=0)
    first_significant = numpy.argmax(significant, axis=0)
    return numpy.sign(modes[first_significant, numpy.arange(modes.shape[1])])
