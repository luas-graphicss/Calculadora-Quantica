import json
from pathlib import Path

import pytest

from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode, ProblemRejectedError
from quantum_calculator.domain.statements import SymbolDeclaration
from quantum_calculator.interfaces.serialization.decoding.object_reader import MAX_LIST_LENGTH
from quantum_calculator.interfaces.serialization.decoding.statement_decoder import decode_statement
from support.statements import CALCULUS, DECAY, DECAY_CONDITION, DECAY_EQUATION, statement_document


def _diagnostics(raw: bytes) -> tuple[Diagnostic, ...]:
    with pytest.raises(ProblemRejectedError) as rejection:
        decode_statement(raw)
    return rejection.value.diagnostics


def _only(raw: bytes) -> Diagnostic:
    (diagnostic,) = _diagnostics(raw)
    return diagnostic


def test_reference_review_case_is_decoded_with_its_source(symbolic_cases: Path) -> None:
    raw = (symbolic_cases / "decay_candidate_correct.json").read_bytes()

    spec = decode_statement(raw)

    assert spec.notation == "text"
    assert spec.statement == "y' = -k*y"
    assert spec.card_identifier == "ode.first_order_linear.candidate_review"
    assert spec.conditions == ("y(0) = y_0",)
    assert spec.candidate == "y(t) = y_0*exp(-k*t)"
    assert spec.source.text == raw.decode("utf-8")
    assert len(spec.source.sha256) == 64
    assert spec.symbols[-1] == SymbolDeclaration("y", "function", "real", "1", "t")


def test_optional_fields_are_absent_when_not_given() -> None:
    spec = decode_statement(statement_document("diff(x^2, x)", CALCULUS))

    assert spec.card_identifier is None
    assert spec.conditions == ()
    assert spec.candidate is None
    assert spec.description is None


def test_every_missing_field_is_reported_in_one_pass() -> None:
    diagnostics = _diagnostics(json.dumps({"statement": "x"}).encode("utf-8"))

    assert {item.pointer for item in diagnostics} == {"/schema_version", "/notation", "/symbols"}
    assert {item.code for item in diagnostics} == {DiagnosticCode.MISSING_FIELD}


def test_unknown_field_is_refused_instead_of_ignored() -> None:
    diagnostic = _only(statement_document("diff(x^2, x)", CALCULUS, assume="x > 0"))

    assert diagnostic.code is DiagnosticCode.UNEXPECTED_FIELD
    assert diagnostic.pointer == "/assume"


def test_symbol_with_an_unknown_inner_field_is_refused() -> None:
    symbols = {"x": {"role": "variable", "domain": "real", "unit": "1", "value": "2"}}

    diagnostic = _only(statement_document("diff(x^2, x)", symbols))

    assert diagnostic.code is DiagnosticCode.UNEXPECTED_FIELD
    assert diagnostic.pointer == "/symbols/x/value"


def test_symbol_without_domain_or_unit_is_refused_field_by_field() -> None:
    diagnostics = _diagnostics(statement_document("diff(x^2, x)", {"x": {"role": "variable"}}))

    assert [(item.code, item.pointer) for item in diagnostics] == [
        (DiagnosticCode.MISSING_FIELD, "/symbols/x/domain"),
        (DiagnosticCode.MISSING_FIELD, "/symbols/x/unit"),
    ]


@pytest.mark.parametrize("conditions", ["y(0) = y_0", {"0": "y(0) = y_0"}, 3])
def test_conditions_that_are_not_a_list_are_refused(conditions: object) -> None:
    diagnostic = _only(statement_document(DECAY_EQUATION, DECAY, conditions=conditions))

    assert diagnostic.code is DiagnosticCode.INVALID_TYPE
    assert diagnostic.pointer == "/conditions"


def test_condition_that_is_not_a_text_is_refused_at_its_index() -> None:
    raw = statement_document(DECAY_EQUATION, DECAY, conditions=[DECAY_CONDITION, 0])

    diagnostic = _only(raw)

    assert diagnostic.code is DiagnosticCode.INVALID_TYPE
    assert diagnostic.pointer == "/conditions/1"


def test_list_of_conditions_over_the_limit_is_refused() -> None:
    conditions = [DECAY_CONDITION] * (MAX_LIST_LENGTH + 1)

    diagnostic = _only(statement_document(DECAY_EQUATION, DECAY, conditions=conditions))

    assert diagnostic.code is DiagnosticCode.INVALID_TYPE
    assert diagnostic.pointer == "/conditions"


def test_empty_statement_is_refused() -> None:
    diagnostic = _only(statement_document("", CALCULUS))

    assert diagnostic.code is DiagnosticCode.INVALID_TYPE
    assert diagnostic.pointer == "/statement"


def test_unsupported_schema_version_is_refused() -> None:
    raw = statement_document("diff(x^2, x)", CALCULUS, schema_version="2.0")

    diagnostic = _only(raw)

    assert diagnostic.code is DiagnosticCode.UNSUPPORTED_SCHEMA_VERSION
    assert diagnostic.pointer == "/schema_version"
