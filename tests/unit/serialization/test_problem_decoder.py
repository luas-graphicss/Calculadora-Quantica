import json
from fractions import Fraction
from pathlib import Path

import pytest

from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode, ProblemRejectedError
from quantum_calculator.domain.problem_spec import ConstantInput, ExactNumber, QuantityInput
from quantum_calculator.interfaces.serialization.decoding.json_document import MAX_DOCUMENT_BYTES
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem


@pytest.fixture
def reference_document(reference_cases: Path) -> dict[str, object]:
    document = json.loads((reference_cases / "electron_box_1nm.json").read_text("utf-8"))
    assert isinstance(document, dict)
    return document


def _encode(document: object) -> bytes:
    return json.dumps(document).encode("utf-8")


def _diagnostics(raw: bytes) -> tuple[Diagnostic, ...]:
    with pytest.raises(ProblemRejectedError) as rejection:
        decode_problem(raw)
    return rejection.value.diagnostics


def _only(raw: bytes) -> Diagnostic:
    (diagnostic,) = _diagnostics(raw)
    return diagnostic


def test_reference_case_is_decoded_without_losing_exactness(reference_cases: Path) -> None:
    raw = (reference_cases / "electron_box_1nm.json").read_bytes()

    spec = decode_problem(raw)

    parameters = {parameter.name: parameter.content for parameter in spec.parameters}
    assert spec.card_identifier == "quantum.infinite_square_well.energy_level"
    assert spec.source.text == raw.decode("utf-8")
    assert len(spec.source.sha256) == 64
    assert parameters["mass"] == ConstantInput("electron_mass")
    assert parameters["width"] == QuantityInput(ExactNumber(Fraction(1), "1"), "nm")
    assert parameters["level"] == ExactNumber(Fraction(1), "1")
    assert spec.requested.significant_digits == ExactNumber(Fraction(10), "10")
    assert spec.uncertainty is None


def test_decimal_json_numbers_are_read_as_exact_fractions(
    reference_document: dict[str, object],
) -> None:
    raw = _encode(reference_document).replace(b'"value": 1', b'"value": 0.1')

    spec = decode_problem(raw)

    width = next(parameter.content for parameter in spec.parameters if parameter.name == "width")
    assert width == QuantityInput(ExactNumber(Fraction(1, 10), "0.1"), "nm")


def test_declared_uncertainties_are_decoded(reference_cases: Path) -> None:
    spec = decode_problem((reference_cases / "electron_box_1nm_uncertainty.json").read_bytes())

    assert spec.uncertainty is not None
    assert spec.uncertainty.covariance == "independent"
    assert [entry.parameter for entry in spec.uncertainty.standard_uncertainties] == [
        "mass",
        "width",
    ]


@pytest.mark.parametrize("token", [b"NaN", b"Infinity", b"-Infinity"])
def test_non_finite_json_tokens_are_refused_at_their_field(
    reference_document: dict[str, object], token: bytes
) -> None:
    raw = _encode(reference_document).replace(b'"value": 1', b'"value": ' + token)

    diagnostic = _only(raw)

    assert diagnostic.code is DiagnosticCode.NON_FINITE_NUMBER
    assert diagnostic.pointer == "/parameters/width/value"


def test_duplicate_fields_are_refused(reference_document: dict[str, object]) -> None:
    raw = _encode(reference_document).replace(b'"level": 1', b'"level": 1, "level": 2')

    assert _only(raw).code is DiagnosticCode.DUPLICATE_FIELD


def test_unknown_field_is_refused_instead_of_ignored(
    reference_document: dict[str, object],
) -> None:
    reference_document["effective_mass"] = 0.067

    diagnostic = _only(_encode(reference_document))

    assert diagnostic.code is DiagnosticCode.UNEXPECTED_FIELD
    assert diagnostic.pointer == "/effective_mass"
    assert "parameters" in diagnostic.expected


def test_every_missing_field_is_reported_in_one_pass() -> None:
    diagnostics = _diagnostics(_encode({"schema_version": "1.0"}))

    assert {item.pointer for item in diagnostics} == {
        "/problem",
        "/hypotheses",
        "/parameters",
        "/requested",
    }
    assert {item.code for item in diagnostics} == {DiagnosticCode.MISSING_FIELD}


def test_unsupported_schema_version_is_refused(reference_document: dict[str, object]) -> None:
    reference_document["schema_version"] = "2.0"

    diagnostic = _only(_encode(reference_document))

    assert diagnostic.code is DiagnosticCode.UNSUPPORTED_SCHEMA_VERSION
    assert diagnostic.pointer == "/schema_version"


def test_parameter_with_the_wrong_json_type_is_refused(
    reference_document: dict[str, object],
) -> None:
    reference_document["parameters"] = {"mass": True, "width": [1, "nm"], "level": 1}

    diagnostics = _diagnostics(_encode(reference_document))

    assert [(item.code, item.pointer) for item in diagnostics] == [
        (DiagnosticCode.INVALID_TYPE, "/parameters/mass"),
        (DiagnosticCode.INVALID_TYPE, "/parameters/width"),
    ]


def test_quantity_with_an_unknown_inner_field_is_refused(
    reference_document: dict[str, object],
) -> None:
    reference_document["parameters"] = {
        "mass": {"constant": "electron_mass"},
        "width": {"value": 1, "unit": "nm", "uncertainty": 0.1},
        "level": 1,
    }

    diagnostic = _only(_encode(reference_document))

    assert diagnostic.code is DiagnosticCode.UNEXPECTED_FIELD
    assert diagnostic.pointer == "/parameters/width/uncertainty"


def test_malformed_json_reports_line_and_column() -> None:
    diagnostic = _only(b'{\n  "schema_version": "1.0",\n  "problem": \n}')

    assert diagnostic.code is DiagnosticCode.MALFORMED_JSON
    assert "linha 4" in diagnostic.message


def test_document_that_is_not_an_object_is_refused() -> None:
    assert _only(b"[1, 2, 3]").code is DiagnosticCode.INVALID_TYPE


def test_document_over_the_size_limit_is_refused_before_parsing() -> None:
    raw = b" " * (MAX_DOCUMENT_BYTES + 1)

    assert _only(raw).code is DiagnosticCode.DOCUMENT_TOO_LARGE


def test_document_that_is_not_utf8_is_refused() -> None:
    assert _only(b'{"problem": "\xff"}').code is DiagnosticCode.INVALID_ENCODING


def test_deeply_nested_document_is_refused_without_crashing() -> None:
    raw = b"[" * 30_000 + b"]" * 30_000

    assert _only(raw).code is DiagnosticCode.DOCUMENT_TOO_DEEP
