import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from quantum_calculator.domain.constants import ConstantExactness
from quantum_calculator.domain.diagnostics import DiagnosticCategory, DiagnosticCode
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.numerical.cards import NumericalFamily
from quantum_calculator.domain.statements import (
    CardSelection,
    Notation,
    SymbolDomain,
    SymbolRole,
)
from quantum_calculator.domain.symbolic_solution import ConditionRelation, ConditionScope
from quantum_calculator.domain.verification import EvidenceKind, VerificationStatus
from quantum_calculator.interfaces.serialization.encoding.common_sections import (
    OUTPUT_SCHEMA_VERSION,
)
from quantum_calculator.interfaces.serialization.schema_files import SCHEMA_NAMES, read_schema
from support.cli import CliRunner
from support.numerical_documents import ACCEPTED_FILES, REFUSALS

ACCEPTED_CASES = ["electron_box_1nm.json", "electron_box_1nm_uncertainty.json"]
STRUCTURALLY_DEFECTIVE_CASES = ["non_finite_width.json", "undeclared_covariance.json"]
STATEMENT_CASES = [
    "product_rule.json",
    "reciprocal_primitive.json",
    "parabola_area.json",
    "decay_general_solution.json",
    "decay_initial_value.json",
    "decay_candidate_correct.json",
    "decay_candidate_wrong_initial_value.json",
    "decay_candidate_wrong_sign.json",
]


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


@pytest.mark.parametrize("case", STATEMENT_CASES)
def test_statement_reference_input_conforms_to_the_statement_schema(
    symbolic_cases: Path, case: str
) -> None:
    document = json.loads((symbolic_cases / case).read_text("utf-8"))

    assert _violations("statement", document) == []


@pytest.mark.parametrize(
    "defect",
    [
        {"notation": "mathml"},
        {"statement": ""},
        {"symbols": {"x": {"role": "variable", "domain": "real"}}},
        {"conditions": "y(0) = y_0"},
        {"assume": "x > 0"},
    ],
)
def test_statement_the_decoder_refuses_for_its_form_also_fails_the_statement_schema(
    symbolic_cases: Path, defect: dict[str, object]
) -> None:
    document = json.loads((symbolic_cases / "decay_initial_value.json").read_text("utf-8"))

    assert _violations("statement", {**document, **defect}) != []


@pytest.mark.parametrize("case", ACCEPTED_FILES)
def test_numerical_reference_input_conforms_to_the_numerical_schema(
    numerical_cases: Path, case: str
) -> None:
    document = json.loads((numerical_cases / case).read_text("utf-8"))

    assert _violations("numerical", document) == []


@pytest.mark.parametrize(
    "defect",
    [
        {"numerics": "fine"},
        {"notation": "mathml"},
        {"statement": ""},
        {"symbols": {"x": {"role": "variable", "domain": "real"}}},
        {"state": {"components": []}},
        {"basis": [[1, {"real": 1}]]},
        {"equations": []},
        {"tolerance": "1e-12"},
    ],
)
def test_numerical_input_the_decoder_refuses_for_its_form_also_fails_the_numerical_schema(
    numerical_cases: Path, defect: dict[str, object]
) -> None:
    document = json.loads((numerical_cases / "sine_quadrature.json").read_text("utf-8"))

    assert _violations("numerical", {**document, **defect}) != []


@pytest.mark.parametrize("command", ["validate", "solve"])
@pytest.mark.parametrize("case", ACCEPTED_FILES)
def test_numerical_json_output_conforms_to_the_output_schema(
    run_cli: CliRunner, numerical_cases: Path, command: str, case: str
) -> None:
    result = run_cli(command, numerical_cases / case, "--format", "json")

    assert _violations("output", json.loads(result.stdout)) == []


@pytest.mark.parametrize("case", REFUSALS, ids=lambda case: case["file"])
def test_every_numerical_refusal_document_conforms_to_the_output_schema(
    run_cli: CliRunner, numerical_cases: Path, case: dict[str, str]
) -> None:
    result = run_cli("solve", numerical_cases / "rejected" / case["file"], "--format", "json")

    assert result.stdout == ""
    assert _violations("output", json.loads(result.stderr)) == []


@pytest.mark.parametrize("command", ["validate", "solve"])
@pytest.mark.parametrize("case", ACCEPTED_CASES)
def test_json_output_conforms_to_the_output_schema(
    run_cli: CliRunner, reference_cases: Path, command: str, case: str
) -> None:
    result = run_cli(command, reference_cases / case, "--format", "json")

    assert _violations("output", json.loads(result.stdout)) == []


@pytest.mark.parametrize("command", ["validate", "solve"])
@pytest.mark.parametrize("case", STATEMENT_CASES)
def test_statement_json_output_conforms_to_the_output_schema(
    run_cli: CliRunner, symbolic_cases: Path, command: str, case: str
) -> None:
    result = run_cli(command, symbolic_cases / case, "--format", "json")

    assert _violations("output", json.loads(result.stdout)) == []


def test_catalog_document_conforms_to_the_output_schema(run_cli: CliRunner) -> None:
    result = run_cli("catalog", "--format", "json")

    assert _violations("output", json.loads(result.stdout)) == []


def test_every_statement_refusal_document_conforms_to_the_output_schema(
    run_cli: CliRunner, symbolic_cases: Path
) -> None:
    refused = sorted((symbolic_cases / "rejected").glob("*.json"))
    cases = [path for path in refused if path.name != "expectations.json"]

    violations = [
        _violations("output", json.loads(run_cli("validate", path, "--format", "json").stderr))
        for path in cases
        if run_cli("validate", path).exit_code != 0
    ]

    assert violations
    assert all(found == [] for found in violations)


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


def test_numerical_schema_enumerations_follow_the_domain_vocabulary() -> None:
    definitions = json.loads(read_schema("output"))["$defs"]
    card = definitions["numerical_problem"]["properties"]["card"]["properties"]
    symbol = json.loads(read_schema("numerical"))["$defs"]["symbol"]["properties"]

    assert card["family"]["enum"] == [family.value for family in NumericalFamily]
    assert definitions["numerical_result"]["properties"]["nature"]["enum"] == [
        nature.value for nature in ResultNature
    ]
    assert symbol["role"]["enum"] == [role.value for role in SymbolRole]
    assert symbol["domain"]["enum"] == [domain.value for domain in SymbolDomain]


def test_statement_schema_enumerations_follow_the_domain_vocabulary() -> None:
    definitions = json.loads(read_schema("output"))["$defs"]
    symbol = definitions["statement_symbol"]["properties"]
    problem = definitions["statement_problem"]["properties"]
    condition = definitions["domain_condition"]["properties"]

    assert symbol["role"]["enum"] == [role.value for role in SymbolRole]
    assert symbol["domain"]["enum"] == [domain.value for domain in SymbolDomain]
    assert problem["notation"]["enum"] == [notation.value for notation in Notation]
    assert problem["card"]["properties"]["selection"]["enum"] == [
        selection.value for selection in CardSelection
    ]
    assert condition["relation"]["enum"] == [relation.value for relation in ConditionRelation]
    assert condition["scope"]["enum"] == [scope.value for scope in ConditionScope]


@pytest.mark.parametrize(
    "document",
    [
        "validation",
        "run_record",
        "statement_validation",
        "statement_run_record",
        "numerical_validation",
        "numerical_run_record",
        "catalog",
        "rejection",
    ],
)
def test_every_output_document_declares_the_current_schema_version(document: str) -> None:
    schema = json.loads(read_schema("output"))
    declared = schema["$defs"][document]["properties"]["schema_version"]

    assert declared == {"const": OUTPUT_SCHEMA_VERSION}
    assert schema["$id"].endswith(f":{OUTPUT_SCHEMA_VERSION}")
    assert {"$ref": f"#/$defs/{document}"} in schema["oneOf"]
