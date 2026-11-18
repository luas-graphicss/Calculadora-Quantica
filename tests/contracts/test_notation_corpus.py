from dataclasses import dataclass

import pytest

from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.domain.diagnostics import Diagnostic, ProblemRejectedError
from quantum_calculator.notation.rendering.structure import render_structure
from support.corpus import ACCEPTED, CORPUS, ITEMS, corpus_spec, expected_of

ITEMS_BY_ID = {str(item["id"]): item for item in ITEMS}


@dataclass(frozen=True, slots=True)
class Outcome:
    classification: str
    card: str | None
    structure: str | None
    diagnostics: tuple[Diagnostic, ...]


def _items(classification_is_accepted: bool, having: str | None = None) -> list[dict[str, object]]:
    return [
        item
        for item in ITEMS
        if (expected_of(item)["classification"] == ACCEPTED) is classification_is_accepted
        and (having is None or having in item or having in expected_of(item))
    ]


def _classify(validator: StatementValidator, item: dict[str, object]) -> Outcome:
    try:
        problem = validator.validate(corpus_spec(item))
    except ProblemRejectedError as rejection:
        return Outcome(rejection.category.value, None, None, rejection.diagnostics)
    return Outcome(ACCEPTED, problem.card.identifier, render_structure(problem.statement), ())


@pytest.mark.parametrize("item", ITEMS, ids=lambda item: item["id"])
def test_corpus_item_receives_the_labelled_classification(
    statement_validator: StatementValidator, item: dict[str, object]
) -> None:
    outcome = _classify(statement_validator, item)

    assert outcome.classification == expected_of(item)["classification"]


@pytest.mark.parametrize("item", _items(True, having="structure"), ids=lambda item: item["id"])
def test_accepted_item_is_read_as_the_labelled_tree_and_card(
    statement_validator: StatementValidator, item: dict[str, object]
) -> None:
    outcome = _classify(statement_validator, item)

    assert outcome.structure == expected_of(item)["structure"]
    assert outcome.card == expected_of(item)["card"]


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
    assert outcome.structure == canonical.structure == expected_of(reference)["structure"]
    assert outcome.card == canonical.card == expected_of(item)["card"]


@pytest.mark.parametrize("item", _items(False), ids=lambda item: item["id"])
def test_refused_item_carries_the_labelled_diagnostic_at_the_labelled_place(
    statement_validator: StatementValidator, item: dict[str, object]
) -> None:
    expected = expected_of(item)

    diagnostic = _classify(statement_validator, item).diagnostics[0]

    assert diagnostic.code.value == expected["code"]
    assert diagnostic.pointer == expected["pointer"]
    assert diagnostic.expected
    if "excerpt" in expected:
        excerpt = diagnostic.excerpt
        assert excerpt is not None
        assert excerpt.text[excerpt.start : excerpt.end] == expected["excerpt"]


def test_corpus_covers_every_declared_classification() -> None:
    labelled = {expected_of(item)["classification"] for item in ITEMS}

    assert labelled == set(CORPUS["classifications"])


def test_corpus_identifiers_are_unique() -> None:
    assert len(ITEMS_BY_ID) == len(ITEMS)


def test_every_item_states_the_intended_reading_and_every_refusal_its_reason() -> None:
    assert all(item["intent"] for item in ITEMS)
    assert all(item["reason"] for item in _items(False))
