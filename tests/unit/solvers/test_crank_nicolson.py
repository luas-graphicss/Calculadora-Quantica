import math

import numpy
import pytest

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
from quantum_calculator.domain.numerical.problems import PotentialModel, ScaledGrid
from quantum_calculator.domain.numerical.report import NumericalSolverReport
from quantum_calculator.numerics.grid import interior_positions, weighted_norm
from quantum_calculator.numerics.hamiltonian import discrete_hamiltonian
from quantum_calculator.solvers.quantum.crank_nicolson import CrankNicolsonPropagator
from quantum_calculator.solvers.quantum.evolution import CrankNicolsonEvolutionSolver
from support.numerical import (
    NANOMETER,
    column,
    discrete_beat_period,
    discrete_well_energy,
    well_evolution_problem,
    well_scales,
)

SOLVER = CrankNicolsonEvolutionSolver()
GRID = ScaledGrid(left=0.0, right=1.0, subintervals=64)


@pytest.fixture(scope="module")
def beat() -> NumericalSolverReport:
    return SOLVER.solve(well_evolution_problem(subintervals=256, steps=1024, samples=9))


@pytest.mark.numerical
def test_one_step_multiplies_a_discrete_mode_by_the_cayley_factor() -> None:
    step = 1e-3
    mode = numpy.sin(math.pi * interior_positions(GRID)).astype(numpy.complex128)
    energy = discrete_well_energy(1, 64)
    cayley_factor = (1 - 0.5j * step * energy) / (1 + 0.5j * step * energy)

    advanced = CrankNicolsonPropagator(
        discrete_hamiltonian(GRID, PotentialModel.ZERO), step
    ).advance(mode)

    assert advanced == pytest.approx(cayley_factor * mode, abs=1e-13)


@pytest.mark.numerical
def test_factorization_is_reused_and_the_norm_survives_many_steps_without_rescaling() -> None:
    positions = interior_positions(GRID)
    packet = (numpy.exp(-200 * (positions - 0.3) ** 2) * numpy.exp(40j * positions)).astype(
        numpy.complex128
    )
    propagator = CrankNicolsonPropagator(discrete_hamiltonian(GRID, PotentialModel.ZERO), 1e-4)
    initial_norm = weighted_norm(GRID, packet)

    for _ in range(2000):
        packet = propagator.advance(packet)

    assert weighted_norm(GRID, packet) == pytest.approx(initial_norm, rel=1e-11)


@pytest.mark.numerical
def test_norm_drifts_less_than_one_part_in_a_billion_over_a_beat_period(
    beat: NumericalSolverReport,
) -> None:
    norms = column(beat, OBSERVABLES, NORM)

    assert max(abs(norm - norms[0]) for norm in norms) <= 1e-9
    assert beat.answer(NORM_DRIFT).value <= 1e-9
    assert norms[0] == pytest.approx(1.0, abs=1e-12)


@pytest.mark.numerical
def test_relative_phase_stays_within_a_milliradian_of_the_exact_discrete_modes(
    beat: NumericalSolverReport,
) -> None:
    reported = column(beat, OBSERVABLES, RELATIVE_PHASE)
    exact = column(beat, OBSERVABLES, REFERENCE_PHASE)

    errors = [
        math.remainder(found - expected, 2 * math.pi)
        for found, expected in zip(reported, exact, strict=True)
    ]

    assert max(abs(error) for error in errors) <= 1e-3
    assert beat.answer(PHASE_ERROR).value <= 1e-3
    assert beat.answer(PHASE_ERROR).unit == "rad"


@pytest.mark.numerical
def test_reference_phase_is_the_beat_of_the_two_discrete_energies(
    beat: NumericalSolverReport,
) -> None:
    scaled_times = numpy.array(column(beat, OBSERVABLES, TIME)) / well_scales().time
    beat_frequency = discrete_well_energy(2, 256) - discrete_well_energy(1, 256)

    exact = column(beat, OBSERVABLES, REFERENCE_PHASE)

    for scaled_time, phase in zip(scaled_times, exact, strict=True):
        assert math.remainder(phase + beat_frequency * scaled_time, 2 * math.pi) == pytest.approx(
            0.0, abs=1e-9
        )


@pytest.mark.numerical
def test_phase_error_falls_with_second_order_when_the_step_is_halved(
    beat: NumericalSolverReport,
) -> None:
    steps = column(beat, TIME_REFINEMENT, STEPS)
    errors = column(beat, TIME_REFINEMENT, PHASE_ERROR)

    assert steps == (256.0, 512.0, 1024.0)
    assert 1.8 <= math.log2(errors[0] / errors[1]) <= 2.2
    assert 1.8 <= math.log2(errors[1] / errors[2]) <= 2.2


@pytest.mark.numerical
def test_populations_of_the_two_modes_stay_at_one_half(beat: NumericalSolverReport) -> None:
    assert column(beat, OBSERVABLES, population(1)) == pytest.approx([0.5] * 9, abs=1e-9)
    assert column(beat, OBSERVABLES, population(2)) == pytest.approx([0.5] * 9, abs=1e-9)


@pytest.mark.numerical
def test_saved_instants_span_exactly_one_discrete_beat_period(beat: NumericalSolverReport) -> None:
    instants = column(beat, OBSERVABLES, TIME)

    assert len(instants) == 9
    assert instants[0] == 0.0
    assert instants[-1] == pytest.approx(discrete_beat_period(256) * well_scales().time, rel=1e-12)


@pytest.mark.numerical
def test_final_density_integrates_to_one_over_the_well(beat: NumericalSolverReport) -> None:
    positions = column(beat, FINAL_DENSITY, POSITION)
    density = column(beat, FINAL_DENSITY, DENSITY)

    assert len(positions) == 257
    assert density[0] == 0.0
    assert density[-1] == 0.0
    assert sum(density) * NANOMETER / 256 == pytest.approx(1.0, abs=1e-9)


def test_only_observables_and_the_final_state_are_kept(beat: NumericalSolverReport) -> None:
    effective = {parameter.name: parameter.value for parameter in beat.effective}

    assert [table.name for table in beat.tables] == [OBSERVABLES, TIME_REFINEMENT, FINAL_DENSITY]
    assert "reutilizado" in effective["linear_solver"]
    assert effective["renormalization"].startswith("nenhuma")
    assert "9 instantes" in effective["stored_states"]
    assert effective["normalization"].startswith("aplicada a pedido")


@pytest.mark.numerical
def test_single_stationary_state_has_no_relative_phase_to_report() -> None:
    stationary = SOLVER.solve(
        well_evolution_problem((1 + 0j,), subintervals=64, steps=64, samples=5, normalize=False)
    )

    assert [answer.name for answer in stationary.answers] == [NORM_DRIFT]
    assert [table.name for table in stationary.tables] == [OBSERVABLES, FINAL_DENSITY]
    assert column(stationary, OBSERVABLES, population(1)) == pytest.approx([1.0] * 5, abs=1e-9)
