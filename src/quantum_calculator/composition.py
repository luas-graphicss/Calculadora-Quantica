from dataclasses import dataclass

from quantum_calculator.adapters.execution.runtime_environment import RuntimeEnvironmentProbe
from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.solve_problem import HomologatedMethod, SolveProblem
from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.catalog.card_catalog import HOMOLOGATED_CARDS, CardCatalog
from quantum_calculator.catalog.infinite_square_well import INFINITE_SQUARE_WELL_ENERGY_LEVEL
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.solvers.symbolic.infinite_square_well import InfiniteSquareWellSolver
from quantum_calculator.verification.infinite_square_well import InfiniteSquareWellVerifier


@dataclass(frozen=True, slots=True)
class Calculator:
    validator: ProblemValidator
    solve_problem: SolveProblem
    units: UnitRegistry


def build_calculator() -> Calculator:
    constants = Codata2022Constants()
    units = SiUnitRegistry(constants)
    validator = ProblemValidator(CardCatalog(HOMOLOGATED_CARDS), units, constants)
    methods = {
        INFINITE_SQUARE_WELL_ENERGY_LEVEL.method.identifier: HomologatedMethod(
            solver=InfiniteSquareWellSolver(constants),
            verifier=InfiniteSquareWellVerifier(constants),
        )
    }
    return Calculator(
        validator=validator,
        solve_problem=SolveProblem(validator, methods, constants, units, RuntimeEnvironmentProbe()),
        units=units,
    )
