import math

import numpy

from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.numerical.layout import (
    EIGENFUNCTIONS,
    ENERGY,
    HALF_WIDTH,
    LEVEL,
    POSITION,
    REFINEMENT,
    SUBINTERVALS,
    TRUNCATION,
    eigenfunction,
    energy_level,
)
from quantum_calculator.domain.numerical.problems import NumericalProblem, SpectrumProblem
from quantum_calculator.domain.numerical.report import (
    EffectiveParameter,
    ErrorEstimate,
    NumericalAnswer,
    NumericalSolverReport,
    SampleColumn,
    SampleTable,
)
from quantum_calculator.numerics.evaluation import Samples
from quantum_calculator.numerics.grid import (
    node_positions,
    spacing,
    widened,
    with_boundary_nodes,
    with_subintervals,
)
from quantum_calculator.solvers.quantum.eigenstates import (
    EIGENSOLVER,
    lowest_eigenstates,
    lowest_energies,
)

COARSENING_FACTORS = (4, 2)
WIDENING = (5, 4)

_DIMENSIONLESS = "1"
_RICHARDSON_DIVISOR = 3.0


class TridiagonalSpectrumSolver:
    def solve(self, problem: NumericalProblem) -> NumericalSolverReport:
        spectrum = _spectrum(problem)
        grid, potential, levels = spectrum.grid, spectrum.potential, spectrum.levels
        states = lowest_eigenstates(grid, potential, levels)
        by_mesh = {
            grid.subintervals // factor: lowest_energies(
                with_subintervals(grid, grid.subintervals // factor), potential, levels
            )
            for factor in COARSENING_FACTORS
        }
        by_mesh[grid.subintervals] = states.energies
        mesh_errors = (
            numpy.abs(states.energies - by_mesh[grid.subintervals // 2]) / _RICHARDSON_DIVISOR
        )
        tables = [
            _eigenfunction_table(spectrum, states.modes),
            _refinement_table(spectrum, by_mesh),
        ]
        if spectrum.is_truncated_domain:
            wider = lowest_energies(widened(grid, *WIDENING), potential, levels)
            tables.append(_truncation_table(spectrum, states.energies, wider))
        return NumericalSolverReport(
            nature=ResultNature.APPROXIMATE,
            answers=_answers(spectrum, states.energies, mesh_errors),
            tables=tuple(tables),
            effective=_effective(spectrum),
            warnings=(),
        )


def _display_factor(problem: SpectrumProblem) -> float:
    return problem.scales.energy / float(problem.energy_unit.si_factor)


def _answers(
    problem: SpectrumProblem, energies: Samples, mesh_errors: Samples
) -> tuple[NumericalAnswer, ...]:
    factor = _display_factor(problem)
    half = problem.grid.subintervals // 2
    origin = (
        f"erro de malha estimado por extrapolação de Richardson entre {half} e "
        f"{problem.grid.subintervals} subintervalos"
    )
    return tuple(
        NumericalAnswer(
            name=energy_level(level),
            symbol=f"E_{level}",
            label=f"energia do nível {level}, contado a partir do fundamental",
            value=float(energies[level - 1]) * factor,
            unit=problem.energy_unit.symbol,
            estimate=ErrorEstimate(float(mesh_errors[level - 1]) * factor, origin),
        )
        for level in range(1, problem.levels + 1)
    )


def _eigenfunction_table(problem: SpectrumProblem, modes: Samples) -> SampleTable:
    length = problem.scales.length
    amplitudes = with_boundary_nodes(modes) / math.sqrt(length)
    columns = [SampleColumn(POSITION, "x", "m", _as_tuple(node_positions(problem.grid) * length))]
    columns += [
        SampleColumn(
            eigenfunction(level), f"psi_{level}(x)", "m^-1/2", _as_tuple(amplitudes[:, level - 1])
        )
        for level in range(1, problem.levels + 1)
    ]
    return SampleTable(
        EIGENFUNCTIONS,
        "Autofunções normalizadas pela integral na malha, com os extremos nulos restaurados",
        tuple(columns),
    )


def _refinement_table(problem: SpectrumProblem, by_mesh: dict[int, Samples]) -> SampleTable:
    factor = _display_factor(problem)
    rows = [
        (float(level), float(subintervals), float(energies[level - 1]) * factor)
        for level in range(1, problem.levels + 1)
        for subintervals, energies in sorted(by_mesh.items())
    ]
    return SampleTable(
        REFINEMENT,
        "Energia de cada nível em cada malha do estudo de refinamento",
        _columns(rows, SUBINTERVALS, "N", _DIMENSIONLESS, problem.energy_unit.symbol),
    )


def _truncation_table(problem: SpectrumProblem, energies: Samples, wider: Samples) -> SampleTable:
    factor = _display_factor(problem)
    half_width = (problem.grid.right - problem.grid.left) / 2 * problem.scales.length
    wider_half_width = half_width * WIDENING[0] / WIDENING[1]
    rows = [
        (float(level), width, float(values[level - 1]) * factor)
        for level in range(1, problem.levels + 1)
        for width, values in ((half_width, energies), (wider_half_width, wider))
    ]
    return SampleTable(
        TRUNCATION,
        "Energia de cada nível no domínio pedido e no domínio ampliado, com o mesmo espaçamento",
        _columns(rows, HALF_WIDTH, "a", "m", problem.energy_unit.symbol),
    )


def _columns(
    rows: list[tuple[float, float, float]], name: str, symbol: str, unit: str, energy_unit: str
) -> tuple[SampleColumn, ...]:
    levels, settings, energies = zip(*rows, strict=True)
    return (
        SampleColumn(LEVEL, "nível", _DIMENSIONLESS, levels),
        SampleColumn(name, symbol, unit, settings),
        SampleColumn(ENERGY, "E", energy_unit, energies),
    )


def _effective(problem: SpectrumProblem) -> tuple[EffectiveParameter, ...]:
    scales = problem.scales
    grid = problem.grid
    return (
        EffectiveParameter("length_scale", "escala de comprimento", f"{scales.length!r} m"),
        EffectiveParameter("energy_scale", "escala de energia", f"{scales.energy!r} J"),
        EffectiveParameter("time_scale", "escala de tempo", f"{scales.time!r} s"),
        EffectiveParameter(
            "spacing", "espaçamento da malha", f"{spacing(grid) * scales.length!r} m"
        ),
        EffectiveParameter("unknowns", "incógnitas internas", str(grid.subintervals - 1)),
        EffectiveParameter(
            "eigensolver",
            "diagonalização",
            f"{EIGENSOLVER} sobre as diagonais, só os níveis 1 a {problem.levels}; nenhuma "
            "matriz densa",
        ),
        EffectiveParameter(
            "termination", "motivo de término", "os níveis pedidos convergiram no LAPACK"
        ),
    )


def _as_tuple(values: Samples) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _spectrum(problem: NumericalProblem) -> SpectrumProblem:
    if not isinstance(problem, SpectrumProblem):
        raise TypeError("the tridiagonal spectrum solver needs a spectrum problem")
    return problem
