import math

from quantum_calculator.domain.numerical.problems import PotentialModel, ScaledGrid


def scaled_energy(potential: PotentialModel, grid: ScaledGrid, level: int) -> float:
    if potential is PotentialModel.HARMONIC:
        return level - 0.5
    return (level * math.pi / (grid.right - grid.left)) ** 2 / 2
