import json
from pathlib import Path

import pytest

from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.workbench.describe_catalog import (
    DescribeCatalog,
    DescribedChoice,
)
from quantum_calculator.catalog.listing import CATALOG_VERSION, catalog_entries
from quantum_calculator.composition import Calculator
from quantum_calculator.domain.workbench.documents import object_members, text_member
from quantum_calculator.domain.workbench.forms import CardForm, InputKind
from quantum_calculator.interfaces.serialization.document_calculator import DocumentCalculator

_CATALOG = DescribeCatalog(SiUnitRegistry(Codata2022Constants()), Codata2022Constants()).execute()
_CHOICES = [choice for question in _CATALOG.questions for choice in question.choices]
_NUMERICAL_CHOICES = [choice for choice in _CHOICES if choice.form.kind is InputKind.NUMERICAL]
_ALWAYS_EXPRESSIBLE = {"schema_version", "problem", "description"}


def _identifier(choice: DescribedChoice) -> str:
    return choice.card.identifier


def _expressible_fields(form: CardForm) -> set[str]:
    notation = form.notation
    present = {
        "hypotheses": bool(form.confirmations),
        "parameters": bool(form.quantities or form.counts),
        "notation": notation is not None,
        "symbols": notation is not None,
        "statement": notation is not None and notation.has_statement,
        "equations": notation is not None and notation.has_equations,
        "conditions": notation is not None and notation.has_conditions,
        "candidate": notation is not None and notation.has_candidate,
        "numerics": bool(form.settings),
        "requested": form.requested is not None,
        "uncertainty": bool(form.covariance_models),
    }
    fields = {field for field, expressible in present.items() if expressible}
    return fields | {array.section for array in form.arrays} | _ALWAYS_EXPRESSIBLE


def _example(choice: DescribedChoice, repository_root: Path) -> dict[str, object]:
    example: dict[str, object] = json.loads((repository_root / choice.card.example).read_text())
    return example


def _keys(example: dict[str, object], section: str) -> set[str]:
    content = example.get(section, {})
    assert isinstance(content, dict)
    return set(content)


def test_the_catalog_carries_the_version_of_the_homologated_cards() -> None:
    assert _CATALOG.version == CATALOG_VERSION


def test_every_homologated_card_answers_exactly_one_physical_question() -> None:
    offered = sorted(_identifier(choice) for choice in _CHOICES)

    assert offered == sorted(card.identifier for card in catalog_entries())


def test_questions_are_worded_as_questions_and_not_as_method_names() -> None:
    methods = {card.method.identifier for card in catalog_entries()}

    for described in _CATALOG.questions:
        assert described.question.question.endswith("?")
        assert not any(method in described.question.question for method in methods)


@pytest.mark.parametrize("choice", _CHOICES, ids=_identifier)
def test_the_form_of_a_card_can_express_its_reference_example(
    choice: DescribedChoice, repository_root: Path
) -> None:
    assert set(_example(choice, repository_root)) <= _expressible_fields(choice.form)


@pytest.mark.parametrize("choice", _CHOICES, ids=_identifier)
def test_the_fields_of_a_form_are_the_ones_its_reference_example_fills(
    choice: DescribedChoice, repository_root: Path
) -> None:
    example = _example(choice, repository_root)
    form = choice.form

    assert _keys(example, "hypotheses") == {item.key for item in form.confirmations}
    assert _keys(example, "parameters") == {item.name for item in form.quantities} | {
        item.name for item in form.counts
    }
    assert _keys(example, "numerics") == {item.name for item in form.settings}


@pytest.mark.parametrize("choice", _NUMERICAL_CHOICES, ids=_identifier)
def test_the_numerical_settings_of_a_form_are_the_ones_the_validator_reads(
    choice: DescribedChoice, repository_root: Path, inline_calculator: Calculator
) -> None:
    source = (repository_root / choice.card.example).read_bytes()

    interpretation = DocumentCalculator(lambda _: inline_calculator).interpret(source, 30.0)

    read = [
        (text_member(setting, "name"), text_member(setting, "label"))
        for setting in object_members(interpretation, "problem", "resolution")
    ]
    assert [(setting.name, setting.label) for setting in choice.form.settings] == read
