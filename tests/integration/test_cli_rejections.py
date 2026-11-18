import io
import json
from pathlib import Path

import pytest

from quantum_calculator.adapters.execution.runtime_environment import RuntimeEnvironmentProbe
from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.review_problem import ReviewProblem
from quantum_calculator.application.solve_problem import HomologatedMethod, SolveProblem
from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.catalog.infinite_square_well import INFINITE_SQUARE_WELL_ENERGY_LEVEL
from quantum_calculator.composition import Calculator
from quantum_calculator.interfaces.cli.exit_codes import ExitCode
from quantum_calculator.interfaces.cli.main import main
from quantum_calculator.interfaces.cli.problem_commands import ProblemCommands
from quantum_calculator.interfaces.cli.rendering.renderer import OutputFormat, renderer_for
from quantum_calculator.interfaces.serialization.decoding.json_document import MAX_DOCUMENT_BYTES
from quantum_calculator.solvers.symbolic.infinite_square_well import InfiniteSquareWellSolver
from quantum_calculator.verification.infinite_square_well import InfiniteSquareWellVerifier
from support.cli import CliRunner, write_document
from support.documents import ProblemDocument
from support.solvers import DoubledEnergySolver

REJECTED = Path(__file__).resolve().parents[2] / "reference_cases" / "quantum" / "rejected"
EXPECTATIONS: list[dict[str, str]] = json.loads(
    (REJECTED / "expectations.json").read_text("utf-8")
)["cases"]
EXIT_CODE_BY_CATEGORY = {"invalid_input": 3, "unsupported_problem": 4}


@pytest.mark.parametrize("output_format", ["text", "json"])
@pytest.mark.parametrize("command", ["validate", "solve"])
@pytest.mark.parametrize("case", EXPECTATIONS, ids=lambda case: case["file"])
def test_rejected_input_exits_non_zero_and_prints_no_result(
    run_cli: CliRunner, case: dict[str, str], command: str, output_format: str
) -> None:
    result = run_cli(command, REJECTED / case["file"], "--format", output_format)

    assert result.exit_code == EXIT_CODE_BY_CATEGORY[case["category"]]
    assert result.stdout == ""
    assert case["pointer"] in result.stderr
    assert case["code"] in result.stderr


@pytest.mark.parametrize("case", EXPECTATIONS, ids=lambda case: case["file"])
def test_json_rejection_names_the_field_and_the_expected_restriction(
    run_cli: CliRunner, case: dict[str, str]
) -> None:
    result = run_cli("solve", REJECTED / case["file"], "--format", "json")

    rejection = json.loads(result.stderr)
    (diagnostic,) = rejection["diagnostics"]
    assert rejection["document"] == "rejection"
    assert rejection["category"] == case["category"]
    assert diagnostic["code"] == case["code"]
    assert diagnostic["pointer"] == case["pointer"]
    assert case["expected_mentions"] in diagnostic["expected"]


def test_text_rejection_shows_what_was_expected(run_cli: CliRunner) -> None:
    result = run_cli("solve", REJECTED / "width_in_seconds.json")

    assert result.stderr.splitlines()[0] == "Entrada recusada (invalid_input)"
    assert "/parameters/width/unit [dimension_mismatch]" in result.stderr
    assert "esperado: unidade de comprimento: m, mm," in result.stderr


def test_missing_file_is_an_operational_error_without_a_result(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    result = run_cli("solve", tmp_path / "absent.json")

    assert result.exit_code == ExitCode.INPUT_UNREADABLE
    assert result.stdout == ""
    assert "absent.json" in result.stderr


def test_malformed_json_is_invalid_input(run_cli: CliRunner, tmp_path: Path) -> None:
    result = run_cli("solve", write_document(tmp_path, b'{"schema_version": '))

    assert result.exit_code == ExitCode.INVALID_INPUT
    assert result.stdout == ""
    assert "malformed_json" in result.stderr


def test_document_over_the_size_limit_is_refused(run_cli: CliRunner, tmp_path: Path) -> None:
    oversized = b"{" + b" " * MAX_DOCUMENT_BYTES + b"}"

    result = run_cli("solve", write_document(tmp_path, oversized))

    assert result.exit_code == ExitCode.INVALID_INPUT
    assert "document_too_large" in result.stderr


def test_control_characters_from_the_input_do_not_reach_the_terminal(
    run_cli: CliRunner, electron_box: ProblemDocument, tmp_path: Path
) -> None:
    hostile = electron_box.with_value(
        "/parameters/width", {"value": 1, "unit": "\x1b[31mnm\x07"}
    ).with_value("/description", "linha\r\noutra\x1b[2J")

    rejection = run_cli("solve", write_document(tmp_path, hostile.encode()))
    accepted = run_cli(
        "validate",
        write_document(tmp_path, hostile.with_value("/parameters/width/unit", "nm").encode()),
    )

    assert rejection.exit_code == ExitCode.INVALID_INPUT
    assert "\x1b" not in rejection.stderr
    assert "\x07" not in rejection.stderr
    assert accepted.exit_code == ExitCode.SUCCESS
    assert "\x1b" not in accepted.stdout
    assert "\r" not in accepted.stdout


def test_command_line_misuse_exits_with_code_two() -> None:
    with pytest.raises(SystemExit) as termination:
        main(["solve"])

    assert termination.value.code == 2


def test_result_that_fails_verification_is_not_reported_as_success(
    validator: ProblemValidator,
    solver: InfiniteSquareWellSolver,
    verifier: InfiniteSquareWellVerifier,
    constants: Codata2022Constants,
    units: SiUnitRegistry,
    reference_cases: Path,
) -> None:
    methods = {
        INFINITE_SQUARE_WELL_ENERGY_LEVEL.method.identifier: HomologatedMethod(
            DoubledEnergySolver(solver), verifier
        )
    }
    faulty = Calculator(
        review_problem=ReviewProblem(validator),
        solve_problem=SolveProblem(validator, methods, constants, units, RuntimeEnvironmentProbe()),
        units=units,
    )
    stdout = io.StringIO()
    commands = ProblemCommands(
        faulty, renderer_for(OutputFormat.TEXT, units), stdout, io.StringIO()
    )

    exit_code = commands.solve(reference_cases / "electron_box_1nm.json")

    assert exit_code == ExitCode.VERIFICATION_NOT_PASSED
    assert "verificação: failed" in stdout.getvalue().splitlines()[1]
    assert "failed [proof] stationary_schrodinger_residual" in stdout.getvalue()
