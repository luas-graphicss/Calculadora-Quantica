from dataclasses import dataclass

from quantum_calculator.adapters.execution.process_executor import ProcessExecutor
from quantum_calculator.adapters.execution.runtime_environment import RuntimeEnvironmentProbe
from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.numerical.validator import NumericalValidator
from quantum_calculator.application.review_numerical import ReviewNumerical
from quantum_calculator.application.review_problem import ReviewProblem
from quantum_calculator.application.review_statement import ReviewStatement
from quantum_calculator.application.solve_numerical import SolveNumerical
from quantum_calculator.application.solve_problem import SolveProblem
from quantum_calculator.application.solve_statement import SolveStatement
from quantum_calculator.application.statements.budget import DEFAULT_SYMBOLIC_BUDGET
from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.catalog.card_catalog import HOMOLOGATED_CARDS, CardCatalog
from quantum_calculator.catalog.listing import catalog_listing
from quantum_calculator.catalog.numerical_catalog import (
    HOMOLOGATED_NUMERICAL_CARDS,
    NumericalCatalog,
)
from quantum_calculator.catalog.statement_catalog import (
    HOMOLOGATED_STATEMENT_CARDS,
    StatementCatalog,
)
from quantum_calculator.domain.cards import CatalogListing
from quantum_calculator.domain.execution import ExecutionBudget
from quantum_calculator.domain.ports import CalculationExecutor, UnitRegistry
from quantum_calculator.method_registry import (
    numerical_methods,
    problem_methods,
    statement_methods,
)


@dataclass(frozen=True, slots=True)
class Calculator:
    review_problem: ReviewProblem
    solve_problem: SolveProblem
    review_statement: ReviewStatement
    solve_statement: SolveStatement
    review_numerical: ReviewNumerical
    solve_numerical: SolveNumerical
    catalog: CatalogListing
    numerical_cards: frozenset[str]
    units: UnitRegistry


def build_calculator(
    budget: ExecutionBudget = DEFAULT_SYMBOLIC_BUDGET, executor: CalculationExecutor | None = None
) -> Calculator:
    constants = Codata2022Constants()
    units = SiUnitRegistry(constants)
    environment = RuntimeEnvironmentProbe()
    process = executor or ProcessExecutor()
    problems = ProblemValidator(CardCatalog(HOMOLOGATED_CARDS), units, constants)
    statements = StatementValidator(StatementCatalog(HOMOLOGATED_STATEMENT_CARDS), units)
    numerical = NumericalValidator(NumericalCatalog(HOMOLOGATED_NUMERICAL_CARDS), units, constants)
    return Calculator(
        review_problem=ReviewProblem(problems),
        solve_problem=SolveProblem(
            problems, problem_methods(constants), constants, units, environment
        ),
        review_statement=ReviewStatement(statements, budget),
        solve_statement=SolveStatement(
            statements, statement_methods(), process, budget, units, environment
        ),
        review_numerical=ReviewNumerical(numerical, budget),
        solve_numerical=SolveNumerical(
            numerical, numerical_methods(), process, budget, constants, units, environment
        ),
        catalog=catalog_listing(),
        numerical_cards=frozenset(card.identifier for card in HOMOLOGATED_NUMERICAL_CARDS),
        units=units,
    )
