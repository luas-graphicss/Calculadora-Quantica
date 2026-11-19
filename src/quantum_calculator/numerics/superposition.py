import math

import numpy

from quantum_calculator.domain.numerical.problems import EvolutionProblem
from quantum_calculator.numerics.finite_basis import Amplitudes

_FULL_TURN = 2 * math.pi


def mode_coefficients(problem: EvolutionProblem) -> Amplitudes:
    coefficients = numpy.array(problem.coefficients, dtype=numpy.complex128)
    return coefficients / numpy.linalg.norm(coefficients) if problem.normalize else coefficients


def beating_pair(problem: EvolutionProblem) -> tuple[int, int] | None:
    populated = [index for index, value in enumerate(problem.coefficients) if value != 0]
    return (populated[0], populated[1]) if len(populated) > 1 else None


def wrapped(angle: float) -> float:
    return math.remainder(angle, _FULL_TURN)


def relative_phase(amplitudes: Amplitudes, pair: tuple[int, int]) -> float:
    lower, upper = pair
    return float(numpy.angle(amplitudes[upper] * numpy.conj(amplitudes[lower])))
