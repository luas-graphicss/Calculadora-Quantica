import numpy
from numpy.typing import NDArray

from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.numerical.layout import (
    DEGENERACY,
    EIGENVALUE,
    EXPECTATION_VALUE,
    IMAGINARY_PART,
    MEASUREMENT,
    PREPARED_STATE,
    PROBABILITY,
    REAL_PART,
    outcome_probability,
)
from quantum_calculator.domain.numerical.problems import FiniteBasisProblem, NumericalProblem
from quantum_calculator.domain.numerical.report import (
    EffectiveParameter,
    NumericalAnswer,
    NumericalSolverReport,
    SampleColumn,
    SampleTable,
)
from quantum_calculator.numerics.failures import non_finite_result
from quantum_calculator.numerics.finite_basis import (
    Amplitudes,
    observable_matrix,
    operator_scale,
    prepared_state,
)

_DIMENSIONLESS = "1"
_SPECTRUM = "O espectro do observável"


class ProjectiveMeasurementSolver:
    def solve(self, problem: NumericalProblem) -> NumericalSolverReport:
        measurement = _measurement(problem)
        state = prepared_state(measurement)
        observable = observable_matrix(measurement)
        if measurement.basis is not None:
            change = numpy.array(measurement.basis, dtype=numpy.complex128)
            state = change.conj() @ state
            observable = change.conj() @ observable @ change.T
        eigenvalues, eigenvectors = numpy.linalg.eigh(observable)
        if not numpy.all(numpy.isfinite(eigenvalues)):
            raise non_finite_result(_SPECTRUM)
        weights = numpy.abs(eigenvectors.conj().T @ state) ** 2
        separation = measurement.tolerance * operator_scale(observable)
        outcomes = _eigenspaces(eigenvalues, weights, separation)
        expectation = sum(value * probability for value, _, probability in outcomes)
        return NumericalSolverReport(
            nature=ResultNature.APPROXIMATE,
            answers=(
                *_probability_answers(outcomes, measurement.unit),
                NumericalAnswer(
                    name=EXPECTATION_VALUE,
                    symbol="<A>",
                    label="valor esperado do observável",
                    value=expectation,
                    unit=measurement.unit,
                    estimate=None,
                ),
            ),
            tables=(_measurement_table(outcomes, measurement.unit), _state_table(state)),
            effective=_effective(measurement, separation),
            warnings=(),
        )


def _eigenspaces(
    eigenvalues: NDArray[numpy.float64], weights: NDArray[numpy.float64], separation: float
) -> list[tuple[float, int, float]]:
    outcomes: list[tuple[float, int, float]] = []
    members: list[int] = []
    for index in range(len(eigenvalues)):
        if members and eigenvalues[index] - eigenvalues[members[-1]] > separation:
            outcomes.append(_eigenspace(eigenvalues, weights, members))
            members = []
        members.append(index)
    outcomes.append(_eigenspace(eigenvalues, weights, members))
    return outcomes


def _eigenspace(
    eigenvalues: NDArray[numpy.float64], weights: NDArray[numpy.float64], members: list[int]
) -> tuple[float, int, float]:
    return (
        float(numpy.mean(eigenvalues[members])),
        len(members),
        float(numpy.sum(weights[members])),
    )


def _probability_answers(
    outcomes: list[tuple[float, int, float]], unit: str
) -> tuple[NumericalAnswer, ...]:
    suffix = "" if unit == _DIMENSIONLESS else f" {unit}"
    return tuple(
        NumericalAnswer(
            name=outcome_probability(index),
            symbol=f"P(a = {value:.12g}{suffix})",
            label=f"probabilidade do resultado {index}, em ordem crescente de autovalor",
            value=probability,
            unit=_DIMENSIONLESS,
            estimate=None,
        )
        for index, (value, _, probability) in enumerate(outcomes, start=1)
    )


def _measurement_table(outcomes: list[tuple[float, int, float]], unit: str) -> SampleTable:
    return SampleTable(
        MEASUREMENT,
        "Resultados possíveis da medição e suas probabilidades",
        (
            SampleColumn(EIGENVALUE, "a", unit, tuple(value for value, _, _ in outcomes)),
            SampleColumn(
                DEGENERACY,
                "g",
                _DIMENSIONLESS,
                tuple(float(degeneracy) for _, degeneracy, _ in outcomes),
            ),
            SampleColumn(
                PROBABILITY,
                "p",
                _DIMENSIONLESS,
                tuple(probability for _, _, probability in outcomes),
            ),
        ),
    )


def _state_table(state: Amplitudes) -> SampleTable:
    return SampleTable(
        PREPARED_STATE,
        "Componentes do estado normalizado, na base em que a medição foi calculada",
        (
            SampleColumn(
                REAL_PART, "Re c", _DIMENSIONLESS, tuple(float(value.real) for value in state)
            ),
            SampleColumn(
                IMAGINARY_PART,
                "Im c",
                _DIMENSIONLESS,
                tuple(float(value.imag) for value in state),
            ),
        ),
    )


def _effective(problem: FiniteBasisProblem, separation: float) -> tuple[EffectiveParameter, ...]:
    given_norm = float(numpy.linalg.norm(numpy.array(problem.state, dtype=numpy.complex128)))
    normalization = (
        f"aplicada a pedido; a norma do estado informado era {given_norm!r}"
        if problem.normalize
        else f"não pedida; a norma do estado informado é {given_norm!r}"
    )
    basis = (
        "computacional, a da entrada"
        if problem.basis is None
        else "a base ortonormal informada; estado e observável foram reescritos nela"
    )
    return (
        EffectiveParameter("normalization", "normalização do estado", normalization),
        EffectiveParameter("basis", "base do cálculo", basis),
        EffectiveParameter("tolerance", "tolerância das checagens", repr(problem.tolerance)),
        EffectiveParameter(
            "degeneracy_separation",
            "separação abaixo da qual autovalores formam um subespaço",
            repr(separation),
        ),
        EffectiveParameter(
            "eigensolver", "diagonalização", "numpy.linalg.eigh, matriz hermitiana densa"
        ),
    )


def _measurement(problem: NumericalProblem) -> FiniteBasisProblem:
    if not isinstance(problem, FiniteBasisProblem):
        raise TypeError("the projective measurement solver needs a finite basis problem")
    return problem
