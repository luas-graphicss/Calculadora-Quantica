import json
from pathlib import Path
from typing import Any

import pytest

from quantum_calculator.application.workbench.canonical_documents import (
    canonical_json,
    canonical_problem,
)
from quantum_calculator.composition import Calculator
from quantum_calculator.domain.execution import NeverCancelled
from quantum_calculator.interfaces.serialization.document_calculator import DocumentCalculator
from support.cli import CliRunner

_EXACT_CASES = [
    "quantum/electron_box_1nm.json",
    "quantum/electron_box_1nm_uncertainty.json",
    "symbolic/decay_initial_value.json",
    "symbolic/decay_candidate_wrong_initial_value.json",
]
_NUMERICAL_CASES = ["numerical/sine_quadrature.json", "numerical/electron_box_1nm_discrete.json"]
_REFUSED_CASES = [
    "quantum/rejected/width_in_seconds.json",
    "numerical/rejected/non_hermitian_operator.json",
]
_TIME_LIMIT = 30.0


@pytest.fixture
def documents(calculator: Calculator) -> DocumentCalculator:
    return DocumentCalculator(lambda _wall_seconds: calculator)


def _case(repository_root: Path, name: str) -> Path:
    return repository_root / "reference_cases" / name


@pytest.mark.parametrize("name", _EXACT_CASES + _NUMERICAL_CASES)
def test_the_api_documents_and_the_cli_give_the_same_canonical_problem_and_method(
    documents: DocumentCalculator, run_cli: CliRunner, repository_root: Path, name: str
) -> None:
    case = _case(repository_root, name)

    interpretation = documents.interpret(case.read_bytes(), _TIME_LIMIT)

    printed = json.loads(run_cli("validate", case, "--format", "json").stdout)
    assert interpretation == printed
    assert canonical_json(canonical_problem(interpretation)) == canonical_json(
        canonical_problem(printed)
    )
    assert interpretation["plan"] == printed["plan"]


@pytest.mark.parametrize("name", _EXACT_CASES)
def test_an_exact_calculation_gives_the_record_the_cli_prints(
    documents: DocumentCalculator, run_cli: CliRunner, repository_root: Path, name: str
) -> None:
    case = _case(repository_root, name)

    record = documents.calculate(case.read_bytes(), _TIME_LIMIT, NeverCancelled())

    assert record == json.loads(run_cli("solve", case, "--format", "json").stdout)


@pytest.mark.numerical
@pytest.mark.parametrize("name", _NUMERICAL_CASES)
def test_a_numerical_calculation_agrees_with_the_cli_within_rounding(
    documents: DocumentCalculator, run_cli: CliRunner, repository_root: Path, name: str
) -> None:
    case = _case(repository_root, name)

    record: Any = documents.calculate(case.read_bytes(), _TIME_LIMIT, NeverCancelled())

    printed = json.loads(run_cli("solve", case, "--format", "json").stdout)
    assert record["problem"] == printed["problem"]
    assert record["plan"] == printed["plan"]
    assert [check["status"] for check in record["verification"]["checks"]] == [
        check["status"] for check in printed["verification"]["checks"]
    ]
    for answer, expected in zip(
        record["result"]["answers"], printed["result"]["answers"], strict=True
    ):
        assert answer["value"] == pytest.approx(expected["value"], rel=1e-12, abs=1e-300)
        assert answer["unit"] == expected["unit"]


@pytest.mark.parametrize("name", _REFUSED_CASES)
def test_a_refused_input_gives_the_rejection_the_cli_prints(
    documents: DocumentCalculator, run_cli: CliRunner, repository_root: Path, name: str
) -> None:
    case = _case(repository_root, name)
    printed = json.loads(run_cli("solve", case, "--format", "json").stderr)

    assert documents.interpret(case.read_bytes(), _TIME_LIMIT) == printed
    assert documents.calculate(case.read_bytes(), _TIME_LIMIT, NeverCancelled()) == printed
