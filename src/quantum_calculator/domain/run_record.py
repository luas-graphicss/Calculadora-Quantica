from dataclasses import dataclass

from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.domain.solution import SolvePlan, SolverReport
from quantum_calculator.domain.validated_problem import ValidatedProblem
from quantum_calculator.domain.verification import VerificationReport


@dataclass(frozen=True, slots=True)
class DependencyVersion:
    name: str
    version: str


@dataclass(frozen=True, slots=True)
class EnvironmentManifest:
    package_name: str
    package_version: str
    python_implementation: str
    python_version: str
    platform: str
    dependencies: tuple[DependencyVersion, ...]


@dataclass(frozen=True, slots=True)
class RunRecord:
    problem: ValidatedProblem
    plan: SolvePlan
    report: SolverReport
    verification: VerificationReport
    constants: tuple[PhysicalConstant, ...]
    constants_edition: str
    unit_registry_version: str
    environment: EnvironmentManifest
