import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from support.api import signed_in_api, solved
from support.cli import CliRunner
from support.evidence import scientific_content

_CASES = [
    "quantum/electron_box_1nm.json",
    "quantum/electron_box_1nm_uncertainty.json",
    "symbolic/decay_initial_value.json",
    "symbolic/decay_candidate_wrong_initial_value.json",
    "numerical/sine_quadrature.json",
]


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with signed_in_api(tmp_path / "profile") as opened:
        yield opened


def _without_input(document: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in document.items() if key != "input"}


@pytest.mark.parametrize("case", _CASES)
def test_the_bench_records_the_canonical_problem_the_cli_validates(
    client: TestClient, run_cli: CliRunner, repository_root: Path, case: str
) -> None:
    path = repository_root / "reference_cases" / case
    validated = json.loads(run_cli("validate", path, "--format", "json").stdout)

    details = solved(client, path.read_bytes(), "agreement-key-1")

    assert details["problem"] == _without_input(validated)


@pytest.mark.parametrize("case", _CASES)
def test_the_bench_records_the_method_and_the_result_the_cli_prints(
    client: TestClient, run_cli: CliRunner, repository_root: Path, case: str
) -> None:
    path = repository_root / "reference_cases" / case
    printed = json.loads(run_cli("solve", path, "--format", "json").stdout)

    details = solved(client, path.read_bytes(), "agreement-key-1")

    assert scientific_content(details["outcome"]) == scientific_content(printed)
    assert details["problem"]["plan"]["method"] == printed["plan"]["method"]
    assert details["run"]["verification_status"] == printed["verification"]["status"]
