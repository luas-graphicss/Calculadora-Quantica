import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from quantum_calculator.domain.constants import ConstantExactness
from quantum_calculator.domain.diagnostics import DiagnosticCategory, DiagnosticCode
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.verification import EvidenceKind, VerificationStatus
from quantum_calculator.interfaces.serialization.schema_files import SCHEMA_NAMES, read_schema
from support.cli import CliRunner

ACCEPTED_CASES = ["electron_box_1nm.json", "electron_box_1nm_uncertainty.json"]
STRUCTURALLY_DEFECTIVE_CASES = ["non_finite_width.json", "undeclared_covariance.json"]


def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(json.loads(read_schema(name)))


def _violations(name: str, document: object) -> list[str]:
    return [
        f"{'/'.join(str(part) for part in error.absolute_path)}: {error.message}"
        for error in _validator(name).iter_errors(document)
    ]


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_packaged_schema_is_a_valid_draft_2020_12_schema(name: str) -> None:
    Draft202012Validator.check_schema(json.loads(read_schema(name)))


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_command_prints_the_packaged_schema(run_cli: CliRunner, name: str) -> None:
    result = run_cli("schema", name)

    assert result.exit_code == 0
    assert result.stdout == read_schema(name)


@pytest.mark.parametrize("case", ACCEPTED_CASES)
def test_accepted_reference_input_conforms_to_the_problem_schema(
    reference_cases: Path, case: str
) -> None:
    document = json.loads((reference_cases / case).read_text("utf-8"))

    assert _violations("problem", document) == []


@pytest.mark.parametrize("case", STRUCTURALLY_DEFECTIVE_CASES)
def test_input_the_decoder_refuses_for_its_form_also_fails_the_problem_schema(
    reference_cases: Path, case: str
) -> None:
    document = json.loads((reference_cases / "rejected" / case).read_text("utf-8"))

    assert _violations("problem", document) != []


@pytest.mark.parametrize("command", ["validate", "solve"])
@pytest.mark.parametrize("case", ACCEPTED_CASES)
def test_json_output_conforms_to_the_output_schema(
    run_cli: CliRunner, reference_cases: Path, command: str, case: str
) -> None:
    result = run_cli(command, reference_cases / case, "--format", "json")

    assert _violations("output", json.loads(result.stdout)) == []


def test_every_rejection_document_conforms_to_the_output_schema(
    run_cli: CliRunner, reference_cases: Path
) -> None:
    rejected = sorted((reference_cases / "rejected").glob("*.json"))
    cases = [path for path in rejected if path.name != "expectations.json"]

    violations = [
        _violations("output", json.loads(run_cli("solve", path, "--format", "json").stderr))
        for path in cases
    ]

    assert cases
    assert all(found == [] for found in violations)


def test_output_schema_enumerations_follow_the_domain_vocabulary() -> None:
    definitions = json.loads(read_schema("output"))["$defs"]
    diagnostic = definitions["diagnostic"]["properties"]
    check = definitions["verification"]["properties"]["checks"]["items"]["properties"]

    assert diagnostic["code"]["enum"] == [code.value for code in DiagnosticCode]
    assert diagnostic["category"]["enum"] == [category.value for category in DiagnosticCategory]
    assert check["status"]["enum"] == [status.value for status in VerificationStatus]
    assert check["kind"]["enum"] == [kind.value for kind in EvidenceKind]
    assert definitions["plan"]["properties"]["nature"]["enum"] == [
        nature.value for nature in ResultNature
    ]
    assert definitions["constant"]["properties"]["exactness"]["enum"] == [
        exactness.value for exactness in ConstantExactness
    ]
