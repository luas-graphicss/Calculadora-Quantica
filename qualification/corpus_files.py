import json
from pathlib import Path
from typing import NotRequired, TypedDict


class ClosedFormOracle(TypedDict):
    case: str
    quantity: str
    nominal_value: str
    absolute_tolerance: str
    derivation: str
    expression: NotRequired[str]
    tolerance_rationale: NotRequired[str]
    uncertainty_rationale: NotRequired[str]
    standard_uncertainty: NotRequired[str]
    relative_standard_uncertainty: NotRequired[str]


class SymbolicCase(TypedDict):
    file: str
    answer: str
    derivation: str
    verification: str
    failed_checks: list[str]


class SymbolicExpectations(TypedDict):
    cases: list[SymbolicCase]


class NumericalAnswer(TypedDict):
    name: str
    expected: float
    absolute_tolerance: NotRequired[float]
    relative_tolerance: NotRequired[float]


class NumericalCase(TypedDict):
    file: str
    oracle: str
    verification: str
    not_passed: list[str]
    answers: list[NumericalAnswer]


class NumericalExpectations(TypedDict):
    cases: list[NumericalCase]


class RefusedCase(TypedDict):
    file: str
    category: str
    code: str
    pointer: str
    reason: NotRequired[str]
    defect: NotRequired[str]


class RefusedExpectations(TypedDict):
    cases: list[RefusedCase]


class NotationExpectation(TypedDict):
    classification: str
    card: NotRequired[str]
    structure: NotRequired[str]
    code: NotRequired[str]
    pointer: NotRequired[str]


class NotationItem(TypedDict):
    id: str
    notation: str
    statement: str
    symbols: str
    intent: str
    expected: NotationExpectation
    same_problem_as: NotRequired[str]
    reason: NotRequired[str]
    problem: NotRequired[str]
    conditions: NotRequired[list[str]]
    candidate: NotRequired[str]


class NotationCorpus(TypedDict):
    symbol_sets: dict[str, dict[str, dict[str, str]]]
    items: list[NotationItem]


def read_closed_form_oracle(path: Path) -> ClosedFormOracle:
    oracle: ClosedFormOracle = json.loads(path.read_text("utf-8"))
    return oracle


def read_symbolic_expectations(path: Path) -> SymbolicExpectations:
    expectations: SymbolicExpectations = json.loads(path.read_text("utf-8"))
    return expectations


def read_numerical_expectations(path: Path) -> NumericalExpectations:
    expectations: NumericalExpectations = json.loads(path.read_text("utf-8"))
    return expectations


def read_refused_expectations(path: Path) -> RefusedExpectations:
    expectations: RefusedExpectations = json.loads(path.read_text("utf-8"))
    return expectations


def read_notation_corpus(path: Path) -> NotationCorpus:
    corpus: NotationCorpus = json.loads(path.read_text("utf-8"))
    return corpus
