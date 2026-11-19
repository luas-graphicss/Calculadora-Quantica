from dataclasses import replace

import numpy
from numpy.typing import NDArray

from quantum_calculator.domain.numerical.problems import ScaledGrid
from quantum_calculator.numerics.evaluation import Samples


def spacing(grid: ScaledGrid) -> float:
    return (grid.right - grid.left) / grid.subintervals


def interior_positions(grid: ScaledGrid) -> Samples:
    return node_positions(grid)[1:-1]


def node_positions(grid: ScaledGrid) -> Samples:
    return numpy.linspace(grid.left, grid.right, grid.subintervals + 1)


def with_boundary_nodes[Scalar: numpy.generic](interior: NDArray[Scalar]) -> NDArray[Scalar]:
    padding = [(1, 1)] + [(0, 0)] * (interior.ndim - 1)
    return numpy.pad(interior, padding)


def weighted_norm(grid: ScaledGrid, interior: NDArray[numpy.generic]) -> float:
    return float(numpy.sqrt(spacing(grid) * numpy.sum(numpy.abs(interior) ** 2)))


def with_subintervals(grid: ScaledGrid, subintervals: int) -> ScaledGrid:
    return replace(grid, subintervals=subintervals)


def widened(grid: ScaledGrid, factor_numerator: int, factor_denominator: int) -> ScaledGrid:
    center = (grid.left + grid.right) / 2
    half_width = (grid.right - grid.left) / 2 * factor_numerator / factor_denominator
    return ScaledGrid(
        left=center - half_width,
        right=center + half_width,
        subintervals=grid.subintervals * factor_numerator // factor_denominator,
    )
