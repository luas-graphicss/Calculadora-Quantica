import cmath

import numpy
from numpy.typing import NDArray

from quantum_calculator.domain.numerical.layout import (
    DEGENERACY,
    EIGENVALUE,
    EXPECTATION_VALUE,
    IMAGINARY_PART,
    MEASUREMENT,
    PREPARED_STATE,
    PROBABILITY,
    REAL_PART,
)
from quantum_calculator.domain.numerical.problems import FiniteBasisProblem, NumericalProblem
from quantum_calculator.domain.numerical.report import NumericalSolverReport
from quantum_calculator.domain.verification import (
    EvidenceKind,
    VerificationCheck,
    VerificationReport,
)
from quantum_calculator.numerics.finite_basis import (
    Amplitudes,
    observable_matrix,
    operator_scale,
    prepared_state,
)
from quantum_calculator.verification.numerical.checks import bounded_check

_PHASE = cmath.exp(1j)
_HERMITIAN_STATEMENT = "O observável é igual ao seu adjunto conjugado."
_NORM_STATEMENT = "O estado usado no cálculo tem norma 1."
_TOTAL_STATEMENT = "As probabilidades dos resultados somam 1."
_PROJECTOR_STATEMENT = (
    "Cada probabilidade é o valor esperado do projetor sobre o subespaço do autovalor, "
    "construído do próprio observável sem usar os autovetores do solver, com o posto igual "
    "à degenerescência relatada."
)
_EXPECTATION_STATEMENT = (
    "O valor esperado relatado é o produto direto do estado pelo observável, na base da entrada."
)
_PHASE_STATEMENT = "Multiplicar o estado por uma fase global não muda as probabilidades."
_REFERENCES = (
    "J. J. Sakurai e J. Napolitano, Modern Quantum Mechanics, 3ª ed., Cambridge University "
    "Press, 2020, seções 1.2 a 1.5.",
)


class FiniteBasisVerifier:
    def verify(
        self, problem: NumericalProblem, report: NumericalSolverReport
    ) -> VerificationReport:
        measurement = _measurement(problem)
        state = prepared_state(measurement)
        observable = observable_matrix(measurement)
        tolerance = measurement.tolerance
        scaled_tolerance = tolerance * operator_scale(observable)
        outcomes = report.table(MEASUREMENT)
        eigenvalues = numpy.array(outcomes.column(EIGENVALUE).values)
        probabilities = numpy.array(outcomes.column(PROBABILITY).values)
        projectors = _spectral_projectors(observable, eigenvalues)
        ranks = numpy.array([float(numpy.trace(projector).real) for projector in projectors])
        return VerificationReport(
            checks=(
                _check(
                    "hermitian_operator",
                    EvidenceKind.CONSISTENCY_TEST,
                    _HERMITIAN_STATEMENT,
                    float(numpy.max(numpy.abs(observable - observable.conj().T))),
                    scaled_tolerance,
                    "maior diferença entre o observável e o adjunto:",
                ),
                _check(
                    "normalized_state",
                    EvidenceKind.CONSISTENCY_TEST,
                    _NORM_STATEMENT,
                    abs(float(numpy.linalg.norm(_reported_state(report))) - 1.0),
                    tolerance,
                    "desvio da norma:",
                ),
                _check(
                    "total_probability",
                    EvidenceKind.CONSISTENCY_TEST,
                    _TOTAL_STATEMENT,
                    abs(float(numpy.sum(probabilities)) - 1.0),
                    tolerance,
                    "desvio da soma:",
                ),
                _check(
                    "subspace_projectors",
                    EvidenceKind.NUMERICAL_EVIDENCE,
                    _PROJECTOR_STATEMENT,
                    max(
                        _largest(probabilities - _expectations(projectors, state)),
                        _largest(ranks - numpy.array(outcomes.column(DEGENERACY).values)),
                    ),
                    tolerance,
                    "maior desvio em probabilidade ou em posto:",
                ),
                _check(
                    "direct_expectation_value",
                    EvidenceKind.NUMERICAL_EVIDENCE,
                    _EXPECTATION_STATEMENT,
                    abs(
                        report.answer(EXPECTATION_VALUE).value
                        - float(numpy.vdot(state, observable @ state).real)
                    ),
                    scaled_tolerance,
                    "diferença para o produto direto:",
                ),
                _check(
                    "global_phase_invariance",
                    EvidenceKind.CONSISTENCY_TEST,
                    _PHASE_STATEMENT,
                    _largest(probabilities - _expectations(projectors, _PHASE * state)),
                    tolerance,
                    "maior mudança de probabilidade:",
                ),
            ),
            not_performed=(),
            references=_REFERENCES,
        )


def _check(
    identifier: str,
    kind: EvidenceKind,
    statement: str,
    measured: float,
    limit: float,
    quantity: str,
) -> VerificationCheck:
    return bounded_check(identifier, kind, statement, measured, limit, quantity)


def _spectral_projectors(
    observable: Amplitudes, eigenvalues: NDArray[numpy.float64]
) -> list[Amplitudes]:
    identity = numpy.eye(len(observable), dtype=numpy.complex128)
    projectors = []
    for index, eigenvalue in enumerate(eigenvalues):
        projector = identity
        for other in numpy.delete(eigenvalues, index):
            projector = projector @ (observable - other * identity) / (eigenvalue - other)
        projectors.append(projector)
    return projectors


def _expectations(projectors: list[Amplitudes], state: Amplitudes) -> NDArray[numpy.float64]:
    return numpy.array(
        [float(numpy.vdot(state, projector @ state).real) for projector in projectors]
    )


def _reported_state(report: NumericalSolverReport) -> Amplitudes:
    table = report.table(PREPARED_STATE)
    real = numpy.array(table.column(REAL_PART).values)
    return real + 1j * numpy.array(table.column(IMAGINARY_PART).values)


def _largest(deviations: NDArray[numpy.float64]) -> float:
    return float(numpy.max(numpy.abs(deviations)))


def _measurement(problem: NumericalProblem) -> FiniteBasisProblem:
    if not isinstance(problem, FiniteBasisProblem):
        raise TypeError("the finite basis verifier needs a finite basis problem")
    return problem
