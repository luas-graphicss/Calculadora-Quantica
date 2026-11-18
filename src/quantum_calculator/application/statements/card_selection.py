from dataclasses import dataclass

from quantum_calculator.application.statements.shape_rules import statement_shape
from quantum_calculator.catalog.statement_catalog import StatementCatalog
from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode, quote_user_text
from quantum_calculator.domain.expressions import Equation, Statement
from quantum_calculator.domain.statement_cards import StatementCard, StatementField, StatementShape
from quantum_calculator.domain.statements import CardSelection, StatementSpec

_CARD_POINTER = "/problem"
_STATEMENT_POINTER = "/statement"
_FIELD_POINTERS = {
    StatementField.CONDITIONS: "/conditions",
    StatementField.CANDIDATE: "/candidate",
}
_FIELD_FORMS = {
    StatementField.CONDITIONS: "lista com a condição inicial, como y(0) = y_0",
    StatementField.CANDIDATE: "a solução candidata, como y(t) = y_0*exp(-k*t)",
}


@dataclass(frozen=True, slots=True)
class SelectedCard:
    card: StatementCard
    selection: CardSelection


class CardSelector:
    def __init__(self, catalog: StatementCatalog) -> None:
        self._catalog = catalog

    def select(
        self, spec: StatementSpec, statement: Statement, diagnostics: list[Diagnostic]
    ) -> SelectedCard | None:
        shape = statement_shape(statement)
        provided = _provided_fields(spec)
        if spec.card_identifier is not None:
            return self._confirm(spec.card_identifier, shape, provided, diagnostics)
        if shape is None:
            diagnostics.append(_no_compatible_card(statement))
            return None
        compatible = self._catalog.with_shape(shape)
        matching = [card for card in compatible if card.required_fields == provided]
        if len(matching) == 1:
            return SelectedCard(matching[0], CardSelection.SUGGESTED)
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.AMBIGUOUS_PROBLEM,
                _CARD_POINTER,
                "O enunciado e os campos fornecidos não escolhem uma única ficha.",
                f"a ficha confirmada em problem: {_describe(compatible)}",
            )
        )
        return None

    def _confirm(
        self,
        identifier: str,
        shape: StatementShape | None,
        provided: frozenset[StatementField],
        diagnostics: list[Diagnostic],
    ) -> SelectedCard | None:
        card = self._catalog.find(identifier)
        if card is None:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCode.UNKNOWN_PROBLEM,
                    _CARD_POINTER,
                    f"A ficha {quote_user_text(identifier)} não está no catálogo homologado.",
                    f"uma destas fichas: {', '.join(self._catalog.identifiers)}",
                )
            )
            return None
        if card.shape is not shape:
            compatible = () if shape is None else self._catalog.with_shape(shape)
            diagnostics.append(
                Diagnostic(
                    DiagnosticCode.CARD_MISMATCH,
                    _CARD_POINTER,
                    f"A ficha {card.identifier} não cobre a forma deste enunciado.",
                    f"uma ficha compatível com o enunciado: {_describe(compatible)}",
                )
            )
            return None
        mismatches = [*_missing(card, provided), *_unused(card, provided)]
        diagnostics.extend(mismatches)
        return None if mismatches else SelectedCard(card, CardSelection.CONFIRMED)


def _provided_fields(spec: StatementSpec) -> frozenset[StatementField]:
    provided = set()
    if spec.conditions:
        provided.add(StatementField.CONDITIONS)
    if spec.candidate is not None:
        provided.add(StatementField.CANDIDATE)
    return frozenset(provided)


def _missing(card: StatementCard, provided: frozenset[StatementField]) -> list[Diagnostic]:
    return [
        Diagnostic(
            DiagnosticCode.MISSING_FIELD,
            _FIELD_POINTERS[field],
            f"A ficha {card.identifier} exige o campo {field.value}, que está ausente.",
            _FIELD_FORMS[field],
        )
        for field in StatementField
        if field in card.required_fields and field not in provided
    ]


def _unused(card: StatementCard, provided: frozenset[StatementField]) -> list[Diagnostic]:
    return [
        Diagnostic(
            DiagnosticCode.UNEXPECTED_FIELD,
            _FIELD_POINTERS[field],
            f"A ficha {card.identifier} não usa o campo {field.value}.",
            f"nenhum campo {field.value} para esta ficha",
        )
        for field in StatementField
        if field in provided and field not in card.required_fields
    ]


def _no_compatible_card(statement: Statement) -> Diagnostic:
    if isinstance(statement, Equation):
        return Diagnostic(
            DiagnosticCode.NO_COMPATIBLE_CARD,
            _STATEMENT_POINTER,
            "Nenhuma ficha homologada cobre esta equação: ela não traz a derivada de uma "
            "função declarada.",
            "uma EDO de primeira ordem em uma função declarada, ou uma expressão com diff, "
            "partial ou integral",
        )
    return Diagnostic(
        DiagnosticCode.AMBIGUOUS_PROBLEM,
        _STATEMENT_POINTER,
        "A expressão não diz a operação pedida: ela pode ser derivada ou integrada.",
        "a operação em volta da expressão: diff(...), partial(...) ou integral(...)",
    )


def _describe(cards: tuple[StatementCard, ...]) -> str:
    if not cards:
        return "nenhuma ficha homologada tem essa forma"
    return "; ".join(f"{card.identifier} ({_requirements(card)})" for card in cards)


def _requirements(card: StatementCard) -> str:
    required = [field.value for field in StatementField if field in card.required_fields]
    return f"exige {' e '.join(required)}" if required else "sem conditions nem candidate"
