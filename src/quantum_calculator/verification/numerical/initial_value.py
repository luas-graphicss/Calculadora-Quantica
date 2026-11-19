import numpy
from scipy import integrate

from quantum_calculator.domain.numerical.layout import TRAJECTORY
from quantum_calculator.domain.numerical.problems import InitialValueProblem, NumericalProblem
from quantum_calculator.domain.numerical.report import NumericalSolverReport
from quantum_calculator.domain.verification import (
    EvidenceKind,
    SkippedCheck,
    VerificationCheck,
    VerificationReport,
)
from quantum_calculator.numerics.evaluation import NonFiniteValueError, Samples
from quantum_calculator.numerics.ode_system import RightHandSide, initial_state, sample_instants
from quantum_calculator.verification.numerical.checks import bounded_check, inconclusive_check

_METHOD = "DOP853"
_COMPLETED = 0
_TIGHTENING = 1e-2
_TIGHTEST_RELATIVE_TOLERANCE = 1e-13
_GLOBAL_ERROR_ALLOWANCE = 100.0
_INITIAL_CHECK = "initial_condition"
_INITIAL_STATEMENT = "A trajetória começa no valor inicial declarado."
_REFINEMENT_CHECK = "tolerance_refinement"
_REFINEMENT_STATEMENT = (
    "Reintegrar com tolerâncias cem vezes mais apertadas muda a trajetória menos que "
    f"{_GLOBAL_ERROR_ALLOWANCE:g} vezes a tolerância pedida, em cada instante e componente."
)
_NOT_PERFORMED = (
    SkippedCheck(
        "closed_form_solution",
        "Nenhuma solução fechada foi usada: a comparação é por refinamento das tolerâncias. "
        "Para a EDO linear de coeficientes constantes, a ficha "
        "ode.first_order_linear.initial_value dá a solução exata.",
    ),
    SkippedCheck(
        "stiffness_detection",
        "A rigidez não é diagnosticada nem tratada: um problema rígido esgota o orçamento ou "
        "o passo, e nenhuma resposta é aprovada.",
    ),
)
_REFERENCES = (
    "E. Hairer, S. P. Nørsett e G. Wanner, Solving Ordinary Differential Equations I: "
    "Nonstiff Problems, 2ª ed., Springer, 1993, seção II.5.",
)


class InitialValueVerifier:
    def verify(
        self, problem: NumericalProblem, report: NumericalSolverReport
    ) -> VerificationReport:
        initial_value = _initial_value(problem)
        table = report.table(TRAJECTORY)
        reported = numpy.array(
            [table.column(component.function).values for component in initial_value.components]
        )
        return VerificationReport(
            checks=(
                _initial_check(initial_value, reported),
                _refinement_check(initial_value, reported),
            ),
            not_performed=_NOT_PERFORMED,
            references=_REFERENCES,
        )


def _initial_check(problem: InitialValueProblem, reported: Samples) -> VerificationCheck:
    deviation = float(numpy.max(numpy.abs(reported[:, 0] - initial_state(problem))))
    return bounded_check(
        _INITIAL_CHECK,
        EvidenceKind.CONSISTENCY_TEST,
        _INITIAL_STATEMENT,
        deviation,
        problem.absolute_tolerance,
        "desvio no primeiro instante",
    )


def _refinement_check(problem: InitialValueProblem, reported: Samples) -> VerificationCheck:
    try:
        reference = integrate.solve_ivp(
            RightHandSide(problem),
            (problem.start, problem.end),
            initial_state(problem),
            method=_METHOD,
            t_eval=sample_instants(problem),
            rtol=max(problem.relative_tolerance * _TIGHTENING, _TIGHTEST_RELATIVE_TOLERANCE),
            atol=problem.absolute_tolerance * _TIGHTENING,
        )
    except NonFiniteValueError:
        return _unfinished_reference("o lado direito deixou de ser finito")
    if int(reference.status) != _COMPLETED:
        return _unfinished_reference(str(reference.message))
    refined = numpy.asarray(reference.y, dtype=numpy.float64)
    allowed = problem.absolute_tolerance + problem.relative_tolerance * numpy.abs(refined)
    worst = float(numpy.max(numpy.abs(reported - refined) / allowed))
    return bounded_check(
        _REFINEMENT_CHECK,
        EvidenceKind.NUMERICAL_EVIDENCE,
        _REFINEMENT_STATEMENT,
        worst,
        _GLOBAL_ERROR_ALLOWANCE,
        "maior mudança, em unidades da tolerância pedida:",
    )


def _unfinished_reference(reason: str) -> VerificationCheck:
    return inconclusive_check(
        _REFINEMENT_CHECK,
        EvidenceKind.NUMERICAL_EVIDENCE,
        _REFINEMENT_STATEMENT,
        f"a integração de referência não terminou: {reason}",
    )


def _initial_value(problem: NumericalProblem) -> InitialValueProblem:
    if not isinstance(problem, InitialValueProblem):
        raise TypeError("the initial value verifier needs an initial value problem")
    return problem
