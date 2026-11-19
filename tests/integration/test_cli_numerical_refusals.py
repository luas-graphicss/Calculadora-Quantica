import io
import json
import multiprocessing
import threading
from pathlib import Path

import pytest

from quantum_calculator.composition import Calculator, build_calculator
from quantum_calculator.domain.execution import (
    CalculationFailedError,
    CancellationSignal,
    NeverCancelled,
)
from quantum_calculator.interfaces.cli.exit_codes import ExitCode
from quantum_calculator.interfaces.cli.problem_commands import ProblemCommands
from quantum_calculator.interfaces.cli.rendering.renderer import OutputFormat, renderer_for
from support.cli import CliResult, CliRunner, write_document
from support.execution import RaisingExecutor
from support.numerical_documents import REFUSALS, REJECTED, numerical_document

EXIT_CODE_BY_CATEGORY = {
    "invalid_input": 3,
    "unsupported_problem": 4,
    "budget_exceeded": 7,
    "non_convergent": 9,
}
WELL = "electron_box_1nm_discrete.json"


def _solve(calculator: Calculator, path: Path, cancellation: CancellationSignal) -> CliResult:
    stdout = io.StringIO()
    stderr = io.StringIO()
    commands = ProblemCommands(
        calculator,
        renderer_for(OutputFormat.TEXT, calculator.units),
        stdout,
        stderr,
        cancellation,
    )
    exit_code = commands.solve(path)
    return CliResult(exit_code=exit_code, stdout=stdout.getvalue(), stderr=stderr.getvalue())


def test_every_refused_numerical_input_has_an_expectation_with_its_reason() -> None:
    files = {path.name for path in REJECTED.glob("*.json")} - {"expectations.json"}

    assert {case["file"] for case in REFUSALS} == files
    assert all(case["reason"] for case in REFUSALS)
    assert {"non_hermitian_operator", "zero_state", "incompatible_condition"} <= {
        case["code"] for case in REFUSALS
    }
    assert {"missing_initial_state.json", "resource_limit.json"} <= files


@pytest.mark.parametrize("case", REFUSALS, ids=lambda case: case["file"])
def test_refused_numerical_input_exits_non_zero_and_prints_no_result(
    run_cli: CliRunner, case: dict[str, str]
) -> None:
    result = run_cli("solve", REJECTED / case["file"])

    assert result.exit_code == EXIT_CODE_BY_CATEGORY[case["category"]]
    assert result.stdout == ""
    assert result.stderr.splitlines()[0] == f"Entrada recusada ({case['category']})"
    assert f"{case['pointer'] or '/'} [{case['code']}]" in result.stderr


@pytest.mark.parametrize("case", REFUSALS, ids=lambda case: case["file"])
def test_json_refusal_names_one_field_one_code_and_what_was_expected(
    run_cli: CliRunner, case: dict[str, str]
) -> None:
    result = run_cli("solve", REJECTED / case["file"], "--format", "json")

    rejection = json.loads(result.stderr)
    (diagnostic,) = rejection["diagnostics"]
    assert result.stdout == ""
    assert rejection["document"] == "rejection"
    assert rejection["category"] == case["category"]
    assert diagnostic["code"] == case["code"]
    assert diagnostic["pointer"] == case["pointer"]
    assert diagnostic["expected"]


def test_request_over_the_profile_is_refused_without_starting_a_calculation_process() -> None:
    never_started = build_calculator(
        executor=RaisingExecutor(AssertionError("the calculation was started"))
    )

    outcome = _solve(never_started, REJECTED / "resource_limit.json", NeverCancelled())

    assert outcome.exit_code == ExitCode.BUDGET_EXCEEDED
    assert outcome.stdout == ""
    assert "Nada foi alocado" in outcome.stderr


def test_method_that_does_not_converge_approves_no_answer(run_cli: CliRunner) -> None:
    result = run_cli("solve", REJECTED / "divergent_integral.json")

    assert result.exit_code == ExitCode.NON_CONVERGENT
    assert result.stdout == ""
    assert "a integral provavelmente diverge" in result.stderr
    assert "Nenhuma resposta foi aprovada." in result.stderr
    assert multiprocessing.active_children() == []


def test_input_refused_by_the_method_still_passes_validation(run_cli: CliRunner) -> None:
    result = run_cli("validate", REJECTED / "divergent_integral.json")

    assert result.exit_code == ExitCode.SUCCESS
    assert "integral(1/x, x, -1, 2)" in result.stdout


def test_numerical_calculation_over_the_time_limit_is_refused_without_a_result(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    result = run_cli("solve", numerical_cases / WELL, "--time-limit", "0.05")

    assert result.exit_code == ExitCode.BUDGET_EXCEEDED
    assert result.stdout == ""
    assert "/ [time_budget_exceeded]" in result.stderr
    assert "O cálculo numérico passou do limite de 0.05 s de relógio." in result.stderr
    assert multiprocessing.active_children() == []


def test_cancelled_numerical_calculation_prints_no_result_and_the_next_one_runs(
    calculator: Calculator, numerical_cases: Path
) -> None:
    case = numerical_cases / WELL
    requested = threading.Event()
    requested.set()

    cancelled = _solve(calculator, case, requested)
    following = _solve(calculator, case, NeverCancelled())

    assert cancelled.exit_code == ExitCode.CANCELLED
    assert cancelled.stdout == ""
    assert (
        cancelled.stderr == "qcalc: cálculo cancelado; nenhum resultado parcial foi aproveitado.\n"
    )
    assert following.exit_code == ExitCode.SUCCESS
    assert multiprocessing.active_children() == []


def test_numerical_process_that_dies_is_an_operational_failure_not_a_result(
    numerical_cases: Path,
) -> None:
    crashing = build_calculator(executor=RaisingExecutor(CalculationFailedError(3)))

    outcome = _solve(crashing, numerical_cases / WELL, NeverCancelled())

    assert outcome.exit_code == ExitCode.CALCULATION_FAILED
    assert outcome.stdout == ""
    assert "código de saída 3" in outcome.stderr


def test_control_characters_from_a_numerical_input_do_not_reach_the_terminal(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    described = numerical_document("sine_quadrature").with_value(
        "/description", "linha\r\noutra\x1b[31m"
    )

    accepted = run_cli("validate", write_document(tmp_path, described.encode()))

    assert accepted.exit_code == ExitCode.SUCCESS
    assert "\x1b" not in accepted.stdout
    assert "\r" not in accepted.stdout
