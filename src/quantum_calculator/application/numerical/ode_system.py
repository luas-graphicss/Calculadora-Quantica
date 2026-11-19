from dataclasses import dataclass
from functools import partial

from quantum_calculator.application.numerical.expressions import BoundExpressions
from quantum_calculator.application.numerical.ode_forms import (
    CONDITION_FORM,
    EXPLICIT_FORM,
    ExplicitEquation,
    InitialCondition,
    explicit_equation,
    initial_condition,
)
from quantum_calculator.application.numerical.request import ValidationRequest, pointer_to
from quantum_calculator.application.statements.field_reader import ReadField
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.expression_dimensions import DimensionAnalyzer
from quantum_calculator.domain.expression_traversal import node_count, unknown_functions
from quantum_calculator.domain.numerical.problems import InterpretedInput, OdeComponent
from quantum_calculator.domain.numerical.scalar_evaluation import (
    UndefinedValueError,
    evaluate_scalar,
)
from quantum_calculator.domain.ports import UnitRegistry

_EQUATIONS = "equations"
_CONDITIONS = "conditions"


@dataclass(frozen=True, slots=True)
class OdeSystem:
    variable: str
    start: float
    components: tuple[OdeComponent, ...]
    inputs: tuple[InterpretedInput, ...]
    derivative_nodes: int


@dataclass(frozen=True, slots=True)
class _InitialPoint:
    instant: float
    value: float


class OdeSystemReader:
    def __init__(
        self, request: ValidationRequest, bound: BoundExpressions, units: UnitRegistry
    ) -> None:
        self._request = request
        self._bound = bound
        self._units = units
        self._dimensions = DimensionAnalyzer(bound.symbols)
        self._inputs: list[InterpretedInput] = []

    def read(self) -> OdeSystem | None:
        reported = len(self._request.diagnostics)
        equations = self._equations()
        if not equations or len(self._request.diagnostics) > reported:
            return None
        points = self._initial_points(equations)
        if len(self._request.diagnostics) > reported or len(points) < len(equations):
            return None
        first = next(iter(equations.values()))
        return OdeSystem(
            variable=first.function.require_argument(),
            start=next(iter(points.values())).instant,
            components=tuple(
                OdeComponent(
                    function=name,
                    unit=self._units.coherent_symbol(equation.function.dimension),
                    derivative=equation.derivative,
                    initial_value=points[name].value,
                )
                for name, equation in equations.items()
            ),
            inputs=tuple(self._inputs),
            derivative_nodes=sum(
                node_count(equation.derivative) for equation in equations.values()
            ),
        )

    def _equations(self) -> dict[str, ExplicitEquation]:
        reader = self._bound.reader
        found: dict[str, ExplicitEquation] = {}
        given = self._request.spec.equations
        for index, text in enumerate(given or ()):
            field = reader.read(pointer_to(_EQUATIONS, str(index)), text)
            if field is None:
                continue
            reader.check(field, partial(self._dimensions.check, field.statement))
            equation = reader.check(
                field, partial(explicit_equation, field.statement, self._bound.symbols)
            )
            if equation is None:
                continue
            name = equation.function.name
            if name in found:
                reader.report(
                    field,
                    DiagnosticCode.DUPLICATE_FIELD,
                    f"A função {name} tem mais de uma equação.",
                    EXPLICIT_FORM,
                )
                continue
            self._bound.require_values(
                field, equation.derivative, equation.function.require_argument()
            )
            self._inputs.append(self._bound.describe(f"equation_{name}", "equação lida", field))
            found[name] = equation
        if given is not None:
            self._check_closed_system(found, has_equations=bool(given))
        return found

    def _check_closed_system(
        self, equations: dict[str, ExplicitEquation], *, has_equations: bool
    ) -> None:
        pointer = pointer_to(_EQUATIONS)
        if not has_equations:
            self._request.refuse(
                DiagnosticCode.MISSING_FIELD,
                pointer,
                "O sistema não traz nenhuma equação.",
                EXPLICIT_FORM,
            )
        referenced = {
            reference.name
            for equation in equations.values()
            for reference in unknown_functions(equation.derivative)
        }
        for name in sorted(referenced - equations.keys()):
            self._request.refuse(
                DiagnosticCode.MISSING_FIELD,
                pointer,
                f"A função {name} aparece no sistema e não tem equação.",
                EXPLICIT_FORM,
            )
        variables = sorted(
            {equation.function.require_argument() for equation in equations.values()}
        )
        if len(variables) > 1:
            self._request.refuse(
                DiagnosticCode.OUTSIDE_COVERAGE,
                pointer,
                f"As funções do sistema dependem de variáveis diferentes: {', '.join(variables)}.",
                "todas as funções dependentes da mesma variável",
            )

    def _initial_points(self, equations: dict[str, ExplicitEquation]) -> dict[str, _InitialPoint]:
        reader = self._bound.reader
        functions = {name: equation.function for name, equation in equations.items()}
        points: dict[str, _InitialPoint] = {}
        given = self._request.spec.conditions
        for index, text in enumerate(given or ()):
            field = reader.read(pointer_to(_CONDITIONS, str(index)), text)
            if field is None:
                continue
            reader.check(field, partial(self._dimensions.check, field.statement))
            condition = reader.check(field, partial(initial_condition, field.statement, functions))
            if condition is None:
                continue
            name = condition.function.name
            if name in points:
                reader.report(
                    field,
                    DiagnosticCode.INCOMPATIBLE_CONDITION,
                    f"A função {name} já tem condição inicial: uma equação de primeira ordem "
                    "aceita uma só.",
                    CONDITION_FORM,
                )
                continue
            point = self._point(field, condition)
            if point is None:
                continue
            self._inputs.append(
                self._bound.describe(f"condition_{name}", "condição inicial lida", field)
            )
            points[name] = point
        if given is not None:
            self._check_single_start(functions.keys() - points.keys(), points)
        return points

    def _point(self, field: ReadField, condition: InitialCondition) -> _InitialPoint | None:
        valued = [
            self._bound.require_values(field, expression, None)
            for expression in (condition.instant, condition.value)
        ]
        if not all(valued):
            return None
        values = self._bound.value_by_name
        try:
            return _InitialPoint(
                evaluate_scalar(condition.instant, values), evaluate_scalar(condition.value, values)
            )
        except UndefinedValueError:
            self._bound.reader.report(
                field,
                DiagnosticCode.UNDEFINED_EXPRESSION,
                "A condição inicial não tem valor finito com os parâmetros dados.",
                CONDITION_FORM,
            )
            return None

    def _check_single_start(self, missing: set[str], points: dict[str, _InitialPoint]) -> None:
        pointer = pointer_to(_CONDITIONS)
        for name in sorted(missing):
            self._request.refuse(
                DiagnosticCode.MISSING_FIELD,
                pointer,
                f"Falta a condição inicial de {name}.",
                CONDITION_FORM,
            )
        instants = {point.instant for point in points.values()}
        if len(instants) > 1:
            placed = ", ".join(f"{name} em {point.instant!r}" for name, point in points.items())
            self._request.refuse(
                DiagnosticCode.INCOMPATIBLE_CONDITION,
                pointer,
                f"As condições iniciais estão em instantes diferentes ({placed}): o problema "
                "de valor inicial parte de um único instante.",
                CONDITION_FORM,
            )
