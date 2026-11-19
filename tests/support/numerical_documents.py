import json
from pathlib import Path
from typing import NotRequired, TypedDict

from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.interfaces.serialization.decoding.numerical_decoder import decode_numerical
from support.documents import ProblemDocument

NUMERICAL = Path(__file__).resolve().parents[2] / "reference_cases" / "numerical"
REJECTED = NUMERICAL / "rejected"


class ExpectedAnswer(TypedDict):
    name: str
    expected: float
    absolute_tolerance: NotRequired[float]
    relative_tolerance: NotRequired[float]


class NumericalExpectation(TypedDict):
    file: str
    card: str
    oracle: str
    verification: str
    not_passed: list[str]
    answers: list[ExpectedAnswer]


EXPECTATIONS: list[NumericalExpectation] = json.loads(
    (NUMERICAL / "expectations.json").read_text("utf-8")
)["cases"]
REFUSALS: list[dict[str, str]] = json.loads((REJECTED / "expectations.json").read_text("utf-8"))[
    "cases"
]
ACCEPTED_FILES = [case["file"] for case in EXPECTATIONS]
VERIFIED_FILES = [case["file"] for case in EXPECTATIONS if case["verification"] == "passed"]


def numerical_document(name: str) -> ProblemDocument:
    return ProblemDocument.load(NUMERICAL / f"{name}.json")


def numerical_spec(document: ProblemDocument) -> NumericalSpec:
    return decode_numerical(document.encode())


def reference_spec(name: str) -> NumericalSpec:
    return numerical_spec(numerical_document(name))
