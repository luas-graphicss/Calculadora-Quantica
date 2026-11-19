import math

import numpy
from scipy import linalg

from quantum_calculator.domain.numerical.layout import (
    DENSITY,
    FINAL_DENSITY,
    NORM,
    OBSERVABLES,
    PHASE_ERROR,
    RELATIVE_PHASE,
    STEPS,
    TIME,
    TIME_REFINEMENT,
)
from quantum_calculator.domain.numerical.problems import EvolutionProblem, NumericalProblem
from quantum_calculator.domain.numerical.report import NumericalSolverReport, SampleTable
from quantum_calculator.domain.verification import (
    EvidenceKind,
    SkippedCheck,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)
from quantum_calculator.numerics.evaluation import Samples
from quantum_calculator.numerics.grid import spacing
from quantum_calculator.numerics.hamiltonian import discrete_hamiltonian
from quantum_calculator.numerics.superposition import (
    beating_pair,
    mode_coefficients,
    relative_phase,
    wrapped,
)
from quantum_calculator.verification.numerical.checks import bounded_check, scientific

NORM_DRIFT_LIMIT = 1e-9
PHASE_ERROR_LIMIT = 1e-3
OBSERVED_ORDER_RANGE = (1.8, 2.2)

_SCHEME_LIMIT = 1e-8
_ROUNDING_FLOOR = 1e-11
_NORM_STATEMENT = (
    "A norma do estado fica constante nos instantes salvos, sem renormalização entre passos."
)
_DENSITY_STATEMENT = (
    "A integral da densidade final sobre a malha é o quadrado da norma relatada no último instante."
)
_PHASE_STATEMENT = (
    "A fase relativa entre os dois modos populados mais baixos acompanha a evolução exata "
    "dos modos discretos, o que isola o erro temporal do erro da malha."
)
_SCHEME_STATEMENT = (
    "A fase relativa relatada é a que o esquema de Crank-Nicolson dá para cada modo "
    "discreto, 2 arctan(E dt / 2) por passo: o propagador aplicado é o declarado."
)
_ORDER_STATEMENT = (
    "Dobrando o número de passos duas vezes, o erro de fase no instante final cai com ordem "
    f"observada entre {OBSERVED_ORDER_RANGE[0]} e {OBSERVED_ORDER_RANGE[1]}, ou já está no "
    "piso de arredondamento."
)
_SPATIAL_ERROR_NOT_ASSESSED = SkippedCheck(
    "spatial_discretization",
    "O erro da malha não é avaliado aqui: a referência é a evolução exata dos modos "
    "discretos. A ficha quantum.infinite_square_well.discrete_spectrum estuda a malha.",
)
_NO_BEATING_PAIR = "Menos de dois modos estão populados: não há fase relativa a conferir."
_REFERENCES = (
    "J. Crank e P. Nicolson, A practical method for numerical evaluation of solutions of "
    "partial differential equations of the heat-conduction type, Proc. Cambridge Philos. "
    "Soc. 43, 50-67, 1947.",
    "A. Goldberg, H. M. Schey e J. L. Schwartz, Computer-generated motion pictures of "
    "one-dimensional quantum-mechanical transmission and reflection phenomena, Am. J. Phys. "
    "35, 177-186, 1967.",
)


class EvolutionVerifier:
    def verify(
        self, problem: NumericalProblem, report: NumericalSolverReport
    ) -> VerificationReport:
        evolution = _evolution(problem)
        observables = report.table(OBSERVABLES)
        norms = numpy.array(observables.column(NORM).values)
        checks = [_norm_check(norms), _density_check(evolution, report, float(norms[-1]))]
        pair = beating_pair(evolution)
        if pair is None:
            skipped = tuple(
                SkippedCheck(identifier, _NO_BEATING_PAIR)
                for identifier in ("relative_phase", "scheme_dispersion", "temporal_order")
            )
            return VerificationReport(
                tuple(checks), (*skipped, _SPATIAL_ERROR_NOT_ASSESSED), _REFERENCES
            )
        energies = _pair_energies(evolution, pair)
        initial_phase = relative_phase(mode_coefficients(evolution), pair)
        scaled_times = numpy.array(observables.column(TIME).values) / evolution.scales.time
        reported = numpy.array(observables.column(RELATIVE_PHASE).values)
        step = evolution.scaled_duration / evolution.steps
        checks += [
            _phase_check(reported, initial_phase - (energies[1] - energies[0]) * scaled_times),
            _scheme_check(reported, initial_phase - _scheme_advance(energies, step) * scaled_times),
            _order_check(evolution, energies, report.table(TIME_REFINEMENT)),
        ]
        return VerificationReport(tuple(checks), (_SPATIAL_ERROR_NOT_ASSESSED,), _REFERENCES)


def _pair_energies(problem: EvolutionProblem, pair: tuple[int, int]) -> tuple[float, float]:
    operator = discrete_hamiltonian(problem.grid, problem.potential)
    energies = linalg.eigvalsh_tridiagonal(
        operator.diagonal, operator.off_diagonal, select="i", select_range=(0, pair[1])
    )
    return float(energies[pair[0]]), float(energies[pair[1]])


def _scheme_advance(energies: tuple[float, float], step: float) -> float:
    lower, upper = energies
    return 2.0 * (math.atan(upper * step / 2) - math.atan(lower * step / 2)) / step


def _largest_wrapped(differences: Samples) -> float:
    return max(abs(wrapped(float(difference))) for difference in differences)


def _norm_check(norms: Samples) -> VerificationCheck:
    return bounded_check(
        "norm_conservation",
        EvidenceKind.NUMERICAL_EVIDENCE,
        _NORM_STATEMENT,
        float(numpy.max(numpy.abs(norms - norms[0]))),
        NORM_DRIFT_LIMIT,
        "deriva máxima da norma:",
    )


def _density_check(
    problem: EvolutionProblem, report: NumericalSolverReport, final_norm: float
) -> VerificationCheck:
    density = numpy.array(report.table(FINAL_DENSITY).column(DENSITY).values)
    integral = float(numpy.sum(density)) * spacing(problem.grid) * problem.scales.length
    return bounded_check(
        "final_density_integral",
        EvidenceKind.CONSISTENCY_TEST,
        _DENSITY_STATEMENT,
        abs(integral - final_norm**2),
        NORM_DRIFT_LIMIT,
        "diferença entre a integral e o quadrado da norma:",
    )


def _phase_check(reported: Samples, exact: Samples) -> VerificationCheck:
    return bounded_check(
        "relative_phase",
        EvidenceKind.NUMERICAL_EVIDENCE,
        _PHASE_STATEMENT,
        _largest_wrapped(reported - exact),
        PHASE_ERROR_LIMIT,
        "maior erro de fase, em rad:",
    )


def _scheme_check(reported: Samples, predicted: Samples) -> VerificationCheck:
    return bounded_check(
        "scheme_dispersion",
        EvidenceKind.NUMERICAL_EVIDENCE,
        _SCHEME_STATEMENT,
        _largest_wrapped(reported - predicted),
        _SCHEME_LIMIT,
        "maior diferença para a fase prevista pelo esquema, em rad:",
    )


def _order_check(
    problem: EvolutionProblem, energies: tuple[float, float], table: SampleTable
) -> VerificationCheck:
    steps = numpy.array(table.column(STEPS).values)
    errors = numpy.array(table.column(PHASE_ERROR).values)
    expected_steps = [problem.steps // 4, problem.steps // 2, problem.steps]
    if steps.tolist() != [float(count) for count in expected_steps]:
        return _order_outcome(
            VerificationStatus.FAILED, "a tabela não traz os três números de passos do estudo"
        )
    beat = energies[1] - energies[0]
    predicted = [
        abs(
            wrapped(
                (beat - _scheme_advance(energies, problem.scaled_duration / count))
                * problem.scaled_duration
            )
        )
        for count in expected_steps
    ]
    if float(numpy.max(numpy.abs(errors - numpy.array(predicted)))) > _SCHEME_LIMIT:
        return _order_outcome(
            VerificationStatus.FAILED,
            "os erros da tabela não são os que o esquema de Crank-Nicolson produz",
        )
    if errors[-1] < _ROUNDING_FLOOR:
        return _order_outcome(
            VerificationStatus.PASSED,
            f"erro final {scientific(float(errors[-1]))} rad, já no piso de arredondamento",
        )
    order = float(numpy.log2(errors[-2] / errors[-1]))
    described = (
        f"ordem observada {order:.3f} entre {expected_steps[1]} e {expected_steps[2]} passos"
    )
    if not OBSERVED_ORDER_RANGE[0] <= order <= OBSERVED_ORDER_RANGE[1]:
        return _order_outcome(
            VerificationStatus.INCONCLUSIVE,
            f"{described}: o passo não está no regime assintótico de segunda ordem",
        )
    return _order_outcome(VerificationStatus.PASSED, described)


def _order_outcome(status: VerificationStatus, observed: str) -> VerificationCheck:
    return VerificationCheck(
        "temporal_order", EvidenceKind.NUMERICAL_EVIDENCE, status, _ORDER_STATEMENT, observed
    )


def _evolution(problem: NumericalProblem) -> EvolutionProblem:
    if not isinstance(problem, EvolutionProblem):
        raise TypeError("the evolution verifier needs an evolution problem")
    return problem
