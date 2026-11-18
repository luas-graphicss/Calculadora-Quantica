from fractions import Fraction

import pytest

from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.domain.dimensions import ENERGY
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.solution import SolverReport
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem
from quantum_calculator.solvers.symbolic.infinite_square_well import InfiniteSquareWellSolver
from support.documents import ProblemDocument

pytestmark = pytest.mark.algebraic

PLANCK = Fraction("6.62607015e-34")
ELECTRON_MASS = Fraction("9.1093837139e-31")
ANGSTROM = "\N{LATIN CAPITAL LETTER A WITH RING ABOVE}"


@pytest.fixture
def solve(validator: ProblemValidator, solver: InfiniteSquareWellSolver) -> "Solve":
    return Solve(validator, solver)


class Solve:
    def __init__(self, validator: ProblemValidator, solver: InfiniteSquareWellSolver) -> None:
        self._validator = validator
        self._solver = solver

    def report(self, document: ProblemDocument) -> SolverReport:
        return self._solver.solve(self._validator.validate(decode_problem(document.encode())))

    def energy(self, document: ProblemDocument) -> Fraction:
        return self.report(document).value.magnitude


def test_energy_equals_the_closed_form_computed_with_plain_fractions(
    solve: Solve, electron_box: ProblemDocument
) -> None:
    width = Fraction(1, 10**9)

    assert solve.energy(electron_box) == PLANCK**2 / (8 * ELECTRON_MASS * width**2)


def test_one_nanometer_and_ten_angstrom_give_the_same_energy(
    solve: Solve, electron_box: ProblemDocument
) -> None:
    in_angstrom = electron_box.with_value("/parameters/width", {"value": 10, "unit": ANGSTROM})

    assert solve.energy(in_angstrom) == solve.energy(electron_box)


@pytest.mark.parametrize("width", ["1", "0.37", "1/3", "2.5e-1"])
def test_doubling_the_width_divides_the_energy_by_four(
    solve: Solve, electron_box: ProblemDocument, width: str
) -> None:
    doubled = str(2 * Fraction(width))
    narrow = electron_box.with_value("/parameters/width", {"value": width, "unit": "nm"})
    wide = electron_box.with_value("/parameters/width", {"value": doubled, "unit": "nm"})

    assert solve.energy(wide) == solve.energy(narrow) / 4


def test_second_level_has_four_times_the_energy_of_the_first(
    solve: Solve, electron_box: ProblemDocument
) -> None:
    second = electron_box.with_value("/parameters/level", 2)

    assert solve.energy(second) == 4 * solve.energy(electron_box)


@pytest.mark.parametrize("level", [3, 7, 100])
def test_energy_grows_with_the_square_of_the_level(
    solve: Solve, electron_box: ProblemDocument, level: int
) -> None:
    excited = electron_box.with_value("/parameters/level", level)

    assert solve.energy(excited) == level**2 * solve.energy(electron_box)


def test_doubling_the_mass_halves_the_energy(solve: Solve, electron_box: ProblemDocument) -> None:
    heavy = electron_box.with_value(
        "/parameters/mass", {"value": str(2 * ELECTRON_MASS), "unit": "kg"}
    )

    assert solve.energy(heavy) == solve.energy(electron_box) / 2


def test_explicit_mass_and_catalog_constant_agree(
    solve: Solve, electron_box: ProblemDocument
) -> None:
    explicit = electron_box.with_value(
        "/parameters/mass", {"value": "9.1093837139e-31", "unit": "kg"}
    )

    assert solve.energy(explicit) == solve.energy(electron_box)


def test_report_states_an_exact_energy_with_its_calculation_memory(
    solve: Solve, electron_box: ProblemDocument
) -> None:
    report = solve.report(electron_box)

    numerator, denominator, energy = (step.value for step in report.steps[1:])
    assert report.nature is ResultNature.EXACT
    assert report.value.dimension == ENERGY
    assert report.expression.plain == "E_n = h**2*n**2/(8*L**2*m)"
    assert [constant.identifier for constant in report.constants] == ["planck_constant"]
    assert numerator is not None
    assert denominator is not None
    assert numerator.magnitude == PLANCK**2
    assert denominator.magnitude == 8 * ELECTRON_MASS * Fraction(1, 10**18)
    assert energy == report.value
    assert report.uncertainty is None
