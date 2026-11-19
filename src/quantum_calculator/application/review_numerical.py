from dataclasses import dataclass

from quantum_calculator.application.numerical.validator import NumericalValidator
from quantum_calculator.domain.execution import ExecutionBudget
from quantum_calculator.domain.numerical.problems import NumericalProblem
from quantum_calculator.domain.numerical.report import NumericalPlan
from quantum_calculator.domain.numerical.spec import NumericalSpec


@dataclass(frozen=True, slots=True)
class NumericalReview:
    problem: NumericalProblem
    plan: NumericalPlan


class ReviewNumerical:
    def __init__(self, validator: NumericalValidator, budget: ExecutionBudget) -> None:
        self._validator = validator
        self._budget = budget

    def execute(self, spec: NumericalSpec) -> NumericalReview:
        problem = self._validator.validate(spec)
        return NumericalReview(problem, NumericalPlan(problem.context.card.method, self._budget))
