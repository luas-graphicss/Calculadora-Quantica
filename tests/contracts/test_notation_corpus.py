import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.domain.diagnostics import Diagnostic, ProblemRejectedError
from quantum_calculator.notation.rendering.structure import render_structure
from support.statements import statement_spec

CORPUS = json.loads(
    (
        Path(__file__).resolve().parents[2] / "reference_cases" / "notation" / "corpus.json"
    ).read_text("utf-8")
)
ITEMS: list[dict[str, object]] = CORPUS["items"]
ITEMS_BY_ID = {str(item["id"]): item for item in ITEMS}
ACCEPTED = "accepted"
OPTIONAL_FIELDS = ("problem", "conditions", "candidate")


@dataclass(frozen=True, slots=True)
class Outcome:
    classification: str
    card: str | None
    structure: str | None
    diagnostics: tuple[Diagnostic, ...]


def _expected(item: dict[str, object]) -> dict[str, str]:
    expected = item["expected"]
    assert isinstance(expected, dict)
    return expected


def _items(classification_is_accepted: bool, having: str | None = None) -> list[dict[str, object]]:
    return [
        item
        for item in ITEMS
        if (_expected(item)["classification"] == ACCEPTED) is classification_is_accepted
        and (having is None or having in item or having in _expected(item))
    ]


def _classify(validator: StatementValidator, item: dict[str, object]) -> Outcome:
    fields = {field: item[field] for field in OPTIONAL_FIELDS if field in item}
    spec = statement_spec(
        str(item["statement"]),
        CORPUS["symbol_sets"][item["symbols"]],
        str(item["notation"]),
        **fields,
    )
    try:
        problem = validator.validate(spec)
    except ProblemRejectedError as rejection:
        return Outcome(rejection.category.value, None, None, rejection.diagnostics)
    return Outcome(ACCEPTED, problem.card.identifier, render_structure(problem.statement), ())


@pytest.mark.parametrize("item", ITEMS, ids=lambda item: item["id"])
def test_corpus_item_receives_the_labelled_classification(
    statement_validator: StatementValidator, item: dict[str, object]
) -> None:
    outcome = _classify(statement_validator, item)

    assert outcome.classification == _expected(item)["classification"]


@pytest.mark.parametrize("item", _items(True, having="structure"), ids=lambda item: item["id"])
def test_accepted_item_is_read_as_the_labelled_tree_and_card(
    statement_validator: StatementValidator, item: dict[str, object]
) -> None:
    outcome = _classify(statement_validator, item)

    assert outcome.structure == _expected(item)["structure"]
    assert outcome.card == _expected(item)["card"]


@pytest.mark.parametrize(
    "item", _items(True, having="same_problem_as"), ids=lambda item: item["id"]
)
def test_equivalent_notation_gives_the_same_canonical_problem(
    statement_validator: StatementValidator, item: dict[str, object]
) -> None:
    reference = ITEMS_BY_ID[str(item["same_problem_as"])]

    outcome = _classify(statement_validator, item)
    canonical = _classify(statement_validator, reference)

    assert item["statement"] != reference["statement"]
    assert outcome.structure == canonical.structure == _expected(reference)["structure"]
    assert outcome.card == canonical.card == _expected(item)["card"]


@pytest.mark.parametrize("item", _items(False), ids=lambda item: item["id"])
def test_refused_item_carries_the_labelled_diagnostic_at_the_labelled_place(
    statement_validator: StatementValidator, item: dict[str, object]
) -> None:
    expected = _expected(item)

    diagnostic = _classify(statement_validator, item).diagnostics[0]

    assert diagnostic.code.value == expected["code"]
    assert diagnostic.pointer == expected["pointer"]
    assert diagnostic.expected
    if "excerpt" in expected:
        excerpt = diagnostic.excerpt
        assert excerpt is not None
        assert excerpt.text[excerpt.start : excerpt.end] == expected["excerpt"]


def test_corpus_covers_every_declared_classification() -> None:
    labelled = {_expected(item)["classification"] for item in ITEMS}

    assert labelled == set(CORPUS["classifications"])


def test_corpus_identifiers_are_unique() -> None:
    assert len(ITEMS_BY_ID) == len(ITEMS)


def test_every_item_states_the_intended_reading_and_every_refusal_its_reason() -> None:
    assert all(item["intent"] for item in ITEMS)
    assert all(item["reason"] for item in _items(False))
