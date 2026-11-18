from quantum_calculator.application.numerical.request import ValidationRequest, pointer_to
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.numerical.cards import InputSection

_NUMERICS = "numerics"
_EXPLICIT_RESOLUTION = (
    "objeto numerics com a resolução e as tolerâncias desta ficha; nada é escolhido em silêncio"
)


def check_sections(request: ValidationRequest) -> None:
    card, spec = request.card, request.spec
    provided = spec.provided_sections
    for section in InputSection:
        if section in card.required_sections and section not in provided:
            request.refuse(
                DiagnosticCode.MISSING_FIELD,
                pointer_to(section.value),
                f"A ficha {card.identifier} exige o campo {section.value}, que está ausente.",
                f"o campo {section.value}, como no exemplo {card.example}",
            )
        if section in provided and section not in card.required_sections | card.optional_sections:
            request.refuse(
                DiagnosticCode.UNEXPECTED_FIELD,
                pointer_to(section.value),
                f"A ficha {card.identifier} não usa o campo {section.value}.",
                f"nenhum campo {section.value} para esta ficha",
            )
    if spec.numerics is None:
        request.refuse(
            DiagnosticCode.MISSING_FIELD,
            pointer_to(_NUMERICS),
            f"A ficha {card.identifier} é numérica e a resposta é aproximada: a resolução e as "
            "tolerâncias precisam vir na entrada.",
            _EXPLICIT_RESOLUTION,
        )
