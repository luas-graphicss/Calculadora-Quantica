from dataclasses import dataclass, replace

from quantum_calculator.application.validation.unit_resolution import describe_dimension
from quantum_calculator.catalog.listing import CATALOG_VERSION, catalog_entries
from quantum_calculator.catalog.numerical.forms import (
    ARRAY_FIELDS,
    DISPLAY_DIMENSIONS,
    NUMERICAL_SETTINGS,
)
from quantum_calculator.catalog.questions import PHYSICAL_QUESTIONS
from quantum_calculator.domain.cards import (
    CatalogEntry,
    HypothesisRule,
    PositiveQuantityRule,
    ProblemCard,
)
from quantum_calculator.domain.numerical.cards import InputSection, NumericalCard
from quantum_calculator.domain.ports import ConstantsEdition, UnitRegistry, require_constant
from quantum_calculator.domain.statement_cards import StatementCard, StatementField
from quantum_calculator.domain.workbench.forms import (
    ArrayField,
    CardForm,
    Confirmation,
    ConstantChoice,
    CountField,
    InputKind,
    NotationFields,
    Presence,
    QuantityField,
    RequestedFields,
)
from quantum_calculator.domain.workbench.questions import PhysicalQuestion

_DISPLAY_LABEL = "unidade de exibição das respostas"
_DIGITS_LABEL = "algarismos significativos das respostas"
_NOTATION_SECTIONS = (
    InputSection.NOTATION,
    InputSection.SYMBOLS,
    InputSection.STATEMENT,
    InputSection.EQUATIONS,
    InputSection.CONDITIONS,
)


@dataclass(frozen=True, slots=True)
class DescribedChoice:
    card: CatalogEntry
    answer: str
    form: CardForm


@dataclass(frozen=True, slots=True)
class DescribedQuestion:
    question: PhysicalQuestion
    choices: tuple[DescribedChoice, ...]


@dataclass(frozen=True, slots=True)
class WorkbenchCatalog:
    version: str
    questions: tuple[DescribedQuestion, ...]


class DescribeCatalog:
    def __init__(self, units: UnitRegistry, constants: ConstantsEdition) -> None:
        self._units = units
        self._constants = constants

    def execute(self) -> WorkbenchCatalog:
        cards = {card.identifier: card for card in catalog_entries()}
        return WorkbenchCatalog(
            version=CATALOG_VERSION,
            questions=tuple(
                DescribedQuestion(
                    question,
                    tuple(
                        DescribedChoice(
                            cards[choice.card_identifier],
                            choice.answer,
                            self._form(cards[choice.card_identifier]),
                        )
                        for choice in question.choices
                    ),
                )
                for question in PHYSICAL_QUESTIONS
            ),
        )

    def _form(self, card: CatalogEntry) -> CardForm:
        if isinstance(card, ProblemCard):
            return self._problem_form(card)
        if isinstance(card, StatementCard):
            return _statement_form(card)
        if isinstance(card, NumericalCard):
            return self._numerical_form(card)
        raise TypeError(f"card {card.identifier} has no input form")

    def _problem_form(self, card: ProblemCard) -> CardForm:
        output = card.outputs[0]
        return CardForm(
            kind=InputKind.PROBLEM,
            confirmations=_confirmations(card.hypotheses),
            quantities=self._quantities(card.quantities),
            counts=tuple(CountField(rule.name, rule.symbol, rule.label) for rule in card.counts),
            notation=None,
            arrays=(),
            settings=(),
            requested=RequestedFields(
                quantity=output.quantity,
                label=output.label,
                units=self._units.symbols_for(output.dimension),
                presence=Presence.REQUIRED,
            ),
            covariance_models=card.method.covariance_models,
        )

    def _numerical_form(self, card: NumericalCard) -> CardForm:
        sections = card.required_sections | card.optional_sections
        return CardForm(
            kind=InputKind.NUMERICAL,
            confirmations=_confirmations(card.hypotheses),
            quantities=self._quantities(card.quantities),
            counts=(),
            notation=_numerical_notation(sections),
            arrays=tuple(
                _array_field(card, section) for section in ARRAY_FIELDS if section in sections
            ),
            settings=NUMERICAL_SETTINGS[card.identifier],
            requested=self._numerical_display(card),
            covariance_models=(),
        )

    def _numerical_display(self, card: NumericalCard) -> RequestedFields:
        dimension = DISPLAY_DIMENSIONS.get(card.family)
        if dimension is None:
            return RequestedFields(None, _DIGITS_LABEL, (), Presence.OPTIONAL)
        return RequestedFields(
            None, _DISPLAY_LABEL, self._units.symbols_for(dimension), Presence.REQUIRED
        )

    def _quantities(self, rules: tuple[PositiveQuantityRule, ...]) -> tuple[QuantityField, ...]:
        return tuple(
            QuantityField(
                name=rule.name,
                symbol=rule.symbol,
                label=rule.label,
                dimension=describe_dimension(rule.dimension),
                units=self._units.symbols_for(rule.dimension),
                constants=tuple(
                    self._constant_choice(identifier)
                    for identifier in self._constants.identifiers_for(rule.dimension)
                ),
            )
            for rule in rules
        )

    def _constant_choice(self, identifier: str) -> ConstantChoice:
        constant = require_constant(self._constants, identifier)
        return ConstantChoice(identifier, constant.symbol, constant.name)


def _statement_form(card: StatementCard) -> CardForm:
    return CardForm(
        kind=InputKind.STATEMENT,
        confirmations=(),
        quantities=(),
        counts=(),
        notation=NotationFields(
            has_statement=True,
            has_equations=False,
            has_conditions=StatementField.CONDITIONS in card.required_fields,
            has_candidate=StatementField.CANDIDATE in card.required_fields,
            symbols_carry_values=False,
        ),
        arrays=(),
        settings=(),
        requested=None,
        covariance_models=(),
    )


def _numerical_notation(sections: frozenset[InputSection]) -> NotationFields | None:
    if not sections.intersection(_NOTATION_SECTIONS):
        return None
    return NotationFields(
        has_statement=InputSection.STATEMENT in sections,
        has_equations=InputSection.EQUATIONS in sections,
        has_conditions=InputSection.CONDITIONS in sections,
        has_candidate=False,
        symbols_carry_values=True,
    )


def _array_field(card: NumericalCard, section: InputSection) -> ArrayField:
    presence = Presence.REQUIRED if section in card.required_sections else Presence.OPTIONAL
    return replace(ARRAY_FIELDS[section], presence=presence)


def _confirmations(rules: tuple[HypothesisRule, ...]) -> tuple[Confirmation, ...]:
    return tuple(Confirmation(rule.key, rule.required_value, rule.statement) for rule in rules)
