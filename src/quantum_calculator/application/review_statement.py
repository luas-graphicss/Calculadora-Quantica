from dataclasses import dataclass

from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.domain.execution import ExecutionBudget
from quantum_calculator.domain.statements import StatementSpec, ValidatedStatement
from quantum_calculator.domain.symbolic_solution import StatementPlan


@dataclass(frozen=True, slots=True)
class StatementReview:
    problem: ValidatedStatement
    plan: StatementPlan


class ReviewStatement:
    def __init__(self, validator: StatementValidator, budget: ExecutionBudget) -> None:
        self._validator = validator
        self._budget = budget

    def execute(self, spec: StatementSpec) -> StatementReview:
        problem = self._validator.validate(spec)
        return StatementReview(problem, StatementPlan(problem.card.method, self._budget))
