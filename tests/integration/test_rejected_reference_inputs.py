import json
from pathlib import Path

import pytest

from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem

REJECTED = Path(__file__).resolve().parents[2] / "reference_cases" / "quantum" / "rejected"
EXPECTATIONS: list[dict[str, str]] = json.loads(
    (REJECTED / "expectations.json").read_text("utf-8")
)["cases"]


def test_every_rejected_input_has_a_declared_expectation() -> None:
    declared = {case["file"] for case in EXPECTATIONS}
    present = {path.name for path in REJECTED.glob("*.json")} - {"expectations.json"}

    assert declared == present


@pytest.mark.parametrize("case", EXPECTATIONS, ids=lambda case: case["file"])
def test_rejected_input_points_to_the_field_and_the_expected_restriction(
    validator: ProblemValidator, case: dict[str, str]
) -> None:
    raw = (REJECTED / case["file"]).read_bytes()

    with pytest.raises(ProblemRejectedError) as rejection:
        validator.validate(decode_problem(raw))

    (diagnostic,) = rejection.value.diagnostics
    assert diagnostic.code.value == case["code"]
    assert diagnostic.pointer == case["pointer"]
    assert diagnostic.category.value == case["category"]
    assert case["expected_mentions"] in diagnostic.expected
    assert rejection.value.category.value == case["category"]
