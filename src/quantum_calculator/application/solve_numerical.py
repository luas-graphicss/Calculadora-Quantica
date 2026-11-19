from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial

from quantum_calculator.application.numerical.validator import NumericalValidator
from quantum_calculator.application.statements.budget import NUMERICAL_WORDING, budget_diagnostic
from quantum_calculator.catalog.listing import CATALOG_VERSION
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.execution import (
    BudgetExceededError,
    CancellationSignal,
    ExecutionBudget,
)
from quantum_calculator.domain.numerical.problems import NumericalProblem
from quantum_calculator.domain.numerical.report import (
    NumericalPlan,
    NumericalRunRecord,
    NumericalSolverReport,
)
from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.domain.ports import (
    CalculationExecutor,
    ConstantsEdition,
    EnvironmentProbe,
    NumericalSolver,
    NumericalVerifier,
    UnitRegistry,
)
from quantum_calculator.domain.verification import VerificationReport


@dataclass(frozen=True, slots=True)
class HomologatedNumericalMethod:
    solver: NumericalSolver
    verifier: NumericalVerifier


@dataclass(frozen=True, slots=True)
class NumericalOutcome:
    report: NumericalSolverReport
    verification: VerificationReport


def solve_and_verify_numerically(
    method: HomologatedNumericalMethod, problem: NumericalProblem
) -> NumericalOutcome:
    report = method.solver.solve(problem)
    return NumericalOutcome(report, method.verifier.verify(problem, report))


class SolveNumerical:
    def __init__(
        self,
        validator: NumericalValidator,
        methods: Mapping[str, HomologatedNumericalMethod],
        executor: CalculationExecutor,
        budget: ExecutionBudget,
        constants: ConstantsEdition,
        units: UnitRegistry,
        environment: EnvironmentProbe,
    ) -> None:
        self._validator = validator
        self._methods = methods
        self._executor = executor
        self._budget = budget
        self._constants = constants
        self._units = units
        self._environment = environment

    def execute(self, spec: NumericalSpec, cancellation: CancellationSignal) -> NumericalRunRecord:
        problem = self._validator.validate(spec)
        plan = NumericalPlan(problem.context.card.method, self._budget)
        method = self._methods[plan.method.identifier]
        try:
            outcome = self._executor.run(
                partial(solve_and_verify_numerically, method, problem), plan.budget, cancellation
            )
        except BudgetExceededError as error:
            diagnostic = budget_diagnostic(error.resource, plan.budget, NUMERICAL_WORDING)
            raise ProblemRejectedError((diagnostic,)) from error
        return NumericalRunRecord(
            problem=problem,
            plan=plan,
            report=outcome.report,
            verification=outcome.verification,
            catalog_version=CATALOG_VERSION,
            constants_edition=self._constants.label,
            unit_registry_version=self._units.version,
            environment=self._environment.describe(),
        )
