from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CardChoice:
    card_identifier: str
    answer: str


@dataclass(frozen=True, slots=True)
class PhysicalQuestion:
    identifier: str
    question: str
    context: str
    choices: tuple[CardChoice, ...]
