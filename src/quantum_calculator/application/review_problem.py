from dataclasses import dataclass

from quantum_calculator.application.planning import plan_solution
from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.domain.problem_spec import ProblemSpec
from quantum_calculator.domain.solution import SolvePlan
from quantum_calculator.domain.validated_problem import ValidatedProblem


@dataclass(frozen=True, slots=True)
class ProblemReview:
    problem: ValidatedProblem
    plan: SolvePlan


class ReviewProblem:
    def __init__(self, validator: ProblemValidator) -> None:
        self._validator = validator

    def execute(self, spec: ProblemSpec) -> ProblemReview:
        problem = self._validator.validate(spec)
        return ProblemReview(problem=problem, plan=plan_solution(problem))
