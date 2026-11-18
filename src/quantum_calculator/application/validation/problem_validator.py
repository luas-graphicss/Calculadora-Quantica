from quantum_calculator.application.validation.hypotheses import confirm_hypotheses
from quantum_calculator.application.validation.output import bind_output
from quantum_calculator.application.validation.parameters import (
    ParameterBinder,
    reject_unknown_parameters,
)
from quantum_calculator.application.validation.uncertainties import bind_uncertainty
from quantum_calculator.application.validation.unit_resolution import UnitResolver
from quantum_calculator.catalog.card_catalog import CardCatalog
from quantum_calculator.domain.cards import ProblemCard
from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    ProblemRejectedError,
    quote_user_text,
)
from quantum_calculator.domain.ports import ConstantsEdition, UnitRegistry
from quantum_calculator.domain.problem_spec import ProblemSpec
from quantum_calculator.domain.validated_problem import ValidatedProblem


class ProblemValidator:
    def __init__(
        self, catalog: CardCatalog, units: UnitRegistry, constants: ConstantsEdition
    ) -> None:
        self._catalog = catalog
        self._resolver = UnitResolver(units)
        self._binder = ParameterBinder(self._resolver, constants)

    def validate(self, spec: ProblemSpec) -> ValidatedProblem:
        card = self._find_card(spec)
        diagnostics: list[Diagnostic] = []
        hypotheses = confirm_hypotheses(card, spec, diagnostics)
        quantities = self._binder.bind_quantities(card, spec, diagnostics)
        counts = self._binder.bind_counts(card, spec, diagnostics)
        reject_unknown_parameters(card, spec, diagnostics)
        output = bind_output(card, spec, self._resolver, diagnostics)
        uncertainty = bind_uncertainty(card, spec, self._resolver, diagnostics)
        if diagnostics or output is None:
            raise ProblemRejectedError(tuple(diagnostics))
        return ValidatedProblem(
            spec=spec,
            card=card,
            hypotheses=hypotheses,
            quantities=quantities,
            counts=counts,
            output=output,
            uncertainty=uncertainty,
        )

    def _find_card(self, spec: ProblemSpec) -> ProblemCard:
        card = self._catalog.find(spec.card_identifier)
        if card is None:
            raise ProblemRejectedError(
                (
                    Diagnostic(
                        DiagnosticCode.UNKNOWN_PROBLEM,
                        "/problem",
                        f"A ficha {quote_user_text(spec.card_identifier)} não está no "
                        "catálogo homologado.",
                        f"uma destas fichas: {', '.join(self._catalog.identifiers)}",
                    ),
                )
            )
        return card
