from dataclasses import replace

from quantum_calculator.domain.ports import Solver
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.solution import SolverReport
from quantum_calculator.domain.validated_problem import ValidatedProblem


class DoubledEnergySolver:
    def __init__(self, honest: Solver) -> None:
        self._honest = honest

    def solve(self, problem: ValidatedProblem) -> SolverReport:
        report = self._honest.solve(problem)
        doubled = Quantity(2 * report.value.magnitude, report.value.dimension)
        return replace(report, value=doubled)
