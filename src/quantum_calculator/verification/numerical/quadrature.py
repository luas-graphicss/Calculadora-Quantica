import numpy

from quantum_calculator.domain.numerical.layout import INTEGRAL
from quantum_calculator.domain.numerical.problems import NumericalProblem, QuadratureProblem
from quantum_calculator.domain.numerical.report import NumericalAnswer, NumericalSolverReport
from quantum_calculator.domain.numerical.tolerance import Tolerance
from quantum_calculator.domain.verification import (
    EvidenceKind,
    SkippedCheck,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)
from quantum_calculator.numerics.evaluation import NonFiniteValueError
from quantum_calculator.numerics.integrand import Integrand
from quantum_calculator.verification.numerical.checks import (
    bounded_check,
    inconclusive_check,
    scientific,
)

_ESTIMATE_CHECK = "integrator_error_estimate"
_ESTIMATE_STATEMENT = (
    "A estimativa de erro do integrador fica dentro da tolerância pedida, absoluta mais "
    "relativa ao valor."
)
_INDEPENDENT_CHECK = "independent_quadrature"
_INDEPENDENT_STATEMENT = (
    "Uma regra composta de Gauss-Legendre, independente do integrador adaptativo, dá o mesmo "
    "valor dentro da tolerância pedida."
)
_RULE_ORDER = 20
_COARSE_PANELS = 64
_FINE_PANELS = 128
_NOT_PERFORMED = (
    SkippedCheck(
        "closed_form_primitive",
        "Esta ficha só aproxima: nenhuma primitiva foi procurada. A ficha "
        "calculus.definite_integral dá o valor exato quando há primitiva coberta.",
    ),
)
_REFERENCES = (
    "R. Piessens, E. de Doncker-Kapenga, C. W. Überhuber e D. K. Kahaner, QUADPACK: A "
    "Subroutine Package for Automatic Integration, Springer, 1983.",
)


class QuadratureVerifier:
    def verify(
        self, problem: NumericalProblem, report: NumericalSolverReport
    ) -> VerificationReport:
        quadrature = _quadrature(problem)
        answer = report.answer(INTEGRAL)
        tolerance = Tolerance(quadrature.absolute_tolerance, quadrature.relative_tolerance)
        return VerificationReport(
            checks=(
                _estimate_check(answer, tolerance),
                _independent_check(quadrature, answer, tolerance),
            ),
            not_performed=_NOT_PERFORMED,
            references=_REFERENCES,
        )


def _estimate_check(answer: NumericalAnswer, tolerance: Tolerance) -> VerificationCheck:
    if answer.estimate is None:
        return VerificationCheck(
            _ESTIMATE_CHECK,
            EvidenceKind.CONSISTENCY_TEST,
            VerificationStatus.FAILED,
            _ESTIMATE_STATEMENT,
            "o resultado veio sem a estimativa de erro do integrador",
        )
    return bounded_check(
        _ESTIMATE_CHECK,
        EvidenceKind.CONSISTENCY_TEST,
        _ESTIMATE_STATEMENT,
        answer.estimate.value,
        tolerance.bound(answer.value),
        "estimativa do integrador",
    )


def _independent_check(
    problem: QuadratureProblem, answer: NumericalAnswer, tolerance: Tolerance
) -> VerificationCheck:
    integrand = Integrand(problem)
    try:
        coarse = _composite_gauss_legendre(integrand, problem, _COARSE_PANELS)
        fine = _composite_gauss_legendre(integrand, problem, _FINE_PANELS)
    except NonFiniteValueError:
        return inconclusive_check(
            _INDEPENDENT_CHECK,
            EvidenceKind.NUMERICAL_EVIDENCE,
            _INDEPENDENT_STATEMENT,
            "o integrando não é finito em um nó da regra de referência",
        )
    bound = tolerance.bound(fine)
    reference_error = abs(fine - coarse)
    if reference_error > bound:
        return inconclusive_check(
            _INDEPENDENT_CHECK,
            EvidenceKind.NUMERICAL_EVIDENCE,
            _INDEPENDENT_STATEMENT,
            f"a regra de referência muda {scientific(reference_error)} entre {_COARSE_PANELS} e "
            f"{_FINE_PANELS} painéis, mais que a tolerância {scientific(bound)}: ela não serve "
            "de referência para este integrando",
        )
    return bounded_check(
        _INDEPENDENT_CHECK,
        EvidenceKind.NUMERICAL_EVIDENCE,
        _INDEPENDENT_STATEMENT,
        abs(answer.value - fine),
        bound + reference_error,
        f"diferença para a regra de {_FINE_PANELS} painéis e ordem {_RULE_ORDER}:",
    )


def _composite_gauss_legendre(
    integrand: Integrand, problem: QuadratureProblem, panels: int
) -> float:
    nodes, weights = numpy.polynomial.legendre.leggauss(_RULE_ORDER)
    edges = numpy.linspace(problem.lower, problem.upper, panels + 1)
    half_widths = (edges[1:] - edges[:-1]) / 2
    centers = (edges[1:] + edges[:-1]) / 2
    positions = centers[:, numpy.newaxis] + half_widths[:, numpy.newaxis] * nodes
    values = integrand.sample(positions.ravel()).reshape(positions.shape)
    return float(numpy.sum(half_widths * (values @ weights)))


def _quadrature(problem: NumericalProblem) -> QuadratureProblem:
    if not isinstance(problem, QuadratureProblem):
        raise TypeError("the quadrature verifier needs a quadrature problem")
    return problem
