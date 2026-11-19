from quantum_calculator.application.numerical.estimates import initial_value_estimate
from quantum_calculator.application.numerical.expressions import (
    ExpressionBinder,
    describe_interval,
)
from quantum_calculator.application.numerical.limits import (
    LOOSEST_ABSOLUTE_TOLERANCE,
    LOOSEST_RELATIVE_TOLERANCE,
    MAX_SAMPLES,
    NO_TOLERANCE,
    TIGHTEST_RELATIVE_TOLERANCE,
)
from quantum_calculator.application.numerical.ode_system import OdeSystemReader
from quantum_calculator.application.numerical.request import ValidationRequest
from quantum_calculator.application.numerical.toolkit import ValidationToolkit
from quantum_calculator.application.statements.unit_expressions import measure_of_unit
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.numerical.problems import (
    InitialValueProblem,
    InterpretedInput,
    NumericalProblem,
)

_END = "end"


class InitialValueValidator:
    def __init__(self, toolkit: ValidationToolkit, binder: ExpressionBinder) -> None:
        self._toolkit = toolkit
        self._binder = binder

    def validate(self, request: ValidationRequest) -> NumericalProblem | None:
        toolkit = self._toolkit
        settings = toolkit.settings(request)
        end = settings.real(_END, "valor final da variável independente, na unidade declarada")
        samples = settings.count("samples", "instantes uniformes da trajetória", 2, MAX_SAMPLES)
        relative = settings.within(
            "relative_tolerance",
            "tolerância relativa por passo",
            TIGHTEST_RELATIVE_TOLERANCE,
            LOOSEST_RELATIVE_TOLERANCE,
        )
        absolute = settings.within(
            "absolute_tolerance",
            "tolerância absoluta por passo, na unidade coerente do SI de cada componente",
            NO_TOLERANCE,
            LOOSEST_ABSOLUTE_TOLERANCE,
        )
        settings.reject_unknown()
        toolkit.refuse_display_unit(request)
        rounding = toolkit.rounding(request)
        bound = self._binder.bind(request)
        if bound is None:
            return None
        system = OdeSystemReader(request, bound, toolkit.units).read()
        if system is None or end is None or samples is None:
            return None
        if relative is None or absolute is None or rounding is None:
            return None
        variable = bound.symbols[system.variable]
        final = float(end * measure_of_unit(variable.unit, toolkit.units).si_factor)
        if final <= system.start:
            settings.refuse(
                _END,
                DiagnosticCode.NUMBER_OUT_OF_RANGE,
                "O valor final precisa vir depois do instante das condições iniciais: a "
                "integração para trás não é coberta.",
                "valor final maior que o instante das condições iniciais",
            )
            return None
        unit = toolkit.units.coherent_symbol(variable.dimension)
        return InitialValueProblem(
            context=toolkit.context(
                request,
                settings,
                inputs=(
                    *system.inputs,
                    InterpretedInput(
                        "interval",
                        "intervalo da variável independente em unidades coerentes do SI",
                        describe_interval(system.start, final, unit),
                        "instante das condições iniciais e valor final pedido",
                    ),
                    *bound.inputs,
                ),
                rounding=rounding,
                estimate=initial_value_estimate(
                    samples, len(system.components), system.derivative_nodes
                ),
            ),
            variable=variable.name,
            variable_unit=unit,
            components=system.components,
            values=bound.values,
            start=system.start,
            end=final,
            samples=samples,
            relative_tolerance=float(relative),
            absolute_tolerance=float(absolute),
        )
