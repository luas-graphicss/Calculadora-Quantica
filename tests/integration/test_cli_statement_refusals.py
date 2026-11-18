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
from quantum_calculator.interfaces.cli.main import main
from quantum_calculator.interfaces.cli.problem_commands import ProblemCommands
from quantum_calculator.interfaces.cli.rendering.renderer import OutputFormat, renderer_for
from support.cli import CliResult, CliRunner, write_document
from support.corpus import ACCEPTED, ITEMS, corpus_document, expected_of
from support.execution import RaisingExecutor
from support.statements import CALCULUS, statement_document

REJECTED = Path(__file__).resolve().parents[2] / "reference_cases" / "symbolic" / "rejected"
EXPECTATIONS: list[dict[str, str]] = json.loads(
    (REJECTED / "expectations.json").read_text("utf-8")
)["cases"]
EXIT_CODE_BY_CATEGORY = {
    "invalid_input": 3,
    "unsupported_problem": 4,
    "ambiguous_input": 6,
    "budget_exceeded": 7,
}
EXIT_CODE_BY_CLASSIFICATION = {ACCEPTED: 0, **EXIT_CODE_BY_CATEGORY}


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


def test_every_refused_reference_statement_has_an_expectation_with_its_reason() -> None:
    files = {path.name for path in REJECTED.glob("*.json")} - {"expectations.json"}

    assert {case["file"] for case in EXPECTATIONS} == files
    assert all(case["reason"] for case in EXPECTATIONS)


@pytest.mark.parametrize("case", EXPECTATIONS, ids=lambda case: case["file"])
def test_refused_statement_exits_non_zero_and_prints_no_result(
    run_cli: CliRunner, case: dict[str, str]
) -> None:
    result = run_cli("solve", REJECTED / case["file"])

    assert result.exit_code == EXIT_CODE_BY_CATEGORY[case["category"]]
    assert result.stdout == ""
    assert result.stderr.splitlines()[0] == f"Entrada recusada ({case['category']})"
    assert f"{case['pointer']} [{case['code']}]" in result.stderr


@pytest.mark.parametrize("case", EXPECTATIONS, ids=lambda case: case["file"])
def test_json_refusal_names_the_field_the_code_and_the_stretch(
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
    if "excerpt" in case:
        excerpt = diagnostic["excerpt"]
        assert excerpt["text"][excerpt["start"] : excerpt["end"]] == case["excerpt"]


def test_text_refusal_marks_the_ambiguous_stretch_under_the_statement(run_cli: CliRunner) -> None:
    result = run_cli("validate", REJECTED / "ambiguous_division.json")

    statement, marker = result.stderr.splitlines()[4:6]
    assert result.exit_code == ExitCode.AMBIGUOUS_INPUT
    assert statement == "    trecho: diff(1/2x, x)"
    assert marker == " " * statement.index("1/2x") + "^^^^"


def test_confirmation_is_requested_when_more_than_one_card_fits(run_cli: CliRunner) -> None:
    result = run_cli("solve", REJECTED / "unconfirmed_card.json")

    assert result.exit_code == ExitCode.AMBIGUOUS_INPUT
    assert "ode.first_order_linear.general_solution (sem conditions nem candidate)" in result.stderr
    assert "ode.first_order_linear.initial_value (exige conditions)" in result.stderr
    assert "ode.first_order_linear.candidate_review (exige conditions e candidate)" in result.stderr


@pytest.mark.parametrize("item", ITEMS, ids=lambda item: item["id"])
def test_corpus_item_gets_its_labelled_classification_from_the_cli(
    run_cli: CliRunner, tmp_path: Path, item: dict[str, object]
) -> None:
    classification = expected_of(item)["classification"]
    document = write_document(tmp_path, corpus_document(item))

    result = run_cli("validate", document, "--format", "json")

    assert result.exit_code == EXIT_CODE_BY_CLASSIFICATION[classification]
    if classification == ACCEPTED:
        assert result.stderr == ""
        assert json.loads(result.stdout)["document"] == "statement_validation"
    else:
        assert result.stdout == ""
        assert json.loads(result.stderr)["category"] == classification


def test_statement_document_without_its_statement_is_diagnosed_as_a_statement(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    document = json.dumps({"schema_version": "1.0", "notation": "text", "symbols": CALCULUS})

    result = run_cli("validate", write_document(tmp_path, document.encode("utf-8")))

    assert result.exit_code == ExitCode.INVALID_INPUT
    assert "/statement [missing_field]" in result.stderr
    assert "/parameters" not in result.stderr


def test_control_characters_from_a_statement_do_not_reach_the_terminal(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    hostile = statement_document("diff(x^2, x)\x1b[2J", CALCULUS)
    described = statement_document("diff(x^2, x)", CALCULUS, description="linha\r\noutra\x1b[31m")

    refused = run_cli("validate", write_document(tmp_path, hostile))
    accepted = run_cli("validate", write_document(tmp_path, described))

    assert refused.exit_code == ExitCode.INVALID_INPUT
    assert "\x1b" not in refused.stderr
    assert accepted.exit_code == ExitCode.SUCCESS
    assert "\x1b" not in accepted.stdout
    assert "\r" not in accepted.stdout


def test_calculation_over_the_time_limit_is_refused_without_a_result(
    run_cli: CliRunner, symbolic_cases: Path
) -> None:
    result = run_cli("solve", symbolic_cases / "product_rule.json", "--time-limit", "0.05")

    assert result.exit_code == ExitCode.BUDGET_EXCEEDED
    assert result.stdout == ""
    assert "/ [time_budget_exceeded]" in result.stderr
    assert multiprocessing.active_children() == []


@pytest.mark.parametrize("limit", ["0", "-1", "601", "nan", "soon"])
def test_time_limit_outside_the_accepted_range_is_command_line_misuse(
    symbolic_cases: Path, limit: str
) -> None:
    with pytest.raises(SystemExit) as termination:
        main(["solve", str(symbolic_cases / "product_rule.json"), "--time-limit", limit])

    assert termination.value.code == 2


def test_cancelled_calculation_prints_no_result_and_the_next_one_runs(
    calculator: Calculator, symbolic_cases: Path
) -> None:
    case = symbolic_cases / "product_rule.json"
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


def test_calculation_process_that_dies_is_an_operational_failure_not_a_result(
    symbolic_cases: Path,
) -> None:
    crashing = build_calculator(executor=RaisingExecutor(CalculationFailedError(3)))

    outcome = _solve(crashing, symbolic_cases / "product_rule.json", NeverCancelled())

    assert outcome.exit_code == ExitCode.CALCULATION_FAILED
    assert outcome.stdout == ""
    assert "código de saída 3" in outcome.stderr
