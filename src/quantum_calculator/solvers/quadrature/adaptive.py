import math

from scipy import integrate

from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.numerical.layout import INTEGRAL
from quantum_calculator.domain.numerical.problems import NumericalProblem, QuadratureProblem
from quantum_calculator.domain.numerical.report import (
    EffectiveParameter,
    ErrorEstimate,
    NumericalAnswer,
    NumericalSolverReport,
)
from quantum_calculator.numerics.evaluation import NonFiniteValueError
from quantum_calculator.numerics.failures import method_not_converged, non_finite_result
from quantum_calculator.numerics.integrand import Integrand

_METHOD = "QUADPACK QAGS"
_CONVERGED_LENGTH = 3
_INTEGRAND = "O integrando"
_VALUE = "O valor da integral"


class AdaptiveQuadratureSolver:
    def solve(self, problem: NumericalProblem) -> NumericalSolverReport:
        quadrature = _quadrature(problem)
        try:
            outcome = integrate.quad(
                Integrand(quadrature),
                quadrature.lower,
                quadrature.upper,
                epsabs=quadrature.absolute_tolerance,
                epsrel=quadrature.relative_tolerance,
                limit=quadrature.subdivision_limit,
                full_output=1,
            )
        except NonFiniteValueError as error:
            raise non_finite_result(_INTEGRAND) from error
        if len(outcome) > _CONVERGED_LENGTH:
            raise method_not_converged(_METHOD, " ".join(str(outcome[3]).split()))
        value, estimate = float(outcome[0]), float(outcome[1])
        if not (math.isfinite(value) and math.isfinite(estimate)):
            raise non_finite_result(_VALUE)
        return NumericalSolverReport(
            nature=ResultNature.APPROXIMATE,
            answers=(
                NumericalAnswer(
                    name=INTEGRAL,
                    symbol="I",
                    label="valor da integral",
                    value=value,
                    unit=quadrature.result_unit,
                    estimate=ErrorEstimate(
                        estimate, "estimativa de erro absoluto do integrador adaptativo"
                    ),
                ),
            ),
            tables=(),
            effective=_effective(quadrature, int(outcome[2]["neval"]), int(outcome[2]["last"])),
            warnings=(),
        )


def _effective(
    problem: QuadratureProblem, evaluations: int, subintervals: int
) -> tuple[EffectiveParameter, ...]:
    return (
        EffectiveParameter(
            "absolute_tolerance", "tolerância absoluta", repr(problem.absolute_tolerance)
        ),
        EffectiveParameter(
            "relative_tolerance", "tolerância relativa", repr(problem.relative_tolerance)
        ),
        EffectiveParameter(
            "subdivision_limit", "limite de subdivisões", str(problem.subdivision_limit)
        ),
        EffectiveParameter("evaluations", "avaliações do integrando", str(evaluations)),
        EffectiveParameter("subintervals", "subintervalos usados", str(subintervals)),
        EffectiveParameter(
            "termination", "motivo de término", "tolerância pedida atingida (ier = 0)"
        ),
    )


def _quadrature(problem: NumericalProblem) -> QuadratureProblem:
    if not isinstance(problem, QuadratureProblem):
        raise TypeError("adaptive quadrature needs a quadrature problem")
    return problem
