import multiprocessing
import threading

import pytest

from quantum_calculator.adapters.execution.process_executor import ProcessExecutor
from quantum_calculator.adapters.execution.runtime_environment import RuntimeEnvironmentProbe
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.review_statement import ReviewStatement
from quantum_calculator.application.solve_statement import SolveStatement
from quantum_calculator.application.statements.budget import (
    DEFAULT_SYMBOLIC_BUDGET,
    symbolic_budget,
)
from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.catalog.listing import CATALOG_VERSION
from quantum_calculator.domain.diagnostics import (
    DiagnosticCategory,
    DiagnosticCode,
    ProblemRejectedError,
)
from quantum_calculator.domain.execution import (
    BudgetExceededError,
    BudgetResource,
    CalculationCancelledError,
    ExecutionBudget,
    NeverCancelled,
)
from quantum_calculator.domain.ports import CalculationExecutor
from quantum_calculator.domain.verification import VerificationStatus
from quantum_calculator.method_registry import statement_methods
from support.execution import InlineExecutor, RaisingExecutor
from support.statements import CALCULUS, DECAY, DECAY_CONDITION, DECAY_EQUATION, statement_spec

PRODUCT_RULE = statement_spec("diff(x^2*sin(x), x)", CALCULUS)
STARVED = symbolic_budget(0.05)


class UseCaseFactory:
    def __init__(self, validator: StatementValidator, units: SiUnitRegistry) -> None:
        self._validator = validator
        self._units = units

    def running_on(
        self, executor: CalculationExecutor, budget: ExecutionBudget = DEFAULT_SYMBOLIC_BUDGET
    ) -> SolveStatement:
        return SolveStatement(
            self._validator,
            statement_methods(),
            executor,
            budget,
            self._units,
            RuntimeEnvironmentProbe(),
        )


@pytest.fixture
def use_case(statement_validator: StatementValidator, units: SiUnitRegistry) -> UseCaseFactory:
    return UseCaseFactory(statement_validator, units)


def test_reference_statement_yields_a_verified_record_with_its_plan_and_versions(
    use_case: UseCaseFactory, units: SiUnitRegistry
) -> None:
    record = use_case.running_on(InlineExecutor()).execute(PRODUCT_RULE, NeverCancelled())

    assert record.verification.status is VerificationStatus.PASSED
    assert record.plan.method == record.problem.card.method
    assert record.plan.budget == DEFAULT_SYMBOLIC_BUDGET
    assert record.catalog_version == CATALOG_VERSION
    assert record.unit_registry_version == units.version
    assert record.environment.package_name == "quantum-calculator"


def test_candidate_with_the_wrong_initial_value_is_recorded_as_a_failed_review(
    use_case: UseCaseFactory,
) -> None:
    spec = statement_spec(
        DECAY_EQUATION, DECAY, conditions=[DECAY_CONDITION], candidate="y(t) = 2*y_0*exp(-k*t)"
    )

    record = use_case.running_on(InlineExecutor()).execute(spec, NeverCancelled())

    failed = {
        check.identifier
        for check in record.verification.checks
        if check.status is VerificationStatus.FAILED
    }
    assert failed == {"initial_condition"}
    assert record.verification.status is VerificationStatus.FAILED


def test_statement_refused_at_validation_never_reaches_the_executor(
    use_case: UseCaseFactory,
) -> None:
    undeclared = statement_spec("diff(z^2, x)", CALCULUS)
    solve = use_case.running_on(RaisingExecutor(BudgetExceededError(BudgetResource.WALL_TIME)))

    with pytest.raises(ProblemRejectedError) as rejection:
        solve.execute(undeclared, NeverCancelled())

    assert rejection.value.category is DiagnosticCategory.INVALID_INPUT


@pytest.mark.parametrize(
    ("resource", "code"),
    [
        (BudgetResource.WALL_TIME, DiagnosticCode.TIME_BUDGET_EXCEEDED),
        (BudgetResource.CPU_TIME, DiagnosticCode.TIME_BUDGET_EXCEEDED),
        (BudgetResource.MEMORY, DiagnosticCode.MEMORY_BUDGET_EXCEEDED),
        (BudgetResource.RECURSION_DEPTH, DiagnosticCode.EXPRESSION_TOO_DEEP),
    ],
)
def test_exhausted_budget_is_a_budget_diagnostic_and_never_a_partial_result(
    use_case: UseCaseFactory, resource: BudgetResource, code: DiagnosticCode
) -> None:
    solve = use_case.running_on(RaisingExecutor(BudgetExceededError(resource)))

    with pytest.raises(ProblemRejectedError) as rejection:
        solve.execute(PRODUCT_RULE, NeverCancelled())

    (diagnostic,) = rejection.value.diagnostics
    assert diagnostic.code is code
    assert rejection.value.category is DiagnosticCategory.BUDGET_EXCEEDED
    assert "nenhum resultado parcial" in diagnostic.message


def test_calculation_over_its_time_budget_leaves_the_next_one_usable(
    use_case: UseCaseFactory,
) -> None:
    executor = ProcessExecutor()

    with pytest.raises(ProblemRejectedError) as rejection:
        use_case.running_on(executor, STARVED).execute(PRODUCT_RULE, NeverCancelled())
    record = use_case.running_on(executor).execute(PRODUCT_RULE, NeverCancelled())

    assert rejection.value.diagnostics[0].code is DiagnosticCode.TIME_BUDGET_EXCEEDED
    assert record.verification.status is VerificationStatus.PASSED
    assert multiprocessing.active_children() == []


def test_cancelled_calculation_returns_nothing_and_the_next_one_runs(
    use_case: UseCaseFactory,
) -> None:
    solve = use_case.running_on(ProcessExecutor())
    cancellation = threading.Event()
    cancellation.set()

    with pytest.raises(CalculationCancelledError):
        solve.execute(PRODUCT_RULE, cancellation)
    record = solve.execute(PRODUCT_RULE, NeverCancelled())

    assert record.verification.status is VerificationStatus.PASSED
    assert multiprocessing.active_children() == []


def test_review_plans_the_card_method_under_the_budget_without_calculating(
    statement_validator: StatementValidator,
) -> None:
    review = ReviewStatement(statement_validator, DEFAULT_SYMBOLIC_BUDGET).execute(PRODUCT_RULE)

    assert review.problem.card.identifier == "calculus.derivative"
    assert review.plan.method.identifier == "symbolic.differentiation"
    assert review.plan.budget == DEFAULT_SYMBOLIC_BUDGET
