from dataclasses import dataclass

import numpy

from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.numerical.layout import (
    DENSITY,
    FINAL_DENSITY,
    NORM,
    NORM_DRIFT,
    OBSERVABLES,
    PHASE_ERROR,
    POSITION,
    REFERENCE_PHASE,
    RELATIVE_PHASE,
    STEPS,
    TIME,
    TIME_REFINEMENT,
    population,
)
from quantum_calculator.domain.numerical.problems import EvolutionProblem, NumericalProblem
from quantum_calculator.domain.numerical.report import (
    EffectiveParameter,
    NumericalAnswer,
    NumericalSolverReport,
    SampleColumn,
    SampleTable,
)
from quantum_calculator.numerics.evaluation import Samples
from quantum_calculator.numerics.failures import non_finite_result
from quantum_calculator.numerics.finite_basis import Amplitudes
from quantum_calculator.numerics.grid import node_positions, spacing, with_boundary_nodes
from quantum_calculator.numerics.hamiltonian import discrete_hamiltonian
from quantum_calculator.numerics.superposition import (
    beating_pair,
    mode_coefficients,
    relative_phase,
    wrapped,
)
from quantum_calculator.solvers.quantum.crank_nicolson import (
    FACTORIZATION,
    CrankNicolsonPropagator,
)
from quantum_calculator.solvers.quantum.eigenstates import DiscreteEigenstates, lowest_eigenstates

COARSENING_FACTORS = (4, 2)

_DIMENSIONLESS = "1"
_RADIAN = "rad"
_STATE = "O estado propagado"


@dataclass(frozen=True, slots=True)
class _Snapshot:
    scaled_time: float
    norm: float
    amplitudes: Amplitudes


@dataclass(frozen=True, slots=True)
class _Propagation:
    snapshots: tuple[_Snapshot, ...]
    final_state: Amplitudes


class CrankNicolsonEvolutionSolver:
    def solve(self, problem: NumericalProblem) -> NumericalSolverReport:
        evolution = _evolution(problem)
        states = lowest_eigenstates(
            evolution.grid, evolution.potential, len(evolution.coefficients)
        )
        coefficients = mode_coefficients(evolution)
        pair = beating_pair(evolution)
        run = _propagate(evolution, states, coefficients, evolution.steps, evolution.samples)
        norms = numpy.array([snapshot.norm for snapshot in run.snapshots])
        answers = [
            NumericalAnswer(
                name=NORM_DRIFT,
                symbol="max | ||psi(t)|| - ||psi(0)|| |",
                label="deriva máxima da norma nos instantes salvos",
                value=float(numpy.max(numpy.abs(norms - norms[0]))),
                unit=_DIMENSIONLESS,
                estimate=None,
            )
        ]
        tables = [_observables_table(evolution, states, coefficients, run, pair)]
        if pair is not None:
            errors = _phase_errors(states, coefficients, run.snapshots, pair)
            answers.append(
                NumericalAnswer(
                    name=PHASE_ERROR,
                    symbol="max |delta phi|",
                    label="erro máximo da fase relativa frente aos modos discretos exatos",
                    value=float(numpy.max(numpy.abs(errors))),
                    unit=_RADIAN,
                    estimate=None,
                )
            )
            tables.append(
                _time_refinement_table(evolution, states, coefficients, pair, abs(errors[-1]))
            )
        tables.append(_density_table(evolution, run.final_state))
        return NumericalSolverReport(
            nature=ResultNature.APPROXIMATE,
            answers=tuple(answers),
            tables=tuple(tables),
            effective=_effective(evolution, states, pair),
            warnings=(),
        )


def _propagate(
    problem: EvolutionProblem,
    states: DiscreteEigenstates,
    coefficients: Amplitudes,
    steps: int,
    samples: int,
) -> _Propagation:
    step = problem.scaled_duration / steps
    weight = spacing(problem.grid)
    propagator = CrankNicolsonPropagator(
        discrete_hamiltonian(problem.grid, problem.potential), step
    )
    stride = steps // (samples - 1)
    state = states.modes @ coefficients
    snapshots = [_snapshot(0.0, state, states.modes, weight)]
    for completed in range(1, steps + 1):
        state = propagator.advance(state)
        if completed % stride == 0:
            snapshots.append(_snapshot(completed * step, state, states.modes, weight))
    if not numpy.all(numpy.isfinite(state)):
        raise non_finite_result(_STATE)
    return _Propagation(tuple(snapshots), state)


def _snapshot(scaled_time: float, state: Amplitudes, modes: Samples, weight: float) -> _Snapshot:
    return _Snapshot(
        scaled_time=scaled_time,
        norm=float(numpy.sqrt(weight * numpy.sum(numpy.abs(state) ** 2))),
        amplitudes=weight * (modes.T @ state),
    )


def _reference_phase(
    states: DiscreteEigenstates, coefficients: Amplitudes, pair: tuple[int, int], scaled_time: float
) -> float:
    lower, upper = pair
    beat = float(states.energies[upper] - states.energies[lower])
    return wrapped(relative_phase(coefficients, pair) - beat * scaled_time)


def _phase_errors(
    states: DiscreteEigenstates,
    coefficients: Amplitudes,
    snapshots: tuple[_Snapshot, ...],
    pair: tuple[int, int],
) -> Samples:
    return numpy.array(
        [
            wrapped(
                relative_phase(snapshot.amplitudes, pair)
                - _reference_phase(states, coefficients, pair, snapshot.scaled_time)
            )
            for snapshot in snapshots
        ]
    )


def _observables_table(
    problem: EvolutionProblem,
    states: DiscreteEigenstates,
    coefficients: Amplitudes,
    run: _Propagation,
    pair: tuple[int, int] | None,
) -> SampleTable:
    snapshots = run.snapshots
    columns = [
        SampleColumn(
            TIME,
            "t",
            "s",
            tuple(snapshot.scaled_time * problem.scales.time for snapshot in snapshots),
        ),
        SampleColumn(NORM, "||psi||", _DIMENSIONLESS, tuple(item.norm for item in snapshots)),
    ]
    columns += [
        SampleColumn(
            population(level),
            f"|c_{level}|^2",
            _DIMENSIONLESS,
            tuple(float(abs(snapshot.amplitudes[level - 1]) ** 2) for snapshot in snapshots),
        )
        for level in range(1, len(problem.coefficients) + 1)
    ]
    if pair is not None:
        columns += [
            SampleColumn(
                RELATIVE_PHASE,
                "phi",
                _RADIAN,
                tuple(relative_phase(snapshot.amplitudes, pair) for snapshot in snapshots),
            ),
            SampleColumn(
                REFERENCE_PHASE,
                "phi exata dos modos discretos",
                _RADIAN,
                tuple(
                    _reference_phase(states, coefficients, pair, snapshot.scaled_time)
                    for snapshot in snapshots
                ),
            ),
        ]
    return SampleTable(OBSERVABLES, "Observáveis nos instantes salvos", tuple(columns))


def _time_refinement_table(
    problem: EvolutionProblem,
    states: DiscreteEigenstates,
    coefficients: Amplitudes,
    pair: tuple[int, int],
    finest_error: float,
) -> SampleTable:
    rows = []
    for factor in COARSENING_FACTORS:
        steps = problem.steps // factor
        coarse = _propagate(problem, states, coefficients, steps, samples=2)
        error = _phase_errors(states, coefficients, coarse.snapshots, pair)[-1]
        rows.append((float(steps), abs(float(error))))
    rows.append((float(problem.steps), float(finest_error)))
    steps_column, errors = zip(*rows, strict=True)
    return SampleTable(
        TIME_REFINEMENT,
        "Erro da fase relativa no instante final para cada número de passos",
        (
            SampleColumn(STEPS, "passos", _DIMENSIONLESS, steps_column),
            SampleColumn(PHASE_ERROR, "|delta phi|", _RADIAN, errors),
        ),
    )


def _density_table(problem: EvolutionProblem, final_state: Amplitudes) -> SampleTable:
    length = problem.scales.length
    density = with_boundary_nodes(numpy.abs(final_state) ** 2) / length
    return SampleTable(
        FINAL_DENSITY,
        "Densidade de probabilidade no instante final",
        (
            SampleColumn(
                POSITION,
                "x",
                "m",
                tuple((node_positions(problem.grid) * length).tolist()),
            ),
            SampleColumn(DENSITY, "|psi(x)|^2", "1/m", tuple(density.tolist())),
        ),
    )


def _effective(
    problem: EvolutionProblem, states: DiscreteEigenstates, pair: tuple[int, int] | None
) -> tuple[EffectiveParameter, ...]:
    scales = problem.scales
    step = problem.scaled_duration / problem.steps * scales.time
    given_norm = float(numpy.linalg.norm(numpy.array(problem.coefficients)))
    normalization = (
        f"aplicada a pedido; a norma dos coeficientes informados era {given_norm!r}"
        if problem.normalize
        else f"não pedida; a norma dos coeficientes informados é {given_norm!r}"
    )
    effective = [
        EffectiveParameter("length_scale", "escala de comprimento", f"{scales.length!r} m"),
        EffectiveParameter("energy_scale", "escala de energia", f"{scales.energy!r} J"),
        EffectiveParameter("time_scale", "escala de tempo", f"{scales.time!r} s"),
        EffectiveParameter("time_step", "passo de tempo", f"{step!r} s"),
        EffectiveParameter("steps", "passos", str(problem.steps)),
        EffectiveParameter("normalization", "normalização do estado inicial", normalization),
        EffectiveParameter(
            "linear_solver",
            "sistema linear",
            f"tridiagonal complexo fatorado uma vez ({FACTORIZATION}) e reutilizado em todos os "
            "passos; nenhuma inversa explícita",
        ),
        EffectiveParameter(
            "renormalization", "renormalização", "nenhuma: a norma não é corrigida entre passos"
        ),
        EffectiveParameter(
            "stored_states",
            "estados guardados",
            f"só os observáveis de {problem.samples} instantes e o estado final",
        ),
    ]
    if pair is not None:
        lower, upper = pair
        beat = float(states.energies[upper] - states.energies[lower])
        period = 2 * numpy.pi / beat * scales.time
        effective.append(
            EffectiveParameter(
                "beat_period",
                f"período de batimento dos modos discretos {lower + 1} e {upper + 1}",
                f"{float(period)!r} s",
            )
        )
    return tuple(effective)


def _evolution(problem: NumericalProblem) -> EvolutionProblem:
    if not isinstance(problem, EvolutionProblem):
        raise TypeError("the Crank-Nicolson solver needs an evolution problem")
    return problem
