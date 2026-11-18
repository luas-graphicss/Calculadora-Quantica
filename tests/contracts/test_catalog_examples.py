from pathlib import Path

import pytest

from quantum_calculator.catalog.card_catalog import HOMOLOGATED_CARDS
from quantum_calculator.composition import Calculator
from quantum_calculator.domain.cards import ProblemCard
from quantum_calculator.domain.verification import VerificationStatus
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem


@pytest.mark.parametrize("card", HOMOLOGATED_CARDS, ids=lambda card: card.identifier)
def test_card_example_is_solved_by_its_homologated_method_and_verified(
    card: ProblemCard, calculator: Calculator, repository_root: Path
) -> None:
    spec = decode_problem((repository_root / card.example).read_bytes())

    record = calculator.solve_problem.execute(spec)

    assert record.problem.card is card
    assert record.plan.method == card.method
    assert record.verification.status is VerificationStatus.PASSED


def test_card_identifiers_are_unique() -> None:
    identifiers = [card.identifier for card in HOMOLOGATED_CARDS]

    assert len(identifiers) == len(set(identifiers))
