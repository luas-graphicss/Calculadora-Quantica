from quantum_calculator.catalog.infinite_square_well import INFINITE_SQUARE_WELL_ENERGY_LEVEL
from quantum_calculator.domain.cards import ProblemCard

HOMOLOGATED_CARDS = (INFINITE_SQUARE_WELL_ENERGY_LEVEL,)


class CardCatalog:
    def __init__(self, cards: tuple[ProblemCard, ...]) -> None:
        self._cards = {card.identifier: card for card in cards}

    @property
    def identifiers(self) -> tuple[str, ...]:
        return tuple(self._cards)

    def find(self, identifier: str) -> ProblemCard | None:
        return self._cards.get(identifier)
