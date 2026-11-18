import numpy
from scipy import integrate

from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.numerical.layout import TRAJECTORY, final_value
from quantum_calculator.domain.numerical.problems import InitialValueProblem, NumericalProblem
from quantum_calculator.domain.numerical.report import (
    EffectiveParameter,
    NumericalAnswer,
    NumericalSolverReport,
    SampleColumn,
    SampleTable,
)
from quantum_calculator.numerics.evaluation import NonFiniteValueError, Samples
from quantum_calculator.numerics.failures import method_not_converged, non_finite_result
from quantum_calculator.numerics.ode_system import RightHandSide, initial_state, sample_instants

METHOD = "DOP853"

_COMPLETED = 0
_DERIVATIVE = "O lado direito da equação"
_TRAJECTORY = "A trajetória"


class ExplicitRungeKuttaSolver:
    def solve(self, problem: NumericalProblem) -> NumericalSolverReport:
        initial_value = _initial_value(problem)
        instants = sample_instants(initial_value)
        try:
            solution = integrate.solve_ivp(
                RightHandSide(initial_value),
                (initial_value.start, initial_value.end),
                initial_state(initial_value),
                method=METHOD,
                t_eval=instants,
                rtol=initial_value.relative_tolerance,
                atol=initial_value.absolute_tolerance,
            )
        except NonFiniteValueError as error:
            raise non_finite_result(_DERIVATIVE) from error
        if int(solution.status) != _COMPLETED:
            raise method_not_converged(METHOD, str(solution.message))
        trajectory = numpy.asarray(solution.y, dtype=numpy.float64)
        if not numpy.all(numpy.isfinite(trajectory)):
            raise non_finite_result(_TRAJECTORY)
        return NumericalSolverReport(
            nature=ResultNature.APPROXIMATE,
            answers=_final_values(initial_value, trajectory),
            tables=(_trajectory_table(initial_value, instants, trajectory),),
            effective=_effective(initial_value, int(solution.nfev), str(solution.message)),
            warnings=(),
        )


def _final_values(problem: InitialValueProblem, trajectory: Samples) -> tuple[NumericalAnswer, ...]:
    return tuple(
        NumericalAnswer(
            name=final_value(component.function),
            symbol=f"{component.function}({problem.variable} final)",
            label=f"valor de {component.function} no fim do intervalo",
            value=float(trajectory[index, -1]),
            unit=component.unit,
            estimate=None,
        )
        for index, component in enumerate(problem.components)
    )


def _trajectory_table(
    problem: InitialValueProblem, instants: Samples, trajectory: Samples
) -> SampleTable:
    variable = problem.variable
    columns = [SampleColumn(variable, variable, problem.variable_unit, _as_tuple(instants))]
    columns += [
        SampleColumn(
            component.function,
            f"{component.function}({variable})",
            component.unit,
            _as_tuple(trajectory[index]),
        )
        for index, component in enumerate(problem.components)
    ]
    return SampleTable(TRAJECTORY, "Trajetória nos instantes pedidos", tuple(columns))


def _effective(
    problem: InitialValueProblem, evaluations: int, termination: str
) -> tuple[EffectiveParameter, ...]:
    return (
        EffectiveParameter(
            "relative_tolerance", "tolerância relativa", repr(problem.relative_tolerance)
        ),
        EffectiveParameter(
            "absolute_tolerance", "tolerância absoluta", repr(problem.absolute_tolerance)
        ),
        EffectiveParameter("evaluations", "avaliações do lado direito", str(evaluations)),
        EffectiveParameter("termination", "motivo de término", termination),
    )


def _as_tuple(values: Samples) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _initial_value(problem: NumericalProblem) -> InitialValueProblem:
    if not isinstance(problem, InitialValueProblem):
        raise TypeError("the explicit Runge-Kutta solver needs an initial value problem")
    return problem
