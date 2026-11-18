import re
from pathlib import Path

import pytest

from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.catalog.card_catalog import HOMOLOGATED_CARDS
from quantum_calculator.catalog.listing import CATALOG_VERSION, catalog_entries
from quantum_calculator.catalog.statement_catalog import HOMOLOGATED_STATEMENT_CARDS
from quantum_calculator.composition import Calculator
from quantum_calculator.domain.cards import CatalogEntry, ProblemCard
from quantum_calculator.domain.statement_cards import StatementCard
from quantum_calculator.domain.statements import CardSelection
from quantum_calculator.domain.verification import VerificationStatus
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem
from quantum_calculator.interfaces.serialization.decoding.statement_decoder import decode_statement

SEMANTIC_VERSION = r"\d+\.\d+\.\d+"


@pytest.mark.parametrize("card", HOMOLOGATED_CARDS, ids=lambda card: card.identifier)
def test_card_example_is_solved_by_its_homologated_method_and_verified(
    card: ProblemCard, calculator: Calculator, repository_root: Path
) -> None:
    spec = decode_problem((repository_root / card.example).read_bytes())

    record = calculator.solve_problem.execute(spec)

    assert record.problem.card is card
    assert record.plan.method == card.method
    assert record.verification.status is VerificationStatus.PASSED


@pytest.mark.parametrize("card", HOMOLOGATED_STATEMENT_CARDS, ids=lambda card: card.identifier)
def test_statement_card_example_is_validated_against_the_card_it_names(
    card: StatementCard, statement_validator: StatementValidator, repository_root: Path
) -> None:
    spec = decode_statement((repository_root / card.example).read_bytes())

    problem = statement_validator.validate(spec)

    assert problem.card is card
    assert problem.selection is CardSelection.CONFIRMED


def test_card_identifiers_are_unique_across_the_catalog() -> None:
    identifiers = [entry.identifier for entry in catalog_entries()]

    assert len(identifiers) == len(set(identifiers))
    assert len(identifiers) == len(HOMOLOGATED_CARDS) + len(HOMOLOGATED_STATEMENT_CARDS)


@pytest.mark.parametrize("entry", catalog_entries(), ids=lambda entry: entry.identifier)
def test_every_card_is_versioned_by_area_problem_type_domain_and_method(
    entry: CatalogEntry, repository_root: Path
) -> None:
    assert re.fullmatch(SEMANTIC_VERSION, entry.version)
    assert entry.identifier.split(".")[-1] == entry.problem_type or entry.problem_type
    assert entry.area
    assert entry.domain
    assert all(entry.domain)
    assert entry.method.identifier
    assert entry.method.justification
    assert entry.limitations
    assert (repository_root / entry.example).is_file()


def test_catalog_itself_carries_a_semantic_version() -> None:
    assert re.fullmatch(SEMANTIC_VERSION, CATALOG_VERSION)


def test_statement_cards_sharing_a_shape_differ_in_the_fields_they_require() -> None:
    signatures = [(card.shape, card.required_fields) for card in HOMOLOGATED_STATEMENT_CARDS]

    assert len(signatures) == len(set(signatures))
