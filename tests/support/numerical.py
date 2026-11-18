import hashlib
from collections.abc import Mapping

from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.numerical.cards import NumericalCard, NumericalFamily
from quantum_calculator.domain.numerical.problems import (
    InitialValueProblem,
    NumericalContext,
    OdeComponent,
    QuadratureProblem,
    ResourceEstimate,
    SymbolValue,
)
from quantum_calculator.domain.numerical.report import NumericalSolverReport
from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.domain.problem_spec import SourceDocument
from quantum_calculator.domain.rounding import RoundingPolicy
from quantum_calculator.domain.statements import SymbolRole
from quantum_calculator.domain.verification import VerificationReport, VerificationStatus
from support.notation import SymbolTable, declared, read_expression_text, symbol_table

VARIABLE = "t"

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
