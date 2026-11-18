from collections.abc import Callable
from typing import Protocol

from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.domain.dimensions import Dimension
from quantum_calculator.domain.execution import CancellationSignal, ExecutionBudget
from quantum_calculator.domain.run_record import EnvironmentManifest
from quantum_calculator.domain.solution import SolverReport
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.symbolic_solution import SymbolicSolverReport
from quantum_calculator.domain.units import Unit
from quantum_calculator.domain.validated_problem import ValidatedProblem
from quantum_calculator.domain.verification import VerificationReport


class UnitRegistry(Protocol):
    @property
    def version(self) -> str: ...

    def find(self, symbol: str) -> Unit | None: ...

    def symbols_for(self, dimension: Dimension) -> tuple[str, ...]: ...

    def coherent_symbol(self, dimension: Dimension) -> str: ...


class ConstantsEdition(Protocol):
    @property
    def label(self) -> str: ...

    def find(self, identifier: str) -> PhysicalConstant | None: ...

    def identifiers_for(self, dimension: Dimension) -> tuple[str, ...]: ...


class Solver(Protocol):
    def solve(self, problem: ValidatedProblem) -> SolverReport: ...


class Verifier(Protocol):
    def verify(self, problem: ValidatedProblem, report: SolverReport) -> VerificationReport: ...


class StatementSolver(Protocol):
    def solve(self, problem: ValidatedStatement) -> SymbolicSolverReport: ...


class StatementVerifier(Protocol):
    def verify(
        self, problem: ValidatedStatement, report: SymbolicSolverReport
    ) -> VerificationReport: ...


class CalculationExecutor(Protocol):
    def run[Result](
        self, task: Callable[[], Result], budget: ExecutionBudget, cancellation: CancellationSignal
    ) -> Result: ...


class EnvironmentProbe(Protocol):
    def describe(self) -> EnvironmentManifest: ...


def require_constant(constants: ConstantsEdition, identifier: str) -> PhysicalConstant:
    constant = constants.find(identifier)
    if constant is None:
        raise LookupError(f"constants edition {constants.label} has no {identifier}")
    return constant
