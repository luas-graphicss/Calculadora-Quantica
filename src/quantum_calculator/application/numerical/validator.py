from typing import Protocol

from quantum_calculator.application.numerical.evolution import EvolutionValidator
from quantum_calculator.application.numerical.expressions import ExpressionBinder
from quantum_calculator.application.numerical.finite_basis import FiniteBasisValidator
from quantum_calculator.application.numerical.initial_value import InitialValueValidator
from quantum_calculator.application.numerical.quadrature import QuadratureValidator
from quantum_calculator.application.numerical.request import ValidationRequest
from quantum_calculator.application.numerical.sections import check_sections
from quantum_calculator.application.numerical.spectrum import SpectrumValidator
from quantum_calculator.application.numerical.toolkit import ValidationToolkit
from quantum_calculator.catalog.numerical_catalog import NumericalCatalog
from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    ProblemRejectedError,
    quote_user_text,
)
from quantum_calculator.domain.numerical.cards import NumericalCard, NumericalFamily
from quantum_calculator.domain.numerical.problems import NumericalProblem
from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.domain.ports import ConstantsEdition, UnitRegistry


class FamilyValidator(Protocol):
    def validate(self, request: ValidationRequest) -> NumericalProblem | None: ...


class NumericalValidator:
    def __init__(
        self, catalog: NumericalCatalog, units: UnitRegistry, constants: ConstantsEdition
    ) -> None:
        self._catalog = catalog
        toolkit = ValidationToolkit(units, constants)
        binder = ExpressionBinder(units)
        spectrum = SpectrumValidator(toolkit)
        self._families: dict[NumericalFamily, FamilyValidator] = {
            NumericalFamily.QUADRATURE: QuadratureValidator(toolkit, binder),
            NumericalFamily.INITIAL_VALUE: InitialValueValidator(toolkit, binder),
            NumericalFamily.FINITE_BASIS: FiniteBasisValidator(toolkit),
            NumericalFamily.WELL_SPECTRUM: spectrum,
            NumericalFamily.OSCILLATOR_SPECTRUM: spectrum,
            NumericalFamily.WELL_EVOLUTION: EvolutionValidator(toolkit),
        }

    def validate(self, spec: NumericalSpec) -> NumericalProblem:
        request = ValidationRequest(self._find_card(spec), spec, [])
        check_sections(request)
        problem = self._families[request.card.family].validate(request)
        if problem is None or request.diagnostics:
            raise ProblemRejectedError(tuple(request.diagnostics))
        return problem

    def _find_card(self, spec: NumericalSpec) -> NumericalCard:
        card = self._catalog.find(spec.card_identifier)
        if card is None:
            raise ProblemRejectedError(
                (
                    Diagnostic(
                        DiagnosticCode.UNKNOWN_PROBLEM,
                        "/problem",
                        f"A ficha {quote_user_text(spec.card_identifier)} não está entre as "
                        "fichas numéricas homologadas.",
                        f"uma destas fichas: {', '.join(self._catalog.identifiers)}",
                    ),
                )
            )
        return card
