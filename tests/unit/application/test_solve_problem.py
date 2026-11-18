from dataclasses import replace

import pytest

from quantum_calculator.adapters.execution.runtime_environment import RuntimeEnvironmentProbe
from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.solve_problem import HomologatedMethod, SolveProblem
from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.composition import Calculator
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.ports import Solver
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.run_record import RunRecord
from quantum_calculator.domain.solution import SolverReport
from quantum_calculator.domain.validated_problem import ValidatedProblem
from quantum_calculator.domain.verification import VerificationStatus
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem
from quantum_calculator.solvers.symbolic.infinite_square_well import InfiniteSquareWellSolver
from quantum_calculator.verification.infinite_square_well import InfiniteSquareWellVerifier
from support.documents import ProblemDocument


class DoubledEnergySolver:
    def __init__(self, honest: Solver) -> None:
        self._honest = honest

    def solve(self, problem: ValidatedProblem) -> SolverReport:
        report = self._honest.solve(problem)
        doubled = Quantity(2 * report.value.magnitude, report.value.dimension)
        return replace(report, value=doubled)


def _execute(calculator: Calculator, document: ProblemDocument) -> RunRecord:
    return calculator.solve_problem.execute(decode_problem(document.encode()))


def test_reference_case_yields_a_verified_exact_record(
    calculator: Calculator, electron_box: ProblemDocument
) -> None:
    record = _execute(calculator, electron_box)

    assert record.plan.method.nature is ResultNature.EXACT
    assert record.plan.rounding.significant_digits == 10
    assert record.verification.status is VerificationStatus.PASSED
    assert record.constants_edition == "CODATA 2022"
    assert record.unit_registry_version == "1.0.0"
    assert [constant.identifier for constant in record.constants] == [
        "planck_constant",
        "electron_mass",
        "electron_volt",
    ]


def test_only_constants_that_took_part_are_recorded(
    calculator: Calculator, electron_box: ProblemDocument
) -> None:
    document = electron_box.with_value(
        "/parameters/mass", {"value": "9.1093837139e-31", "unit": "kg"}
    ).with_value("/requested/unit", "J")

    record = _execute(calculator, document)

    assert [constant.identifier for constant in record.constants] == ["planck_constant"]


def test_rejected_input_never_reaches_a_record(
    calculator: Calculator, electron_box: ProblemDocument
) -> None:
    document = electron_box.with_value("/parameters/width", {"value": 0, "unit": "nm"})

    with pytest.raises(ProblemRejectedError):
        _execute(calculator, document)


def test_a_wrong_solver_result_is_recorded_as_failed_verification(
    validator: ProblemValidator,
    solver: InfiniteSquareWellSolver,
    verifier: InfiniteSquareWellVerifier,
    constants: Codata2022Constants,
    units: SiUnitRegistry,
    electron_box: ProblemDocument,
) -> None:
    card_method = validator.validate(decode_problem(electron_box.encode())).card.method
    methods = {card_method.identifier: HomologatedMethod(DoubledEnergySolver(solver), verifier)}
    solve_problem = SolveProblem(validator, methods, constants, units, RuntimeEnvironmentProbe())

    record = solve_problem.execute(decode_problem(electron_box.encode()))

    assert record.verification.status is VerificationStatus.FAILED
