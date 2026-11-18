from dataclasses import dataclass
from enum import StrEnum

from quantum_calculator.domain.execution import ExecutionBudget
from quantum_calculator.domain.expressions import Equation, Expression, Statement
from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.run_record import EnvironmentManifest
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.verification import VerificationReport


class ConditionRelation(StrEnum):
    NONZERO = "nonzero"
    POSITIVE = "positive"
    NONNEGATIVE = "nonnegative"


class ConditionScope(StrEnum):
    POINTWISE = "pointwise"
    INTEGRATION_INTERVAL = "integration_interval"


@dataclass(frozen=True, slots=True)
class DomainCondition:
    relation: ConditionRelation
    expression: Expression
    scope: ConditionScope = ConditionScope.POINTWISE


@dataclass(frozen=True, slots=True)
class SpecialCase:
    when: Equation
    answer: Equation


@dataclass(frozen=True, slots=True)
class SymbolicStep:
    description: str
    expression: Statement


@dataclass(frozen=True, slots=True)
class SymbolicSolverReport:
    answer: Equation
    nature: ResultNature
    validity: tuple[DomainCondition, ...]
    assumptions: tuple[DomainCondition, ...]
    special_cases: tuple[SpecialCase, ...]
    arbitrary_constants: tuple[str, ...]
    certificate: Expression | None
    steps: tuple[SymbolicStep, ...]


@dataclass(frozen=True, slots=True)
class StatementPlan:
    method: MethodDescription
    budget: ExecutionBudget


@dataclass(frozen=True, slots=True)
class StatementRunRecord:
    problem: ValidatedStatement
    plan: StatementPlan
    report: SymbolicSolverReport
    verification: VerificationReport
    catalog_version: str
    unit_registry_version: str
    environment: EnvironmentManifest
