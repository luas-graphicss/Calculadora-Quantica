from collections.abc import Mapping
from functools import partial

from quantum_calculator.application.numerical.estimates import quadrature_estimate
from quantum_calculator.application.numerical.expressions import (
    BoundExpressions,
    ExpressionBinder,
    describe_interval,
)
from quantum_calculator.application.numerical.limits import (
    LOOSEST_ABSOLUTE_TOLERANCE,
    LOOSEST_RELATIVE_TOLERANCE,
    MAX_SUBDIVISIONS,
    NO_TOLERANCE,
    TIGHTEST_RELATIVE_TOLERANCE,
)
from quantum_calculator.application.numerical.request import ValidationRequest, pointer_to
from quantum_calculator.application.numerical.toolkit import ValidationToolkit
from quantum_calculator.application.statements.field_reader import ReadField
from quantum_calculator.application.statements.shape_rules import check_operator
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.dimensions import Dimension
from quantum_calculator.domain.expression_dimensions import DimensionAnalyzer
from quantum_calculator.domain.expression_traversal import node_count
from quantum_calculator.domain.expressions import Integral, IntegrationBounds
from quantum_calculator.domain.numerical.problems import (
    InterpretedInput,
    NumericalProblem,
    QuadratureProblem,
)
from quantum_calculator.domain.numerical.scalar_evaluation import (
    UndefinedValueError,
    evaluate_scalar,
)
from quantum_calculator.domain.statements import BoundSymbol

_STATEMENT = "statement"
_DEFINITE_FORM = "uma integral definida de uma variável, como integral(sin(x), x, 0, pi)"
_FINITE_BOUNDS = "limites finitos, calculáveis com os valores dos parâmetros"


class QuadratureValidator:
    def __init__(self, toolkit: ValidationToolkit, binder: ExpressionBinder) -> None:
        self._toolkit = toolkit
        self._binder = binder

    def validate(self, request: ValidationRequest) -> NumericalProblem | None:
        toolkit = self._toolkit
        settings = toolkit.settings(request)
        absolute = settings.within(
            "absolute_tolerance",
            "tolerância absoluta, na unidade coerente do SI do resultado",
            NO_TOLERANCE,
            LOOSEST_ABSOLUTE_TOLERANCE,
        )
        relative = settings.within(
            "relative_tolerance",
            "tolerância relativa",
            TIGHTEST_RELATIVE_TOLERANCE,
            LOOSEST_RELATIVE_TOLERANCE,
        )
        limit = settings.count(
            "subdivision_limit", "limite de subdivisões do intervalo", 1, MAX_SUBDIVISIONS
        )
        settings.reject_unknown()
        toolkit.refuse_display_unit(request)
        rounding = toolkit.rounding(request)
        bound = self._binder.bind(request)
        text = request.spec.statement
        if bound is None or text is None:
            return None
        field = bound.reader.read(pointer_to(_STATEMENT), text)
        if field is None:
            return None
        integral = _definite_integral(bound, field)
        dimension = _dimension(bound, field)
        if integral is None or integral.bounds is None or dimension is None:
            return None
        interval = _interval(bound, field, integral, integral.bounds)
        if interval is None or absolute is None or relative is None:
            return None
        if limit is None or rounding is None:
            return None
        lower, upper = interval
        unit = toolkit.units.coherent_symbol(dimension)
        variable_unit = toolkit.units.coherent_symbol(bound.symbols[integral.variable].dimension)
        return QuadratureProblem(
            context=toolkit.context(
                request,
                settings,
                inputs=(
                    bound.describe(_STATEMENT, "integral lida", field),
                    InterpretedInput(
                        "interval",
                        "intervalo de integração em unidades coerentes do SI",
                        describe_interval(lower, upper, variable_unit),
                        "limites calculados com os valores dos parâmetros",
                    ),
                    *bound.inputs,
                ),
                rounding=rounding,
                estimate=quadrature_estimate(limit, node_count(integral.body)),
            ),
            integrand=integral.body,
            variable=integral.variable,
            lower=lower,
            upper=upper,
            values=bound.values,
            result_unit=unit,
            absolute_tolerance=float(absolute),
            relative_tolerance=float(relative),
            subdivision_limit=limit,
        )


def _definite_integral(bound: BoundExpressions, field: ReadField) -> Integral | None:
    statement = field.statement
    if not isinstance(statement, Integral) or statement.bounds is None:
        bound.reader.report(
            field,
            DiagnosticCode.CARD_MISMATCH,
            "O enunciado não é uma integral definida.",
            _DEFINITE_FORM,
        )
        return None
    return bound.reader.check(field, partial(_checked, statement, bound.symbols))


def _checked(integral: Integral, symbols: Mapping[str, BoundSymbol]) -> Integral:
    check_operator(integral, symbols)
    return integral


def _dimension(bound: BoundExpressions, field: ReadField) -> Dimension | None:
    return bound.reader.check(
        field, partial(DimensionAnalyzer(bound.symbols).check, field.statement)
    )


def _interval(
    bound: BoundExpressions, field: ReadField, integral: Integral, bounds: IntegrationBounds
) -> tuple[float, float] | None:
    explicit = [
        bound.require_values(field, expression, integral.variable)
        for expression in (integral.body, bounds.lower, bounds.upper)
    ]
    if not all(explicit):
        return None
    values = bound.value_by_name
    try:
        return evaluate_scalar(bounds.lower, values), evaluate_scalar(bounds.upper, values)
    except UndefinedValueError:
        bound.reader.report(
            field,
            DiagnosticCode.UNDEFINED_EXPRESSION,
            "Um limite de integração não tem valor finito com os parâmetros dados.",
            _FINITE_BOUNDS,
        )
        return None
