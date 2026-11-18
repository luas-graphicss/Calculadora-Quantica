from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial

from quantum_calculator.application.statements.budget import budget_diagnostic
from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.catalog.listing import CATALOG_VERSION
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.execution import (
    BudgetExceededError,
    CancellationSignal,
    ExecutionBudget,
)
from quantum_calculator.domain.ports import (
    CalculationExecutor,
    EnvironmentProbe,
    StatementSolver,
    StatementVerifier,
    UnitRegistry,
)
from quantum_calculator.domain.statements import StatementSpec, ValidatedStatement
from quantum_calculator.domain.symbolic_solution import (
    StatementPlan,
    StatementRunRecord,
    SymbolicSolverReport,
)
from quantum_calculator.domain.verification import VerificationReport


@dataclass(frozen=True, slots=True)
class HomologatedStatementMethod:
    solver: StatementSolver
    verifier: StatementVerifier


@dataclass(frozen=True, slots=True)
class SymbolicOutcome:
    report: SymbolicSolverReport
    verification: VerificationReport


def solve_and_verify(
    method: HomologatedStatementMethod, problem: ValidatedStatement
) -> SymbolicOutcome:
    report = method.solver.solve(problem)
    return SymbolicOutcome(report, method.verifier.verify(problem, report))


class SolveStatement:
    def __init__(
        self,
        validator: StatementValidator,
        methods: Mapping[str, HomologatedStatementMethod],
        executor: CalculationExecutor,
        budget: ExecutionBudget,
        units: UnitRegistry,
        environment: EnvironmentProbe,
    ) -> None:
        self._validator = validator
        self._methods = methods
        self._executor = executor
        self._budget = budget
        self._units = units
        self._environment = environment

    def execute(self, spec: StatementSpec, cancellation: CancellationSignal) -> StatementRunRecord:
        problem = self._validator.validate(spec)
        plan = StatementPlan(problem.card.method, self._budget)
        method = self._methods[plan.method.identifier]
        try:
            outcome = self._executor.run(
                partial(solve_and_verify, method, problem), plan.budget, cancellation
            )
        except BudgetExceededError as error:
            diagnostic = budget_diagnostic(error.resource, plan.budget)
            raise ProblemRejectedError((diagnostic,)) from error
        return StatementRunRecord(
            problem=problem,
            plan=plan,
            report=outcome.report,
            verification=outcome.verification,
            catalog_version=CATALOG_VERSION,
            unit_registry_version=self._units.version,
            environment=self._environment.describe(),
        )
