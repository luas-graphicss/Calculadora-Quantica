from dataclasses import dataclass

from quantum_calculator.domain.execution import ExecutionBudget
from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.numerical.problems import NumericalProblem
from quantum_calculator.domain.run_record import EnvironmentManifest
from quantum_calculator.domain.verification import VerificationReport


@dataclass(frozen=True, slots=True)
class ErrorEstimate:
    value: float
    origin: str


@dataclass(frozen=True, slots=True)
class NumericalAnswer:
    name: str
    symbol: str
    label: str
    value: float
    unit: str
    estimate: ErrorEstimate | None


@dataclass(frozen=True, slots=True)
class SampleColumn:
    name: str
    symbol: str
    unit: str
    values: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class SampleTable:
    name: str
    title: str
    columns: tuple[SampleColumn, ...]

    @property
    def row_count(self) -> int:
        return len(self.columns[0].values) if self.columns else 0

    def column(self, name: str) -> SampleColumn:
        for column in self.columns:
            if column.name == name:
                return column
        raise KeyError(name)


@dataclass(frozen=True, slots=True)
class EffectiveParameter:
    name: str
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class NumericalSolverReport:
    nature: ResultNature
    answers: tuple[NumericalAnswer, ...]
    tables: tuple[SampleTable, ...]
    effective: tuple[EffectiveParameter, ...]
    warnings: tuple[str, ...]

    def answer(self, name: str) -> NumericalAnswer:
        for answer in self.answers:
            if answer.name == name:
                return answer
        raise KeyError(name)

    def table(self, name: str) -> SampleTable:
        for table in self.tables:
            if table.name == name:
                return table
        raise KeyError(name)


@dataclass(frozen=True, slots=True)
class NumericalPlan:
    method: MethodDescription
    budget: ExecutionBudget


@dataclass(frozen=True, slots=True)
class NumericalRunRecord:
    problem: NumericalProblem
    plan: NumericalPlan
    report: NumericalSolverReport
    verification: VerificationReport
    catalog_version: str
    constants_edition: str
    unit_registry_version: str
    environment: EnvironmentManifest
