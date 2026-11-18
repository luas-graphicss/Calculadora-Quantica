from quantum_calculator.application.validation.unit_resolution import UnitResolver
from quantum_calculator.domain.cards import ProblemCard
from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode, quote_user_text
from quantum_calculator.domain.problem_spec import ExactNumber, ProblemSpec
from quantum_calculator.domain.rounding import (
    DEFAULT_SIGNIFICANT_DIGITS,
    MAX_SIGNIFICANT_DIGITS,
    RoundingPolicy,
)
from quantum_calculator.domain.validated_problem import BoundOutput


def bind_output(
    card: ProblemCard, spec: ProblemSpec, resolver: UnitResolver, diagnostics: list[Diagnostic]
) -> BoundOutput | None:
    requested = spec.requested
    rule = next((rule for rule in card.outputs if rule.quantity == requested.quantity), None)
    if rule is None:
        offered = ", ".join(output.quantity for output in card.outputs)
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.UNSUPPORTED_QUANTITY,
                "/requested/quantity",
                f"A ficha não calcula a grandeza {quote_user_text(requested.quantity)}.",
                f"uma destas grandezas: {offered}",
            )
        )
        return None
    unit = resolver.resolve(
        requested.unit,
        rule.dimension,
        f"a grandeza {rule.quantity} ({rule.label})",
        "/requested/unit",
        diagnostics,
    )
    rounding = _rounding_policy(requested.significant_digits, diagnostics)
    if unit is None or rounding is None:
        return None
    return BoundOutput(rule, unit, rounding)


def _rounding_policy(
    requested: ExactNumber | None, diagnostics: list[Diagnostic]
) -> RoundingPolicy | None:
    if requested is None:
        return RoundingPolicy(DEFAULT_SIGNIFICANT_DIGITS)
    digits = requested.value
    if digits.denominator != 1 or not 1 <= digits <= MAX_SIGNIFICANT_DIGITS:
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.NUMBER_OUT_OF_RANGE,
                "/requested/significant_digits",
                f"A quantidade de algarismos significativos "
                f"{quote_user_text(requested.literal)} não é aceita.",
                f"inteiro entre 1 e {MAX_SIGNIFICANT_DIGITS}",
            )
        )
        return None
    return RoundingPolicy(digits.numerator)
