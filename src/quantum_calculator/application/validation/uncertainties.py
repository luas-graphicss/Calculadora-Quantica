from quantum_calculator.application.validation.unit_resolution import UnitResolver
from quantum_calculator.domain.cards import PositiveQuantityRule, ProblemCard
from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    json_pointer,
    quote_user_text,
)
from quantum_calculator.domain.problem_spec import ProblemSpec, QuantityInput
from quantum_calculator.domain.validated_problem import (
    DeclaredUncertainty,
    UncertaintyModel,
    UserQuantity,
)

_SECTION = ("uncertainty", "standard_uncertainties")


def bind_uncertainty(
    card: ProblemCard, spec: ProblemSpec, resolver: UnitResolver, diagnostics: list[Diagnostic]
) -> UncertaintyModel | None:
    declaration = spec.uncertainty
    if declaration is None:
        return None
    supported = card.method.covariance_models
    if declaration.covariance not in supported:
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.UNSUPPORTED_COVARIANCE,
                "/uncertainty/covariance",
                f"A hipótese de covariância {quote_user_text(declaration.covariance)} "
                "não está homologada para esta ficha.",
                f"uma destas hipóteses: {', '.join(supported)}",
            )
        )
    given = {entry.parameter: entry.quantity for entry in declaration.standard_uncertainties}
    declared: list[DeclaredUncertainty] = []
    for rule in card.quantities:
        uncertainty = _bind(rule, given.pop(rule.name, None), resolver, diagnostics)
        if uncertainty is not None:
            declared.append(uncertainty)
    known = ", ".join(rule.name for rule in card.quantities)
    diagnostics.extend(
        Diagnostic(
            DiagnosticCode.UNEXPECTED_FIELD,
            json_pointer(*_SECTION, name),
            f"A ficha não tem a grandeza {quote_user_text(name)} para receber incerteza.",
            f"uma destas grandezas: {known}",
        )
        for name in given
    )
    return UncertaintyModel(declaration.covariance, tuple(declared))


def _bind(
    rule: PositiveQuantityRule,
    given: QuantityInput | None,
    resolver: UnitResolver,
    diagnostics: list[Diagnostic],
) -> DeclaredUncertainty | None:
    pointer = json_pointer(*_SECTION, rule.name)
    subject = f"a incerteza-padrão do parâmetro {rule.name} ({rule.label})"
    if given is None:
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.MISSING_FIELD,
                pointer,
                f"Falta {subject}.",
                "valor não negativo com unidade; 0 declara o parâmetro como exato",
            )
        )
        return None
    unit = resolver.resolve(given.unit, rule.dimension, subject, f"{pointer}/unit", diagnostics)
    is_non_negative = given.number.value >= 0
    if not is_non_negative:
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.NEGATIVE_UNCERTAINTY,
                f"{pointer}/value",
                f"{subject.capitalize()} não pode ser negativa; "
                f"a entrada traz {quote_user_text(given.number.literal)}.",
                "valor maior ou igual a zero",
            )
        )
    if unit is None or not is_non_negative:
        return None
    return DeclaredUncertainty(rule.name, UserQuantity(given.number, unit))
