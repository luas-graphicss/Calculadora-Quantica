from quantum_calculator.catalog.numerical.discrete_schrodinger import (
    OSCILLATOR_TRUNCATED_SPECTRUM,
    WELL_DISCRETE_SPECTRUM,
    WELL_TIME_EVOLUTION,
)
from quantum_calculator.catalog.numerical.finite_basis import PROJECTIVE_MEASUREMENT
from quantum_calculator.catalog.numerical.initial_value import EXPLICIT_RUNGE_KUTTA
from quantum_calculator.catalog.numerical.quadrature import ADAPTIVE_QUADRATURE
from quantum_calculator.domain.numerical.cards import NumericalCard

HOMOLOGATED_NUMERICAL_CARDS = (
    ADAPTIVE_QUADRATURE,
    EXPLICIT_RUNGE_KUTTA,
    PROJECTIVE_MEASUREMENT,
    WELL_DISCRETE_SPECTRUM,
    OSCILLATOR_TRUNCATED_SPECTRUM,
    WELL_TIME_EVOLUTION,
)


class NumericalCatalog:
    def __init__(self, cards: tuple[NumericalCard, ...]) -> None:
        self._cards = {card.identifier: card for card in cards}

    @property
    def identifiers(self) -> tuple[str, ...]:
        return tuple(self._cards)

    def find(self, identifier: str) -> NumericalCard | None:
        return self._cards.get(identifier)
