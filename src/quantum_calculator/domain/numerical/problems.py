from dataclasses import dataclass
from enum import StrEnum

from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.domain.expressions import Expression
from quantum_calculator.domain.numerical.cards import NumericalCard
from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.domain.rounding import RoundingPolicy
from quantum_calculator.domain.units import Unit
from quantum_calculator.domain.validated_problem import ConfirmedHypothesis


@dataclass(frozen=True, slots=True)
class InterpretedInput:
    name: str
    label: str
    value: str
    origin: str


@dataclass(frozen=True, slots=True)
class ResolutionSetting:
    name: str
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class ResourceEstimate:
    memory_bytes: int
    operations: int


@dataclass(frozen=True, slots=True)
class NumericalContext:
    spec: NumericalSpec
    card: NumericalCard
    hypotheses: tuple[ConfirmedHypothesis, ...]
    inputs: tuple[InterpretedInput, ...]
    resolution: tuple[ResolutionSetting, ...]
    constants: tuple[PhysicalConstant, ...]
    rounding: RoundingPolicy
    estimate: ResourceEstimate


@dataclass(frozen=True, slots=True)
class SymbolValue:
    name: str
    value: float


@dataclass(frozen=True, slots=True)
class QuadratureProblem:
    context: NumericalContext
    integrand: Expression
    variable: str
    lower: float
    upper: float
    values: tuple[SymbolValue, ...]
    result_unit: str
    absolute_tolerance: float
    relative_tolerance: float
    subdivision_limit: int


@dataclass(frozen=True, slots=True)
class OdeComponent:
    function: str
    unit: str
    derivative: Expression
    initial_value: float


@dataclass(frozen=True, slots=True)
class InitialValueProblem:
    context: NumericalContext
    variable: str
    variable_unit: str
    components: tuple[OdeComponent, ...]
    values: tuple[SymbolValue, ...]
    start: float
    end: float
    samples: int
    relative_tolerance: float
    absolute_tolerance: float


type ComplexVector = tuple[complex, ...]
type ComplexMatrix = tuple[ComplexVector, ...]


@dataclass(frozen=True, slots=True)
class FiniteBasisProblem:
    context: NumericalContext
    state: ComplexVector
    normalize: bool
    observable: ComplexMatrix
    unit: str
    basis: ComplexMatrix | None
    tolerance: float


class PotentialModel(StrEnum):
    ZERO = "zero"
    HARMONIC = "harmonic"


@dataclass(frozen=True, slots=True)
class PhysicalScales:
    length: float
    energy: float
    time: float


@dataclass(frozen=True, slots=True)
class ScaledGrid:
    left: float
    right: float
    subintervals: int


@dataclass(frozen=True, slots=True)
class SpectrumProblem:
    context: NumericalContext
    scales: PhysicalScales
    grid: ScaledGrid
    potential: PotentialModel
    levels: int
    energy_unit: Unit
    is_truncated_domain: bool


@dataclass(frozen=True, slots=True)
class EvolutionProblem:
    context: NumericalContext
    scales: PhysicalScales
    grid: ScaledGrid
    potential: PotentialModel
    coefficients: ComplexVector
    normalize: bool
    scaled_duration: float
    steps: int
    samples: int


type NumericalProblem = (
    QuadratureProblem
    | InitialValueProblem
    | FiniteBasisProblem
    | SpectrumProblem
    | EvolutionProblem
)
