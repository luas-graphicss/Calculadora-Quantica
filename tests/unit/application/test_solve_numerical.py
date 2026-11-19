import multiprocessing
import threading

import pytest

from quantum_calculator.adapters.execution.process_executor import ProcessExecutor
from quantum_calculator.adapters.execution.runtime_environment import RuntimeEnvironmentProbe
from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.numerical.validator import NumericalValidator
from quantum_calculator.application.review_numerical import ReviewNumerical
from quantum_calculator.application.solve_numerical import SolveNumerical
from quantum_calculator.application.statements.budget import (
    DEFAULT_SYMBOLIC_BUDGET,
    symbolic_budget,
)
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
from quantum_calculator.method_registry import numerical_methods
from support.documents import ProblemDocument
from support.execution import InlineExecutor, RaisingExecutor
from support.numerical_documents import (
    ACCEPTED_FILES,
    NUMERICAL,
    REJECTED,
    numerical_document,
    numerical_spec,
    reference_spec,
)

WELL = reference_spec("electron_box_1nm_discrete")
STARVED = symbolic_budget(0.05)


class UseCaseFactory:
    def __init__(
        self, validator: NumericalValidator, units: SiUnitRegistry, constants: Codata2022Constants
    ) -> None:
        self._validator = validator
        self._units = units
        self._constants = constants

    def running_on(
        self, executor: CalculationExecutor, budget: ExecutionBudget = DEFAULT_SYMBOLIC_BUDGET
    ) -> SolveNumerical:
        return SolveNumerical(
            self._validator,
            numerical_methods(),
            executor,
            budget,
            self._constants,
            self._units,
            RuntimeEnvironmentProbe(),
        )


@pytest.fixture
def use_case(
    numerical_validator: NumericalValidator, units: SiUnitRegistry, constants: Codata2022Constants
) -> UseCaseFactory:
    return UseCaseFactory(numerical_validator, units, constants)


def test_reference_problem_yields_a_verified_record_with_its_plan_and_versions(
    use_case: UseCaseFactory, units: SiUnitRegistry, constants: Codata2022Constants
) -> None:
    record = use_case.running_on(InlineExecutor()).execute(WELL, NeverCancelled())

    assert record.verification.status is VerificationStatus.PASSED
    assert record.plan.method == record.problem.context.card.method
    assert record.plan.budget == DEFAULT_SYMBOLIC_BUDGET
    assert record.catalog_version == CATALOG_VERSION
    assert record.constants_edition == constants.label
    assert record.unit_registry_version == units.version
    assert {library.interface for library in record.environment.linear_algebra} == {
        "blas",
        "lapack",
    }


@pytest.mark.parametrize("file", ACCEPTED_FILES)
def test_report_carries_plain_finite_numbers_only(use_case: UseCaseFactory, file: str) -> None:
    spec = numerical_spec(ProblemDocument.load(NUMERICAL / file))

    report = use_case.running_on(InlineExecutor()).execute(spec, NeverCancelled()).report

    values = [answer.value for answer in report.answers]
    values += [
        value for table in report.tables for column in table.columns for value in column.values
    ]
    assert values
    assert all(
        type(value) is float and value == value and abs(value) != float("inf") for value in values
    )


def test_problem_refused_at_validation_never_reaches_the_executor(
    use_case: UseCaseFactory,
) -> None:
    oversized = numerical_spec(ProblemDocument.load(REJECTED / "resource_limit.json"))
    solve = use_case.running_on(RaisingExecutor(AssertionError("the calculation was started")))

    with pytest.raises(ProblemRejectedError) as rejection:
        solve.execute(oversized, NeverCancelled())

    assert rejection.value.category is DiagnosticCategory.BUDGET_EXCEEDED


@pytest.mark.parametrize(
    ("resource", "code"),
    [
        (BudgetResource.WALL_TIME, DiagnosticCode.TIME_BUDGET_EXCEEDED),
        (BudgetResource.CPU_TIME, DiagnosticCode.TIME_BUDGET_EXCEEDED),
        (BudgetResource.MEMORY, DiagnosticCode.MEMORY_BUDGET_EXCEEDED),
    ],
)
def test_exhausted_budget_is_a_numerical_budget_diagnostic_and_never_a_partial_result(
    use_case: UseCaseFactory, resource: BudgetResource, code: DiagnosticCode
) -> None:
    solve = use_case.running_on(RaisingExecutor(BudgetExceededError(resource)))

    with pytest.raises(ProblemRejectedError) as rejection:
        solve.execute(WELL, NeverCancelled())

    (diagnostic,) = rejection.value.diagnostics
    assert diagnostic.code is code
    assert rejection.value.category is DiagnosticCategory.BUDGET_EXCEEDED
    assert diagnostic.message.startswith("O cálculo numérico passou do limite")
    assert "nenhum resultado parcial" in diagnostic.message


def test_problem_crosses_the_process_boundary_and_comes_back_verified(
    use_case: UseCaseFactory,
) -> None:
    inline = use_case.running_on(InlineExecutor()).execute(WELL, NeverCancelled())

    isolated = use_case.running_on(ProcessExecutor()).execute(WELL, NeverCancelled())

    assert isolated.report == inline.report
    assert isolated.verification == inline.verification
    assert multiprocessing.active_children() == []


def test_method_that_does_not_converge_yields_a_diagnostic_and_no_record(
    use_case: UseCaseFactory,
) -> None:
    divergent = numerical_spec(ProblemDocument.load(REJECTED / "divergent_integral.json"))

    with pytest.raises(ProblemRejectedError) as rejection:
        use_case.running_on(ProcessExecutor()).execute(divergent, NeverCancelled())

    (diagnostic,) = rejection.value.diagnostics
    assert rejection.value.category is DiagnosticCategory.NON_CONVERGENT
    assert diagnostic.code is DiagnosticCode.METHOD_NOT_CONVERGED
    assert "Nenhuma resposta foi aprovada" in diagnostic.message
    assert multiprocessing.active_children() == []


def test_calculation_over_its_time_budget_leaves_the_next_one_usable(
    use_case: UseCaseFactory,
) -> None:
    executor = ProcessExecutor()

    with pytest.raises(ProblemRejectedError) as rejection:
        use_case.running_on(executor, STARVED).execute(WELL, NeverCancelled())
    record = use_case.running_on(executor).execute(WELL, NeverCancelled())

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
        solve.execute(WELL, cancellation)
    record = solve.execute(WELL, NeverCancelled())

    assert record.verification.status is VerificationStatus.PASSED
    assert multiprocessing.active_children() == []


def test_review_plans_the_card_method_under_the_budget_without_calculating(
    numerical_validator: NumericalValidator,
) -> None:
    review = ReviewNumerical(numerical_validator, DEFAULT_SYMBOLIC_BUDGET).execute(
        numerical_spec(numerical_document("electron_box_1nm_beat"))
    )

    assert review.problem.context.card.identifier == "quantum.infinite_square_well.time_evolution"
    assert review.plan.method.identifier == "finite_difference.crank_nicolson"
    assert review.plan.budget == DEFAULT_SYMBOLIC_BUDGET
