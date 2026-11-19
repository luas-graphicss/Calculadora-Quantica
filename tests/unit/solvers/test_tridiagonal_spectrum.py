import math

import numpy
import pytest

from quantum_calculator.domain.numerical.layout import (
    EIGENFUNCTIONS,
    ENERGY,
    POSITION,
    REFINEMENT,
    SUBINTERVALS,
    TRUNCATION,
    eigenfunction,
    energy_level,
)
from quantum_calculator.domain.numerical.report import NumericalSolverReport
from quantum_calculator.solvers.quantum.stationary import TridiagonalSpectrumSolver
from support.numerical import (
    ELECTRON_MASS,
    ELECTRON_VOLT_IN_JOULES,
    JOULE,
    NANOMETER,
    PLANCK,
    column,
    oscillator_spectrum_problem,
    well_spectrum_problem,
)

SOLVER = TridiagonalSpectrumSolver()
LEVELS = (1, 2, 3)
ANALYTIC_WELL_GROUND_ENERGY_IN_EV = (
    PLANCK**2 / (8 * ELECTRON_MASS * NANOMETER**2) / float(ELECTRON_VOLT_IN_JOULES)
)


@pytest.fixture(scope="module")
def well() -> NumericalSolverReport:
    return SOLVER.solve(well_spectrum_problem(subintervals=512, levels=3))


@pytest.fixture(scope="module")
def oscillator() -> NumericalSolverReport:
    return SOLVER.solve(oscillator_spectrum_problem(half_width=8.0, subintervals=1024, levels=3))


def _energies_at(report: NumericalSolverReport, subintervals: int) -> list[float]:
    meshes = column(report, REFINEMENT, SUBINTERVALS)
    energies = column(report, REFINEMENT, ENERGY)
    return [energy for mesh, energy in zip(meshes, energies, strict=True) if mesh == subintervals]


@pytest.mark.numerical
@pytest.mark.parametrize("level", LEVELS)
def test_well_level_agrees_with_the_closed_form_within_the_mesh_error(
    well: NumericalSolverReport, level: int
) -> None:
    analytic = level**2 * ANALYTIC_WELL_GROUND_ENERGY_IN_EV

    answer = well.answer(energy_level(level))

    assert answer.unit == "eV"
    assert abs(answer.value - analytic) / analytic <= 3e-5


@pytest.mark.numerical
@pytest.mark.parametrize("level", LEVELS)
def test_well_energy_converges_with_second_order_over_three_meshes(
    well: NumericalSolverReport, level: int
) -> None:
    coarse, middle, fine = (_energies_at(well, mesh)[level - 1] for mesh in (128, 256, 512))

    observed_order = math.log2(abs(coarse - middle) / abs(middle - fine))

    assert 1.8 <= observed_order <= 2.2


@pytest.mark.numerical
@pytest.mark.parametrize("level", LEVELS)
def test_reported_mesh_error_estimates_the_distance_to_the_closed_form(
    well: NumericalSolverReport, level: int
) -> None:
    answer = well.answer(energy_level(level))
    actual_error = abs(answer.value - level**2 * ANALYTIC_WELL_GROUND_ENERGY_IN_EV)

    assert answer.estimate is not None
    assert "Richardson" in answer.estimate.origin
    assert answer.estimate.value == pytest.approx(actual_error, rel=1e-3)


@pytest.mark.numerical
def test_512_subintervals_mean_511_interior_unknowns_and_513_reported_nodes(
    well: NumericalSolverReport,
) -> None:
    positions = column(well, EIGENFUNCTIONS, POSITION)
    effective = {parameter.name: parameter.value for parameter in well.effective}

    assert len(positions) == 513
    assert positions[0] == 0.0
    assert positions[-1] == pytest.approx(NANOMETER, rel=1e-15)
    assert effective["unknowns"] == "511"


@pytest.mark.numerical
@pytest.mark.parametrize("level", LEVELS)
def test_eigenfunction_vanishes_at_the_walls_and_is_normalized_over_the_grid(
    well: NumericalSolverReport, level: int
) -> None:
    amplitudes = numpy.array(column(well, EIGENFUNCTIONS, eigenfunction(level)))
    step = NANOMETER / 512

    assert amplitudes[0] == 0.0
    assert amplitudes[-1] == 0.0
    assert step * numpy.sum(amplitudes**2) == pytest.approx(1.0, abs=1e-12)
    assert numpy.sum(amplitudes**2) != pytest.approx(1.0, rel=0.5)


@pytest.mark.numerical
@pytest.mark.parametrize("level", LEVELS)
def test_eigenfunction_follows_the_analytic_mode_with_a_positive_first_lobe(
    well: NumericalSolverReport, level: int
) -> None:
    positions = numpy.array(column(well, EIGENFUNCTIONS, POSITION))
    analytic = math.sqrt(2 / NANOMETER) * numpy.sin(level * math.pi * positions / NANOMETER)

    amplitudes = numpy.array(column(well, EIGENFUNCTIONS, eigenfunction(level)))

    assert amplitudes == pytest.approx(analytic, abs=1e-9 * math.sqrt(2 / NANOMETER))


@pytest.mark.numerical
def test_energy_in_joules_is_the_same_level_in_another_unit() -> None:
    in_joules = SOLVER.solve(well_spectrum_problem(levels=1, energy_unit=JOULE))
    in_electron_volts = SOLVER.solve(well_spectrum_problem(levels=1))

    assert in_joules.answer(energy_level(1)).unit == "J"
    assert in_joules.answer(energy_level(1)).value == pytest.approx(
        in_electron_volts.answer(energy_level(1)).value * float(ELECTRON_VOLT_IN_JOULES),
        rel=1e-14,
    )


def test_scales_that_recover_physical_length_energy_and_time_are_recorded(
    well: NumericalSolverReport,
) -> None:
    effective = {parameter.name: parameter.value for parameter in well.effective}

    assert effective["length_scale"] == "1e-09 m"
    assert effective["energy_scale"].endswith(" J")
    assert effective["time_scale"].endswith(" s")
    assert "nenhuma matriz densa" in effective["eigensolver"]


def test_only_the_requested_levels_are_returned() -> None:
    report = SOLVER.solve(well_spectrum_problem(subintervals=64, levels=2))

    assert [answer.name for answer in report.answers] == ["energy_1", "energy_2"]
    assert [table.name for table in report.tables] == [EIGENFUNCTIONS, REFINEMENT]


@pytest.mark.numerical
@pytest.mark.parametrize("level", LEVELS)
def test_oscillator_level_agrees_with_the_infinite_domain_spectrum(
    oscillator: NumericalSolverReport, level: int
) -> None:
    analytic_in_ev = level - 0.5

    answer = oscillator.answer(energy_level(level))

    assert abs(answer.value - analytic_in_ev) / analytic_in_ev < 1e-3


@pytest.mark.numerical
def test_widening_the_oscillator_domain_at_fixed_spacing_leaves_the_levels_unchanged(
    oscillator: NumericalSolverReport,
) -> None:
    energies = column(oscillator, TRUNCATION, ENERGY)
    requested, widened = energies[0::2], energies[1::2]

    assert len(requested) == 3
    assert widened == pytest.approx(requested, rel=1e-10)


@pytest.mark.numerical
def test_domain_that_cuts_the_oscillator_states_shows_up_in_the_truncation_table() -> None:
    cramped = SOLVER.solve(oscillator_spectrum_problem(half_width=2.0, subintervals=256))

    energies = column(cramped, TRUNCATION, ENERGY)

    assert abs(energies[5] - energies[4]) / energies[4] > 1e-2
