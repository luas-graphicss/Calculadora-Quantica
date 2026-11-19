import numpy

from quantum_calculator.domain.numerical.problems import QuadratureProblem
from quantum_calculator.numerics.evaluation import Samples, evaluate


class Integrand:
    def __init__(self, problem: QuadratureProblem) -> None:
        self._expression = problem.integrand
        self._variable = problem.variable
        self._values = {item.name: item.value for item in problem.values}

    def __call__(self, position: float) -> float:
        return float(evaluate(self._expression, {**self._values, self._variable: position}))

    def sample(self, positions: Samples) -> Samples:
        values = evaluate(self._expression, {**self._values, self._variable: positions})
        return numpy.broadcast_to(values, positions.shape)
