from quantum_calculator.catalog.calculus import ANTIDERIVATIVE, DEFINITE_INTEGRAL, DERIVATIVE
from quantum_calculator.catalog.first_order_linear_ode import (
    CANDIDATE_REVIEW,
    GENERAL_SOLUTION,
    INITIAL_VALUE,
)
from quantum_calculator.domain.statement_cards import StatementCard, StatementShape

HOMOLOGATED_STATEMENT_CARDS = (
    DERIVATIVE,
    ANTIDERIVATIVE,
    DEFINITE_INTEGRAL,
    GENERAL_SOLUTION,
    INITIAL_VALUE,
    CANDIDATE_REVIEW,
)


class StatementCatalog:
    def __init__(self, cards: tuple[StatementCard, ...]) -> None:
        self._cards = {card.identifier: card for card in cards}

    @property
    def identifiers(self) -> tuple[str, ...]:
        return tuple(self._cards)

    def find(self, identifier: str) -> StatementCard | None:
        return self._cards.get(identifier)

    def with_shape(self, shape: StatementShape) -> tuple[StatementCard, ...]:
        return tuple(card for card in self._cards.values() if card.shape is shape)
