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
_REASONS = (
    (
        "The maximum number of subdivisions",
        "o limite de subdivisões foi atingido sem alcançar a tolerância",
    ),
    (
        "The occurrence of roundoff error",
        "o erro de arredondamento impede alcançar a tolerância pedida",
    ),
    (
        "Extremely bad integrand behavior",
        "o integrando se comporta mal em algum ponto do intervalo",
    ),
    (
        "The algorithm does not converge",
        "a extrapolação não converge e o erro de arredondamento domina",
    ),
    (
        "The integral is probably divergent",
        "a integral provavelmente diverge ou converge devagar demais",
    ),
)


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
            raise method_not_converged(_METHOD, _reason(str(outcome[3])))
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


def _reason(library_message: str) -> str:
    sentence, _, _ = " ".join(library_message.split()).partition(". ")
    for opening, reason in _REASONS:
        if sentence.startswith(opening):
            return f"{reason}."
    return f"a biblioteca relata: {sentence.rstrip('.')}."


def _quadrature(problem: NumericalProblem) -> QuadratureProblem:
    if not isinstance(problem, QuadratureProblem):
        raise TypeError("adaptive quadrature needs a quadrature problem")
    return problem
