from quantum_calculator.domain.solution import SolvePlan
from quantum_calculator.domain.validated_problem import ValidatedProblem


def plan_solution(problem: ValidatedProblem) -> SolvePlan:
    return SolvePlan(method=problem.card.method, rounding=problem.output.rounding)
