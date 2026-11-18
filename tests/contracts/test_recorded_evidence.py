import json
from pathlib import Path

import pytest

from support.cli import CliRunner
from support.evidence import before_environment, scientific_content


@pytest.fixture(scope="module")
def evidence(repository_root: Path) -> Path:
    return repository_root / "docs" / "evidence" / "phase-1"


@pytest.mark.parametrize("case", ["electron_box_1nm", "electron_box_1nm_uncertainty"])
def test_recorded_run_record_is_what_the_cli_produces_now(
    run_cli: CliRunner, reference_cases: Path, evidence: Path, case: str
) -> None:
    recorded = json.loads((evidence / f"{case}.run_record.json").read_text("utf-8"))

    result = run_cli("solve", reference_cases / f"{case}.json", "--format", "json")

    assert scientific_content(json.loads(result.stdout)) == scientific_content(recorded)


def test_recorded_text_report_is_what_the_cli_produces_now(
    run_cli: CliRunner, reference_cases: Path, evidence: Path
) -> None:
    recorded = (evidence / "electron_box_1nm.solve.txt").read_text("utf-8")

    result = run_cli("solve", reference_cases / "electron_box_1nm.json")

    assert before_environment(result.stdout) == before_environment(recorded)


def test_recorded_validation_is_what_the_cli_produces_now(
    run_cli: CliRunner, reference_cases: Path, evidence: Path
) -> None:
    recorded = (evidence / "electron_box_1nm.validate.txt").read_text("utf-8")

    assert run_cli("validate", reference_cases / "electron_box_1nm.json").stdout == recorded


def test_recorded_rejection_is_what_the_cli_produces_now(
    run_cli: CliRunner, reference_cases: Path, evidence: Path
) -> None:
    recorded = (evidence / "width_in_seconds.rejection.json").read_text("utf-8")

    result = run_cli(
        "solve", reference_cases / "rejected" / "width_in_seconds.json", "--format", "json"
    )

    assert result.exit_code == 3
    assert result.stdout == ""
    assert result.stderr == recorded
