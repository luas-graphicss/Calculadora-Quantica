import hashlib
import math
from collections.abc import Mapping
from fractions import Fraction

from quantum_calculator.domain.dimensions import ENERGY
from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.numerical.cards import NumericalCard, NumericalFamily
from quantum_calculator.domain.numerical.problems import (
    ComplexMatrix,
    ComplexVector,
    EvolutionProblem,
    FiniteBasisProblem,
    InitialValueProblem,
    NumericalContext,
    OdeComponent,
    PhysicalScales,
    PotentialModel,
    QuadratureProblem,
    ResourceEstimate,
    ScaledGrid,
    SpectrumProblem,
    SymbolValue,
)
from quantum_calculator.domain.numerical.report import NumericalSolverReport
from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.domain.problem_spec import SourceDocument
from quantum_calculator.domain.rounding import RoundingPolicy
from quantum_calculator.domain.statements import SymbolRole
from quantum_calculator.domain.units import Unit
from quantum_calculator.domain.verification import VerificationReport, VerificationStatus
from support.notation import SymbolTable, declared, read_expression_text, symbol_table

VARIABLE = "t"
PLANCK = 6.62607015e-34
REDUCED_PLANCK = PLANCK / (2 * math.pi)
ELECTRON_MASS = 9.1093837139e-31
ELECTRON_VOLT_IN_JOULES = Fraction("1.602176634e-19")
ELECTRON_VOLT = Unit("eV", ENERGY, ELECTRON_VOLT_IN_JOULES, ("electron_volt",))
JOULE = Unit("J", ENERGY, Fraction(1))
NANOMETER = 1e-9
UNIT_WELL_GROUND_ENERGY = math.pi**2 / 2

_SOURCE_TEXT = "{}"
_SPEC = NumericalSpec(
    source=SourceDocument(_SOURCE_TEXT, hashlib.sha256(_SOURCE_TEXT.encode()).hexdigest()),
    schema_version="1.0",
    card_identifier="bench.numerical",
    description=None,
    hypotheses=None,
    parameters=None,
    notation=None,
    symbols=None,
    statement=None,
    equations=None,
    conditions=None,
    state=None,
    observable=None,
    basis=None,
    initial_state=None,
    numerics=None,
    requested=None,
)


def bench_context(family: NumericalFamily) -> NumericalContext:
    card = NumericalCard(
        identifier="bench.numerical",
        version="1.0.0",
        area="bench",
        problem_type="bench",
        title="Problema montado direto no domínio para testar um método",
        domain=("Só para testes.",),
        family=family,
        required_sections=frozenset(),
        optional_sections=frozenset(),
        hypotheses=(),
        method=MethodDescription("bench.method", ResultNature.APPROXIMATE, "Só para testes.", ()),
        limitations=("Só para testes.",),
        example="",
    )
    return NumericalContext(
        spec=_SPEC,
        card=card,
        hypotheses=(),
        inputs=(),
        resolution=(),
        constants=(),
        rounding=RoundingPolicy(10),
        estimate=ResourceEstimate(memory_bytes=0, operations=0),
    )


def quadrature_problem(
    integrand: str,
    lower: float,
    upper: float,
    *,
    absolute_tolerance: float = 1e-12,
    relative_tolerance: float = 1e-12,
    subdivision_limit: int = 50,
    values: Mapping[str, float] | None = None,
) -> QuadratureProblem:
    parameters = values or {}
    return QuadratureProblem(
        context=bench_context(NumericalFamily.QUADRATURE),
        integrand=read_expression_text(integrand, _symbols(("x",), parameters)),
        variable="x",
        lower=lower,
        upper=upper,
        values=_symbol_values(parameters),
        result_unit="1",
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        subdivision_limit=subdivision_limit,
    )


def initial_value_problem(
    derivatives: Mapping[str, str],
    initial_values: Mapping[str, float],
    end: float,
    samples: int,
    *,
    relative_tolerance: float = 1e-10,
    absolute_tolerance: float = 1e-12,
    values: Mapping[str, float] | None = None,
) -> InitialValueProblem:
    parameters = values or {}
    symbols = _symbols((VARIABLE,), parameters, tuple(derivatives))
    return InitialValueProblem(
        context=bench_context(NumericalFamily.INITIAL_VALUE),
        variable=VARIABLE,
        variable_unit="s",
        components=tuple(
            OdeComponent(
                function=function,
                unit="1",
                derivative=read_expression_text(derivative, symbols),
                initial_value=initial_values[function],
            )
            for function, derivative in derivatives.items()
        ),
        values=_symbol_values(parameters),
        start=0.0,
        end=end,
        samples=samples,
        relative_tolerance=relative_tolerance,
        absolute_tolerance=absolute_tolerance,
    )


def finite_basis_problem(
    state: ComplexVector,
    observable: ComplexMatrix,
    *,
    normalize: bool = False,
    basis: ComplexMatrix | None = None,
    tolerance: float = 1e-12,
) -> FiniteBasisProblem:
    return FiniteBasisProblem(
        context=bench_context(NumericalFamily.FINITE_BASIS),
        state=state,
        normalize=normalize,
        observable=observable,
        unit="1",
        basis=basis,
        tolerance=tolerance,
    )


def well_scales(width: float = NANOMETER) -> PhysicalScales:
    energy = REDUCED_PLANCK**2 / (ELECTRON_MASS * width**2)
    return PhysicalScales(length=width, energy=energy, time=REDUCED_PLANCK / energy)


def oscillator_scales(level_spacing: float = float(ELECTRON_VOLT_IN_JOULES)) -> PhysicalScales:
    return PhysicalScales(
        length=REDUCED_PLANCK / math.sqrt(ELECTRON_MASS * level_spacing),
        energy=level_spacing,
        time=REDUCED_PLANCK / level_spacing,
    )


def well_spectrum_problem(
    subintervals: int = 512, levels: int = 3, energy_unit: Unit = ELECTRON_VOLT
) -> SpectrumProblem:
    return SpectrumProblem(
        context=bench_context(NumericalFamily.WELL_SPECTRUM),
        scales=well_scales(),
        grid=ScaledGrid(left=0.0, right=1.0, subintervals=subintervals),
        potential=PotentialModel.ZERO,
        levels=levels,
        energy_unit=energy_unit,
        is_truncated_domain=False,
    )


def oscillator_spectrum_problem(
    half_width: float = 8.0, subintervals: int = 1024, levels: int = 3
) -> SpectrumProblem:
    return SpectrumProblem(
        context=bench_context(NumericalFamily.OSCILLATOR_SPECTRUM),
        scales=oscillator_scales(),
        grid=ScaledGrid(left=-half_width, right=half_width, subintervals=subintervals),
        potential=PotentialModel.HARMONIC,
        levels=levels,
        energy_unit=ELECTRON_VOLT,
        is_truncated_domain=True,
    )


def discrete_well_energy(level: int, subintervals: int) -> float:
    return (1.0 - math.cos(level * math.pi / subintervals)) * subintervals**2


def discrete_beat_period(subintervals: int, lower: int = 1, upper: int = 2) -> float:
    beat = discrete_well_energy(upper, subintervals) - discrete_well_energy(lower, subintervals)
    return 2 * math.pi / beat


def well_evolution_problem(
    coefficients: ComplexVector = (1 + 0j, 1 + 0j),
    *,
    subintervals: int = 256,
    steps: int = 1024,
    samples: int = 9,
    beat_periods: float = 1.0,
    normalize: bool = True,
) -> EvolutionProblem:
    return EvolutionProblem(
        context=bench_context(NumericalFamily.WELL_EVOLUTION),
        scales=well_scales(),
        grid=ScaledGrid(left=0.0, right=1.0, subintervals=subintervals),
        potential=PotentialModel.ZERO,
        coefficients=coefficients,
        normalize=normalize,
        scaled_duration=beat_periods * discrete_beat_period(subintervals),
        steps=steps,
        samples=samples,
    )


def statuses(report: VerificationReport) -> dict[str, VerificationStatus]:
    return {check.identifier: check.status for check in report.checks}


def column(report: NumericalSolverReport, table: str, name: str) -> tuple[float, ...]:
    return report.table(table).column(name).values


def _symbols(
    variables: tuple[str, ...], parameters: Mapping[str, float], functions: tuple[str, ...] = ()
) -> SymbolTable:
    return symbol_table(
        *(declared(name) for name in variables),
        *(declared(name, SymbolRole.PARAMETER) for name in parameters),
        *(declared(name, SymbolRole.FUNCTION, VARIABLE) for name in functions),
    )


def _symbol_values(parameters: Mapping[str, float]) -> tuple[SymbolValue, ...]:
    return tuple(SymbolValue(name, value) for name, value in parameters.items())
