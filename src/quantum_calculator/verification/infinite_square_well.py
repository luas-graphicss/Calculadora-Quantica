from fractions import Fraction

import sympy

from quantum_calculator.domain.constants import PLANCK_CONSTANT
from quantum_calculator.domain.ports import ConstantsEdition, require_constant
from quantum_calculator.domain.solution import SolverReport
from quantum_calculator.domain.validated_problem import ValidatedProblem
from quantum_calculator.domain.verification import (
    EvidenceKind,
    SkippedCheck,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)

_SCALED_POSITION = sympy.Symbol("xi", real=True)
_LEVEL = sympy.Symbol("n", integer=True, positive=True)
_PLANCK = sympy.Symbol("h", positive=True)
_MASS = sympy.Symbol("m", positive=True)
_WIDTH = sympy.Symbol("L", positive=True)
_MODE = sympy.sin(_LEVEL * sympy.pi * _SCALED_POSITION)

_NOT_PERFORMED = (
    SkippedCheck(
        identifier="independent_discrete_solution",
        reason=(
            "Nenhum método numérico está homologado nesta versão para comparar com uma "
            "solução discreta independente."
        ),
    ),
)
_REFERENCES = (
    "D. J. Griffiths e D. F. Schroeter, Introduction to Quantum Mechanics, 3ª ed., "
    "Cambridge University Press, 2018, seção 2.2.",
)


class InfiniteSquareWellVerifier:
    def __init__(self, constants: ConstantsEdition) -> None:
        self._planck = require_constant(constants, PLANCK_CONSTANT)

    def verify(self, problem: ValidatedProblem, report: SolverReport) -> VerificationReport:
        return VerificationReport(
            checks=(
                _check_dimension(problem, report),
                self._check_stationary_equation(problem, report),
                _check_boundary(),
                _check_normalization(),
            ),
            not_performed=_NOT_PERFORMED,
            references=_REFERENCES,
        )

    def _check_stationary_equation(
        self, problem: ValidatedProblem, report: SolverReport
    ) -> VerificationCheck:
        curvature = sympy.diff(_MODE, _SCALED_POSITION, 2)
        local_energy = -(_PLANCK**2) / (8 * sympy.pi**2 * _MASS * _WIDTH**2) * curvature / _MODE
        eigenvalue = local_energy.subs(
            {
                _LEVEL: sympy.Integer(problem.count("level").value),
                _PLANCK: _to_rational(self._planck.value.magnitude),
                _MASS: _to_rational(problem.quantity("mass").quantity.magnitude),
                _WIDTH: _to_rational(problem.quantity("width").quantity.magnitude),
            }
        )
        is_eigenfunction = bool(eigenvalue.is_Rational)
        claimed = report.value.magnitude
        is_satisfied = (
            is_eigenfunction and Fraction(int(eigenvalue.p), int(eigenvalue.q)) == claimed
        )
        return VerificationCheck(
            identifier="stationary_schrodinger_residual",
            kind=EvidenceKind.PROOF,
            status=_status(is_satisfied),
            statement=(
                "psi_n(x) = sin(n pi x / L) satisfaz -(h^2 / (8 pi^2 m)) psi_n'' = E psi_n "
                "em 0 < x < L com a energia informada."
            ),
            observed=(
                "a razão -(h^2 / (8 pi^2 m)) psi_n'' / psi_n não depende da posição e é "
                "igual à energia informada"
                if is_satisfied
                else "a energia informada não é o autovalor que a equação dá para psi_n"
            ),
        )


def _check_dimension(problem: ValidatedProblem, report: SolverReport) -> VerificationCheck:
    declared = problem.output.rule.dimension
    is_consistent = report.value.dimension == declared == problem.output.unit.dimension
    return VerificationCheck(
        identifier="dimensional_consistency",
        kind=EvidenceKind.CONSISTENCY_TEST,
        status=_status(is_consistent),
        statement=(
            "O valor relatado e a unidade de exibição têm a dimensão que a ficha declara "
            "para a saída."
        ),
        observed=(
            f"valor relatado em {report.value.dimension.base_si_unit()}; "
            f"a ficha declara {declared.base_si_unit()}"
        ),
    )


def _check_boundary() -> VerificationCheck:
    left = _MODE.subs(_SCALED_POSITION, 0)
    right = _MODE.subs(_SCALED_POSITION, 1)
    return VerificationCheck(
        identifier="dirichlet_boundary",
        kind=EvidenceKind.PROOF,
        status=_status(left == 0 and right == 0),
        statement="psi_n se anula nas duas extremidades do poço para todo n inteiro positivo.",
        observed=f"psi_n(0) = {sympy.sstr(left)} e psi_n(L) = {sympy.sstr(right)}",
    )


def _check_normalization() -> VerificationCheck:
    scaled_norm = sympy.integrate(_MODE**2, (_SCALED_POSITION, 0, 1))
    return VerificationCheck(
        identifier="normalizable_mode",
        kind=EvidenceKind.PROOF,
        status=_status(scaled_norm == sympy.Rational(1, 2)),
        statement=(
            "A integral de psi_n(x)^2 em [0, L] vale L/2: o estado é normalizável, com "
            "constante sqrt(2/L)."
        ),
        observed=f"integral em x/L igual a {sympy.sstr(scaled_norm)}",
    )


def _status(is_satisfied: bool) -> VerificationStatus:
    return VerificationStatus.PASSED if is_satisfied else VerificationStatus.FAILED


def _to_rational(value: Fraction) -> sympy.Rational:
    return sympy.Rational(value.numerator, value.denominator)
