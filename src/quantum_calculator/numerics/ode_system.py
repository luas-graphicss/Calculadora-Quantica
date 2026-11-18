import numpy

from quantum_calculator.domain.numerical.problems import InitialValueProblem
from quantum_calculator.numerics.evaluation import Samples, evaluate


class RightHandSide:
    def __init__(self, problem: InitialValueProblem) -> None:
        self._variable = problem.variable
        self._components = problem.components
        self._values = {item.name: item.value for item in problem.values}

    def __call__(self, instant: float, state: Samples) -> Samples:
        bindings = {
            **self._values,
            self._variable: instant,
            **{
                component.function: float(state[index])
                for index, component in enumerate(self._components)
            },
        }
        return numpy.array(
            [float(evaluate(component.derivative, bindings)) for component in self._components]
        )


def initial_state(problem: InitialValueProblem) -> Samples:
    return numpy.array([component.initial_value for component in problem.components])


def sample_instants(problem: InitialValueProblem) -> Samples:
    return numpy.linspace(problem.start, problem.end, problem.samples)
