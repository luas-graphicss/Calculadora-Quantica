import json
from fractions import Fraction

import pytest

from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.domain.problem_spec import ProblemSpec
from quantum_calculator.domain.statements import StatementSpec
from quantum_calculator.interfaces.serialization.decoding.input_decoder import decode_input
from quantum_calculator.interfaces.serialization.decoding.numerical_decoder import decode_numerical
from support.documents import ProblemDocument
from support.numerical_documents import numerical_document, numerical_spec
from support.statements import CALCULUS, statement_document

SPIN = "spin_half_measurement"
NUMERICAL_CARDS = frozenset({"quantum.infinite_square_well.discrete_spectrum"})


def _refusals(document: ProblemDocument) -> list[tuple[str, str]]:
    with pytest.raises(ProblemRejectedError) as rejection:
        decode_numerical(document.encode())
    return [(item.code.value, item.pointer) for item in rejection.value.diagnostics]


def test_reference_document_is_decoded_with_exact_numbers_and_its_source() -> None:
    document = numerical_document("electron_box_1nm_discrete")

    spec = numerical_spec(document)

    assert spec.card_identifier == "quantum.infinite_square_well.discrete_spectrum"
    assert spec.numerics is not None
    assert [(item.name, item.number.value) for item in spec.numerics] == [
        ("subintervals", Fraction(512)),
        ("levels", Fraction(3)),
    ]
    assert spec.requested is not None
    assert spec.requested.unit == "eV"
    assert spec.source.text == document.encode().decode("utf-8")
    assert spec.state is None
    assert spec.equations is None


def test_amplitude_is_a_real_number_or_a_real_and_imaginary_pair() -> None:
    document = numerical_document(SPIN).with_value(
        "/state/components", ["1/3", {"real": "0.5", "imaginary": -2}]
    )

    spec = numerical_spec(document)

    assert spec.state is not None
    real, pair = spec.state.components
    assert (real.real.value, real.imaginary) == (Fraction(1, 3), None)
    assert pair.imaginary is not None
    assert (pair.real.value, pair.imaginary.value) == (Fraction(1, 2), Fraction(-2))


def test_normalization_is_never_assumed_when_the_flag_is_absent() -> None:
    spec = numerical_spec(numerical_document(SPIN).without("/state/normalize"))

    assert spec.state is not None
    assert not spec.state.normalize


@pytest.mark.parametrize(
    ("pointer", "value", "code", "reported_at"),
    [
        ("/state/components", 1, "invalid_type", "/state/components"),
        ("/state/components", [], "invalid_type", "/state/components"),
        ("/state/components", [1] * 17, "invalid_type", "/state/components"),
        ("/state/components", [{"real": 1}], "missing_field", "/state/components/0/imaginary"),
        (
            "/state/components",
            [{"real": 1, "imaginary": 0, "phase": 0}],
            "unexpected_field",
            "/state/components/0/phase",
        ),
        ("/state/components", ["one"], "malformed_number", "/state/components/0"),
        ("/state/normalize", "yes", "invalid_type", "/state/normalize"),
        ("/observable/matrix", [[1, 0], 2], "invalid_type", "/observable/matrix/1"),
        ("/observable/unit", "", "invalid_type", "/observable/unit"),
        ("/basis", [[1, 0], "second"], "invalid_type", "/basis/1"),
        ("/numerics/tolerance", "tight", "malformed_number", "/numerics/tolerance"),
        ("/numerics", [1e-12], "invalid_type", "/numerics"),
        ("/hypotheses/state", 1, "invalid_type", "/hypotheses/state"),
        ("/schema_version", "2.0", "unsupported_schema_version", "/schema_version"),
        ("/uncertainty", {}, "unexpected_field", "/uncertainty"),
        ("/equations", [], "invalid_type", "/equations"),
        ("/requested/digits", 3, "unexpected_field", "/requested/digits"),
    ],
)
def test_structural_defect_is_refused_at_the_defective_field(
    pointer: str, value: object, code: str, reported_at: str
) -> None:
    document = numerical_document(SPIN).with_value(pointer, value)

    assert _refusals(document) == [(code, reported_at)]


def test_document_with_numerics_is_read_as_a_numerical_problem() -> None:
    raw = numerical_document(SPIN).encode()

    assert isinstance(decode_input(raw, NUMERICAL_CARDS), NumericalSpec)


def test_numerical_card_without_numerics_is_still_read_as_a_numerical_problem() -> None:
    raw = numerical_document("electron_box_1nm_discrete").without("/numerics").encode()

    spec = decode_input(raw, NUMERICAL_CARDS)

    assert isinstance(spec, NumericalSpec)
    assert spec.numerics is None


def test_statement_and_card_documents_keep_their_own_readers() -> None:
    card = json.dumps(
        {
            "schema_version": "1.0",
            "problem": "quantum.infinite_square_well.energy_level",
            "hypotheses": {},
            "parameters": {},
            "requested": {"quantity": "energy", "unit": "eV"},
        }
    ).encode("utf-8")

    assert isinstance(
        decode_input(statement_document("diff(x^2, x)", CALCULUS), NUMERICAL_CARDS), StatementSpec
    )
    assert isinstance(decode_input(card, NUMERICAL_CARDS), ProblemSpec)
