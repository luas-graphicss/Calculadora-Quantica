import json
from pathlib import Path

import pytest

from support.cli import CliRunner

ENVIRONMENT_SECTION = "\nAmbiente\n"


@pytest.fixture(scope="module")
def evidence(repository_root: Path) -> Path:
    return repository_root / "docs" / "evidence" / "phase-1"


def _scientific_content(document: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in document.items() if key != "environment"}


@pytest.mark.parametrize("case", ["electron_box_1nm", "electron_box_1nm_uncertainty"])
def test_recorded_run_record_is_what_the_cli_produces_now(
    run_cli: CliRunner, reference_cases: Path, evidence: Path, case: str
) -> None:
    recorded = json.loads((evidence / f"{case}.run_record.json").read_text("utf-8"))

    result = run_cli("solve", reference_cases / f"{case}.json", "--format", "json")

    assert _scientific_content(json.loads(result.stdout)) == _scientific_content(recorded)


def test_recorded_text_report_is_what_the_cli_produces_now(
    run_cli: CliRunner, reference_cases: Path, evidence: Path
) -> None:
    recorded = (evidence / "electron_box_1nm.solve.txt").read_text("utf-8")

    result = run_cli("solve", reference_cases / "electron_box_1nm.json")

    assert ENVIRONMENT_SECTION in recorded
    assert result.stdout.split(ENVIRONMENT_SECTION)[0] == recorded.split(ENVIRONMENT_SECTION)[0]


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
