from quantum_calculator.application.numerical.estimates import check_profile
from quantum_calculator.application.numerical.request import ValidationRequest, pointer_to
from quantum_calculator.application.numerical.settings import SettingsReader
from quantum_calculator.application.validation.hypotheses import confirm_hypotheses
from quantum_calculator.application.validation.output import rounding_policy
from quantum_calculator.application.validation.parameters import (
    ParameterBinder,
    reject_unknown_parameters,
)
from quantum_calculator.application.validation.unit_resolution import UnitResolver
from quantum_calculator.domain.constants import PLANCK_CONSTANT, PhysicalConstant
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.dimensions import ENERGY
from quantum_calculator.domain.numerical.problems import (
    InterpretedInput,
    NumericalContext,
    ResourceEstimate,
)
from quantum_calculator.domain.ports import ConstantsEdition, UnitRegistry, require_constant
from quantum_calculator.domain.rounding import (
    DEFAULT_SIGNIFICANT_DIGITS,
    MAX_SIGNIFICANT_DIGITS,
    RoundingPolicy,
    render_decimal,
)
from quantum_calculator.domain.units import Unit
from quantum_calculator.domain.validated_problem import BoundQuantity, ConfirmedHypothesis

_REQUESTED = "requested"
_UNIT = "unit"


class ValidationToolkit:
    def __init__(self, units: UnitRegistry, constants: ConstantsEdition) -> None:
        self.units = units
        self._constants = constants
        self._resolver = UnitResolver(units)
        self._binder = ParameterBinder(self._resolver, constants)

    @property
    def planck(self) -> PhysicalConstant:
        return require_constant(self._constants, PLANCK_CONSTANT)

    def hypotheses(self, request: ValidationRequest) -> tuple[ConfirmedHypothesis, ...]:
        given = request.spec.hypotheses
        if given is None:
            return ()
        return confirm_hypotheses(request.card.hypotheses, given, request.diagnostics)

    def quantities(self, request: ValidationRequest) -> dict[str, BoundQuantity]:
        rules = request.card.quantities
        parameters = request.spec.parameters
        if parameters is None:
            return {}
        bound = self._binder.bind_quantities(rules, parameters, request.diagnostics)
        reject_unknown_parameters(
            tuple(rule.name for rule in rules), parameters, request.diagnostics
        )
        return {quantity.name: quantity for quantity in bound}

    def describe_quantities(
        self, request: ValidationRequest, quantities: dict[str, BoundQuantity]
    ) -> tuple[InterpretedInput, ...]:
        return tuple(
            self._describe(quantities[rule.name], rule.label)
            for rule in request.card.quantities
            if rule.name in quantities
        )

    def energy_unit(self, request: ValidationRequest) -> Unit | None:
        requested = request.spec.requested
        if requested is None:
            return None
        if requested.unit is None:
            request.refuse(
                DiagnosticCode.MISSING_FIELD,
                pointer_to(_REQUESTED, _UNIT),
                "Falta a unidade de exibição das energias.",
                f"unidade de energia: {', '.join(self.units.symbols_for(ENERGY))}",
            )
            return None
        return self._resolver.resolve(
            requested.unit,
            ENERGY,
            "a energia dos níveis",
            pointer_to(_REQUESTED, _UNIT),
            request.diagnostics,
        )

    def refuse_display_unit(self, request: ValidationRequest) -> None:
        requested = request.spec.requested
        if requested is not None and requested.unit is not None:
            request.refuse(
                DiagnosticCode.UNEXPECTED_FIELD,
                pointer_to(_REQUESTED, _UNIT),
                f"A ficha {request.card.identifier} não converte a resposta para outra unidade.",
                "nenhuma unidade em requested; a resposta sai em unidades coerentes do SI",
            )

    def rounding(self, request: ValidationRequest) -> RoundingPolicy | None:
        requested = request.spec.requested
        if requested is None:
            return RoundingPolicy(DEFAULT_SIGNIFICANT_DIGITS)
        return rounding_policy(requested.significant_digits, request.diagnostics)

    def settings(self, request: ValidationRequest) -> SettingsReader:
        return SettingsReader(request)

    def constants_used(
        self, quantities: dict[str, BoundQuantity], display_unit: Unit | None
    ) -> tuple[PhysicalConstant, ...]:
        cited = (
            bound.origin
            for bound in quantities.values()
            if isinstance(bound.origin, PhysicalConstant)
        )
        defining = (
            require_constant(self._constants, identifier)
            for identifier in (() if display_unit is None else display_unit.defining_constants)
        )
        used = (self.planck, *cited, *defining)
        return tuple({constant.identifier: constant for constant in used}.values())

    def context(
        self,
        request: ValidationRequest,
        settings: SettingsReader,
        *,
        hypotheses: tuple[ConfirmedHypothesis, ...] = (),
        inputs: tuple[InterpretedInput, ...] = (),
        constants: tuple[PhysicalConstant, ...] = (),
        rounding: RoundingPolicy,
        estimate: ResourceEstimate,
    ) -> NumericalContext:
        check_profile(request, estimate)
        return NumericalContext(
            spec=request.spec,
            card=request.card,
            hypotheses=hypotheses,
            inputs=inputs,
            resolution=settings.resolution,
            constants=constants,
            rounding=rounding,
            estimate=estimate,
        )

    def _describe(self, bound: BoundQuantity, label: str) -> InterpretedInput:
        magnitude = render_decimal(bound.quantity.magnitude, MAX_SIGNIFICANT_DIGITS).decimal
        unit = self.units.coherent_symbol(bound.quantity.dimension)
        if isinstance(bound.origin, PhysicalConstant):
            origin = f"constante {bound.origin.identifier} do catálogo"
        else:
            origin = f"entrada: {bound.origin.number.literal} {bound.origin.unit.symbol}"
        return InterpretedInput(bound.name, label, f"{magnitude} {unit}", origin)
