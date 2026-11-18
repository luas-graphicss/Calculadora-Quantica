import json
from pathlib import Path

import pytest

from quantum_calculator.interfaces.cli.exit_codes import ExitCode
from support.cli import CliRunner
from support.evidence import before_environment, scientific_content

RECORDED_REPORTS = [
    "decay_initial_value",
    "decay_candidate_wrong_initial_value",
    "decay_candidate_wrong_sign",
]
RECORDED_RUN_RECORDS = ["decay_initial_value", "decay_candidate_wrong_initial_value"]


@pytest.fixture(scope="module")
def evidence(repository_root: Path) -> Path:
    return repository_root / "docs" / "evidence" / "phase-2"


@pytest.mark.parametrize(("output_format", "extension"), [("text", "txt"), ("json", "json")])
def test_recorded_catalog_is_what_the_cli_produces_now(
    run_cli: CliRunner, evidence: Path, output_format: str, extension: str
) -> None:
    recorded = (evidence / f"catalog.{extension}").read_text("utf-8")

    assert run_cli("catalog", "--format", output_format).stdout == recorded


def test_recorded_preview_is_what_the_cli_produces_now(
    run_cli: CliRunner, symbolic_cases: Path, evidence: Path
) -> None:
    recorded = (evidence / "product_rule.validate.txt").read_text("utf-8")

    assert run_cli("validate", symbolic_cases / "product_rule.json").stdout == recorded


@pytest.mark.parametrize("case", RECORDED_RUN_RECORDS)
def test_recorded_statement_run_record_is_what_the_cli_produces_now(
    run_cli: CliRunner, symbolic_cases: Path, evidence: Path, case: str
) -> None:
    recorded = json.loads((evidence / f"{case}.run_record.json").read_text("utf-8"))

    result = run_cli("solve", symbolic_cases / f"{case}.json", "--format", "json")

    assert scientific_content(json.loads(result.stdout)) == scientific_content(recorded)


@pytest.mark.parametrize("case", RECORDED_REPORTS)
def test_recorded_statement_report_is_what_the_cli_produces_now(
    run_cli: CliRunner, symbolic_cases: Path, evidence: Path, case: str
) -> None:
    recorded = (evidence / f"{case}.solve.txt").read_text("utf-8")

    result = run_cli("solve", symbolic_cases / f"{case}.json")

    assert before_environment(result.stdout) == before_environment(recorded)


@pytest.mark.parametrize(("output_format", "extension"), [("text", "txt"), ("json", "json")])
def test_recorded_ambiguity_refusal_is_what_the_cli_produces_now(
    run_cli: CliRunner, symbolic_cases: Path, evidence: Path, output_format: str, extension: str
) -> None:
    recorded = (evidence / f"ambiguous_division.rejection.{extension}").read_text("utf-8")

    result = run_cli(
        "solve", symbolic_cases / "rejected" / "ambiguous_division.json", "--format", output_format
    )

    assert result.exit_code == ExitCode.AMBIGUOUS_INPUT
    assert result.stdout == ""
    assert result.stderr == recorded


def test_recorded_budget_refusal_is_what_the_cli_produces_now(
    run_cli: CliRunner, symbolic_cases: Path, evidence: Path
) -> None:
    recorded = (evidence / "time_budget_exceeded.rejection.txt").read_text("utf-8")

    result = run_cli("solve", symbolic_cases / "product_rule.json", "--time-limit", "0.05")

    assert result.exit_code == ExitCode.BUDGET_EXCEEDED
    assert result.stdout == ""
    assert result.stderr == recorded
