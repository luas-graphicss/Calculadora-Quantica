from quantum_calculator.application.validation.unit_resolution import (
    UnitResolver,
    describe_dimension,
)
from quantum_calculator.domain.cards import PositiveIntegerRule, PositiveQuantityRule
from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    json_pointer,
    quote_user_text,
)
from quantum_calculator.domain.ports import ConstantsEdition
from quantum_calculator.domain.problem_spec import (
    ConstantInput,
    ExactNumber,
    ParameterContent,
    ParameterInput,
    QuantityInput,
)
from quantum_calculator.domain.validated_problem import BoundCount, BoundQuantity, UserQuantity

_POSITIVE_INTEGER = "inteiro positivo: 1, 2, 3, ..."


class ParameterBinder:
    def __init__(self, resolver: UnitResolver, constants: ConstantsEdition) -> None:
        self._resolver = resolver
        self._constants = constants

    def bind_quantities(
        self,
        rules: tuple[PositiveQuantityRule, ...],
        parameters: tuple[ParameterInput, ...],
        diagnostics: list[Diagnostic],
    ) -> tuple[BoundQuantity, ...]:
        given = _contents_by_name(parameters)
        candidates = (
            self._bind_quantity(rule, given.get(rule.name), diagnostics) for rule in rules
        )
        return tuple(bound for bound in candidates if bound is not None)

    def bind_counts(
        self,
        rules: tuple[PositiveIntegerRule, ...],
        parameters: tuple[ParameterInput, ...],
        diagnostics: list[Diagnostic],
    ) -> tuple[BoundCount, ...]:
        given = _contents_by_name(parameters)
        candidates = (_bind_count(rule, given.get(rule.name), diagnostics) for rule in rules)
        return tuple(bound for bound in candidates if bound is not None)

    def _bind_quantity(
        self,
        rule: PositiveQuantityRule,
        content: ParameterContent | None,
        diagnostics: list[Diagnostic],
    ) -> BoundQuantity | None:
        pointer = json_pointer("parameters", rule.name)
        match content:
            case QuantityInput():
                return self._bind_user_quantity(rule, content, pointer, diagnostics)
            case ConstantInput():
                return self._bind_constant(rule, content, pointer, diagnostics)
            case None:
                diagnostics.append(
                    Diagnostic(
                        DiagnosticCode.MISSING_FIELD,
                        pointer,
                        f"{_subject(rule).capitalize()} está ausente.",
                        self._quantity_forms(rule),
                    )
                )
            case ExactNumber():
                diagnostics.append(
                    Diagnostic(
                        DiagnosticCode.INVALID_TYPE,
                        pointer,
                        f"{_subject(rule).capitalize()} precisa de unidade.",
                        self._quantity_forms(rule),
                    )
                )
        return None

    def _bind_user_quantity(
        self,
        rule: PositiveQuantityRule,
        given: QuantityInput,
        pointer: str,
        diagnostics: list[Diagnostic],
    ) -> BoundQuantity | None:
        unit = self._resolver.resolve(
            given.unit, rule.dimension, _subject(rule), f"{pointer}/unit", diagnostics
        )
        is_positive = given.number.value > 0
        if not is_positive:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCode.NON_POSITIVE_QUANTITY,
                    f"{pointer}/value",
                    f"{_subject(rule).capitalize()} deve ser estritamente positivo; "
                    f"a entrada traz {quote_user_text(given.number.literal)}.",
                    "valor maior que zero",
                )
            )
        if unit is None or not is_positive:
            return None
        origin = UserQuantity(given.number, unit)
        return BoundQuantity(rule.name, rule.symbol, origin.to_si(), origin)

    def _bind_constant(
        self,
        rule: PositiveQuantityRule,
        given: ConstantInput,
        pointer: str,
        diagnostics: list[Diagnostic],
    ) -> BoundQuantity | None:
        constant = self._constants.find(given.identifier)
        if constant is None:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCode.UNKNOWN_CONSTANT,
                    f"{pointer}/constant",
                    f"A constante {quote_user_text(given.identifier)} não consta da edição "
                    f"{self._constants.label}.",
                    self._constant_candidates(rule),
                )
            )
            return None
        if constant.value.dimension != rule.dimension:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCode.DIMENSION_MISMATCH,
                    f"{pointer}/constant",
                    f"A constante {quote_user_text(given.identifier)} mede "
                    f"{describe_dimension(constant.value.dimension)}, mas {_subject(rule)} exige "
                    f"{describe_dimension(rule.dimension)}.",
                    self._constant_candidates(rule),
                )
            )
            return None
        return BoundQuantity(rule.name, rule.symbol, constant.value, constant)

    def _constant_candidates(self, rule: PositiveQuantityRule) -> str:
        identifiers = ", ".join(self._constants.identifiers_for(rule.dimension))
        return f"constante de {describe_dimension(rule.dimension)} do catálogo: {identifiers}"

    def _quantity_forms(self, rule: PositiveQuantityRule) -> str:
        return f"valor positivo com unidade de {describe_dimension(rule.dimension)} ou " + (
            self._constant_candidates(rule)
        )


def reject_unknown_parameters(
    known: tuple[str, ...], parameters: tuple[ParameterInput, ...], diagnostics: list[Diagnostic]
) -> None:
    diagnostics.extend(
        Diagnostic(
            DiagnosticCode.UNEXPECTED_FIELD,
            json_pointer("parameters", parameter.name),
            f"A ficha não usa o parâmetro {quote_user_text(parameter.name)}.",
            f"um destes parâmetros: {', '.join(known)}",
        )
        for parameter in parameters
        if parameter.name not in known
    )


def _bind_count(
    rule: PositiveIntegerRule, content: ParameterContent | None, diagnostics: list[Diagnostic]
) -> BoundCount | None:
    pointer = json_pointer("parameters", rule.name)
    if content is None:
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.MISSING_FIELD,
                pointer,
                f"{_subject(rule).capitalize()} está ausente.",
                _POSITIVE_INTEGER,
            )
        )
        return None
    if not isinstance(content, ExactNumber):
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.INVALID_TYPE,
                pointer,
                f"{_subject(rule).capitalize()} é uma contagem, sem unidade nem constante.",
                _POSITIVE_INTEGER,
            )
        )
        return None
    if content.value.denominator != 1 or content.value < 1:
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.NOT_A_POSITIVE_INTEGER,
                pointer,
                f"{_subject(rule).capitalize()} deve ser um inteiro positivo; "
                f"a entrada traz {quote_user_text(content.literal)}.",
                _POSITIVE_INTEGER,
            )
        )
        return None
    return BoundCount(rule.name, rule.symbol, content.value.numerator)


def _contents_by_name(parameters: tuple[ParameterInput, ...]) -> dict[str, ParameterContent]:
    return {parameter.name: parameter.content for parameter in parameters}


def _subject(rule: PositiveQuantityRule | PositiveIntegerRule) -> str:
    return f"o parâmetro {rule.name} ({rule.label})"
