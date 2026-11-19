import math

import numpy

from quantum_calculator.domain.numerical.layout import (
    EIGENFUNCTIONS,
    ENERGY,
    REFINEMENT,
    SUBINTERVALS,
    TRUNCATION,
    eigenfunction,
    energy_level,
)
from quantum_calculator.domain.numerical.problems import (
    NumericalProblem,
    ScaledGrid,
    SpectrumProblem,
)
from quantum_calculator.domain.numerical.report import NumericalSolverReport, SampleTable
from quantum_calculator.domain.verification import (
    EvidenceKind,
    SkippedCheck,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)
from quantum_calculator.numerics.closed_forms import scaled_energy
from quantum_calculator.numerics.evaluation import Samples
from quantum_calculator.numerics.grid import spacing, widened, with_subintervals
from quantum_calculator.numerics.hamiltonian import discrete_hamiltonian
from quantum_calculator.verification.numerical.checks import (
    bounded_check,
    inconclusive_check,
    scientific,
)

RESIDUAL_LIMIT = 1e-10
ORTHONORMALITY_LIMIT = 1e-10
OBSERVED_ORDER_RANGE = (1.8, 2.2)
TRUNCATION_LIMIT = 1e-9

_PLACEMENT_WINDOW = 1e-9
_AGREEMENT_SAFETY = 2.0
_RICHARDSON_DIVISOR = 3.0
_WIDENING = (5, 4)
_RESIDUAL_STATEMENT = (
    "Cada par relatado satisfaz o problema discreto: o resíduo ||H psi - E psi|| / "
    "((||H||_inf + |E|) ||psi||) fica abaixo do limite. Isso confere o operador discreto, "
    "não a convergência da malha."
)
_ORTHONORMALITY_STATEMENT = (
    "As autofunções relatadas são ortonormais com o peso da malha: a integral discreta de "
    "psi_i psi_j difere da identidade menos que o limite."
)
_BOUNDARY_STATEMENT = "As autofunções relatadas se anulam nos dois extremos do domínio."
_PLACEMENT_STATEMENT = (
    "Abaixo da energia relatada do nível k há exatamente k - 1 autovalores do operador "
    "discreto, contados pela inércia sem diagonalizar: nenhum nível foi pulado."
)
_REFINEMENT_STATEMENT = (
    "Dobrando a malha duas vezes, a diferença entre energias cai com ordem observada entre "
    f"{OBSERVED_ORDER_RANGE[0]} e {OBSERVED_ORDER_RANGE[1]} em todos os níveis, o que indica "
    "o regime assintótico de segunda ordem."
)
_TRUNCATION_STATEMENT = (
    "Ampliar o domínio em 25%, com o mesmo espaçamento, não muda as energias além do "
    "limite relativo: o corte do domínio não contamina os níveis pedidos."
)
_AGREEMENT_STATEMENT = (
    "As energias discretas concordam com a expressão fechada do modelo dentro de duas vezes "
    "o erro de malha estimado."
)
_WALLS_ARE_THE_MODEL = SkippedCheck(
    "domain_truncation", "As paredes fazem parte do modelo: não há domínio a ampliar."
)
_REFERENCES = (
    "D. J. Griffiths e D. F. Schroeter, Introduction to Quantum Mechanics, 3ª ed., "
    "Cambridge University Press, 2018, seções 2.2 e 2.3.",
    "R. J. LeVeque, Finite Difference Methods for Ordinary and Partial Differential "
    "Equations, SIAM, 2007, capítulo 2.",
)


class SpectrumVerifier:
    def verify(
        self, problem: NumericalProblem, report: NumericalSolverReport
    ) -> VerificationReport:
        spectrum = _spectrum(problem)
        factor = spectrum.scales.energy / float(spectrum.energy_unit.si_factor)
        levels = range(1, spectrum.levels + 1)
        energies = numpy.array([report.answer(energy_level(level)).value for level in levels])
        energies /= factor
        table = report.table(EIGENFUNCTIONS)
        amplitudes = numpy.array([table.column(eigenfunction(level)).values for level in levels])
        modes = amplitudes.T * math.sqrt(spectrum.scales.length)
        refinement = _energies_by_setting(report.table(REFINEMENT), SUBINTERVALS, factor)
        checks = [
            _residual_check(spectrum, energies, modes[1:-1]),
            _orthonormality_check(spectrum, modes[1:-1]),
            _boundary_check(modes),
            _placement_check(spectrum, energies),
            _refinement_check(spectrum, energies, refinement),
        ]
        not_performed: tuple[SkippedCheck, ...] = (_WALLS_ARE_THE_MODEL,)
        if spectrum.is_truncated_domain:
            checks.append(_truncation_check(spectrum, energies, report.table(TRUNCATION), factor))
            not_performed = ()
        checks.append(_agreement_check(spectrum, energies, refinement))
        return VerificationReport(tuple(checks), not_performed, _REFERENCES)


def _residual_check(
    problem: SpectrumProblem, energies: Samples, modes: Samples
) -> VerificationCheck:
    operator = discrete_hamiltonian(problem.grid, problem.potential)
    defects = numpy.linalg.norm(operator.apply(modes.copy()) - modes * energies, axis=0)
    scales = (operator.infinity_norm() + numpy.abs(energies)) * numpy.linalg.norm(modes, axis=0)
    return bounded_check(
        "discrete_residual",
        EvidenceKind.NUMERICAL_EVIDENCE,
        _RESIDUAL_STATEMENT,
        float(numpy.max(defects / scales)),
        RESIDUAL_LIMIT,
        "maior resíduo adimensional:",
    )


def _orthonormality_check(problem: SpectrumProblem, modes: Samples) -> VerificationCheck:
    gram = spacing(problem.grid) * modes.T @ modes
    return bounded_check(
        "weighted_orthonormality",
        EvidenceKind.NUMERICAL_EVIDENCE,
        _ORTHONORMALITY_STATEMENT,
        float(numpy.max(numpy.abs(gram - numpy.eye(problem.levels)))),
        ORTHONORMALITY_LIMIT,
        "maior desvio da identidade:",
    )


def _boundary_check(modes: Samples) -> VerificationCheck:
    return bounded_check(
        "dirichlet_boundary",
        EvidenceKind.CONSISTENCY_TEST,
        _BOUNDARY_STATEMENT,
        float(numpy.max(numpy.abs(modes[[0, -1]]))),
        0.0,
        "maior valor nos extremos:",
    )


def _misplaced_levels(grid: ScaledGrid, problem: SpectrumProblem, energies: Samples) -> list[int]:
    operator = discrete_hamiltonian(grid, problem.potential)
    misplaced = []
    for level, energy in enumerate(energies, start=1):
        window = _PLACEMENT_WINDOW * max(abs(float(energy)), 1.0)
        below = operator.eigenvalues_below(float(energy) - window)
        through = operator.eigenvalues_below(float(energy) + window)
        if (below, through) != (level - 1, level):
            misplaced.append(level)
    return misplaced


def _placement_check(problem: SpectrumProblem, energies: Samples) -> VerificationCheck:
    misplaced = _misplaced_levels(problem.grid, problem, energies)
    return VerificationCheck(
        "level_placement",
        EvidenceKind.NUMERICAL_EVIDENCE,
        VerificationStatus.FAILED if misplaced else VerificationStatus.PASSED,
        _PLACEMENT_STATEMENT,
        f"a contagem não confirma os níveis {misplaced}"
        if misplaced
        else f"a contagem confirma os níveis 1 a {len(energies)}",
    )


def _refinement_check(
    problem: SpectrumProblem, energies: Samples, refinement: dict[float, Samples]
) -> VerificationCheck:
    fine = problem.grid.subintervals
    meshes = (fine // 4, fine // 2, fine)
    if sorted(refinement) != [float(mesh) for mesh in meshes]:
        return _refinement_outcome(
            VerificationStatus.FAILED, "a tabela de refinamento não traz as três malhas do estudo"
        )
    coarse, middle, reported = (refinement[float(mesh)] for mesh in meshes)
    is_consistent = numpy.allclose(
        reported, energies, rtol=_PLACEMENT_WINDOW, atol=0.0
    ) and not any(
        _misplaced_levels(with_subintervals(problem.grid, mesh), problem, refinement[float(mesh)])
        for mesh in meshes[:2]
    )
    if not is_consistent:
        return _refinement_outcome(
            VerificationStatus.FAILED,
            "as energias da tabela de refinamento não são os níveis do operador discreto de "
            "cada malha",
        )
    last_change = numpy.abs(middle - reported)
    if numpy.any(last_change == 0.0):
        return _refinement_outcome(
            VerificationStatus.INCONCLUSIVE,
            "a energia não mudou entre as duas malhas mais finas: a ordem não fica definida",
        )
    orders = numpy.log2(numpy.abs(coarse - middle) / last_change)
    lowest, highest = float(numpy.min(orders)), float(numpy.max(orders))
    described = (
        f"ordem observada entre {lowest:.3f} e {highest:.3f} com {meshes[0]}, {meshes[1]} e "
        f"{meshes[2]} subintervalos"
    )
    if lowest < OBSERVED_ORDER_RANGE[0] or highest > OBSERVED_ORDER_RANGE[1]:
        return _refinement_outcome(
            VerificationStatus.INCONCLUSIVE,
            f"{described}: a malha não está no regime assintótico e não é declarada convergida",
        )
    relative = float(numpy.max(last_change / _RICHARDSON_DIVISOR / numpy.abs(reported)))
    return _refinement_outcome(
        VerificationStatus.PASSED,
        f"{described}; erro de malha relativo estimado até {scientific(relative)}",
    )


def _refinement_outcome(status: VerificationStatus, observed: str) -> VerificationCheck:
    return VerificationCheck(
        "mesh_refinement", EvidenceKind.NUMERICAL_EVIDENCE, status, _REFINEMENT_STATEMENT, observed
    )


def _truncation_check(
    problem: SpectrumProblem, energies: Samples, table: SampleTable, factor: float
) -> VerificationCheck:
    by_width = _energies_by_setting(table, table.columns[1].name, factor)
    wider = by_width[max(by_width)]
    if _misplaced_levels(widened(problem.grid, *_WIDENING), problem, wider):
        return VerificationCheck(
            "domain_truncation",
            EvidenceKind.NUMERICAL_EVIDENCE,
            VerificationStatus.FAILED,
            _TRUNCATION_STATEMENT,
            "as energias do domínio ampliado não são os níveis do operador discreto ampliado",
        )
    return bounded_check(
        "domain_truncation",
        EvidenceKind.NUMERICAL_EVIDENCE,
        _TRUNCATION_STATEMENT,
        float(numpy.max(numpy.abs(wider - energies) / numpy.abs(energies))),
        TRUNCATION_LIMIT,
        "maior mudança relativa:",
    )


def _agreement_check(
    problem: SpectrumProblem, energies: Samples, refinement: dict[float, Samples]
) -> VerificationCheck:
    half = refinement.get(float(problem.grid.subintervals // 2))
    if half is None:
        return inconclusive_check(
            "closed_form_agreement",
            EvidenceKind.NUMERICAL_EVIDENCE,
            _AGREEMENT_STATEMENT,
            "sem a malha intermediária não há erro de malha estimado para comparar",
        )
    closed = numpy.array(
        [
            scaled_energy(problem.potential, problem.grid, level)
            for level in range(1, len(energies) + 1)
        ]
    )
    mesh_errors = numpy.abs(energies - half) / _RICHARDSON_DIVISOR
    return bounded_check(
        "closed_form_agreement",
        EvidenceKind.NUMERICAL_EVIDENCE,
        _AGREEMENT_STATEMENT,
        float(numpy.max(numpy.abs(energies - closed) / mesh_errors)),
        _AGREEMENT_SAFETY,
        "maior diferença, em unidades do erro de malha estimado:",
    )


def _energies_by_setting(table: SampleTable, setting: str, factor: float) -> dict[float, Samples]:
    settings = table.column(setting).values
    energies = table.column(ENERGY).values
    return {
        value: numpy.array(
            [energy for found, energy in zip(settings, energies, strict=True) if found == value]
        )
        / factor
        for value in dict.fromkeys(settings)
    }


def _spectrum(problem: NumericalProblem) -> SpectrumProblem:
    if not isinstance(problem, SpectrumProblem):
        raise TypeError("the spectrum verifier needs a spectrum problem")
    return problem
