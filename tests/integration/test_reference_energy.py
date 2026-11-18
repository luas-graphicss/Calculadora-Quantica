import json
from fractions import Fraction
from pathlib import Path

import pytest

from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem
from quantum_calculator.solvers.symbolic.infinite_square_well import InfiniteSquareWellSolver


@pytest.mark.numerical
def test_reference_energy_agrees_with_the_oracle_within_its_tolerance(
    validator: ProblemValidator, solver: InfiniteSquareWellSolver, reference_cases: Path
) -> None:
    oracle = json.loads((reference_cases / "electron_box_1nm.expected.json").read_text("utf-8"))
    problem = validator.validate(decode_problem((reference_cases / oracle["case"]).read_bytes()))

    energy = problem.output.unit.from_si(solver.solve(problem).value)

    assert problem.output.unit.symbol == oracle["unit"]
    assert abs(energy - Fraction(oracle["nominal_value"])) <= Fraction(oracle["absolute_tolerance"])
