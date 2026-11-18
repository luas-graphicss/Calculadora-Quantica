import numpy
from numpy.typing import NDArray

from quantum_calculator.domain.numerical.problems import FiniteBasisProblem

type Amplitudes = NDArray[numpy.complex128]


def prepared_state(problem: FiniteBasisProblem) -> Amplitudes:
    state = numpy.array(problem.state, dtype=numpy.complex128)
    return state / numpy.linalg.norm(state) if problem.normalize else state


def observable_matrix(problem: FiniteBasisProblem) -> Amplitudes:
    return numpy.array(problem.observable, dtype=numpy.complex128)


def operator_scale(matrix: Amplitudes) -> float:
    return max(1.0, float(numpy.max(numpy.sum(numpy.abs(matrix), axis=1))))
