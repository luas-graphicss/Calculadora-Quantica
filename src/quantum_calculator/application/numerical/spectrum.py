from fractions import Fraction

from quantum_calculator.application.numerical.estimates import spectrum_estimate
from quantum_calculator.application.numerical.limits import (
    MAX_HALF_WIDTH,
    MAX_LEVELS,
    MAX_SUBINTERVALS,
    MIN_SUBINTERVALS,
)
from quantum_calculator.application.numerical.mesh import check_refinable, check_resolved_levels
from quantum_calculator.application.numerical.request import ValidationRequest
from quantum_calculator.application.numerical.scales import oscillator_scales, well_scales
from quantum_calculator.application.numerical.toolkit import ValidationToolkit
from quantum_calculator.domain.numerical.cards import NumericalFamily
from quantum_calculator.domain.numerical.problems import (
    NumericalProblem,
    PhysicalScales,
    PotentialModel,
    ScaledGrid,
    SpectrumProblem,
)
from quantum_calculator.domain.validated_problem import BoundQuantity

_SUBINTERVALS = "subintervals"
_SUBINTERVALS_LABEL = "subintervalos da malha uniforme"


class SpectrumValidator:
    def __init__(self, toolkit: ValidationToolkit) -> None:
        self._toolkit = toolkit

    def validate(self, request: ValidationRequest) -> NumericalProblem | None:
        toolkit = self._toolkit
        is_oscillator = request.card.family is NumericalFamily.OSCILLATOR_SPECTRUM
        hypotheses = toolkit.hypotheses(request)
        quantities = toolkit.quantities(request)
        settings = toolkit.settings(request)
        subintervals = settings.count(
            _SUBINTERVALS, _SUBINTERVALS_LABEL, MIN_SUBINTERVALS, MAX_SUBINTERVALS
        )
        levels = settings.count("levels", "níveis pedidos, a partir do fundamental", 1, MAX_LEVELS)
        half_width = (
            settings.within(
                "half_width",
                "meia largura do domínio, em comprimentos do oscilador",
                Fraction(0),
                MAX_HALF_WIDTH,
            )
            if is_oscillator
            else Fraction(1, 2)
        )
        settings.reject_unknown()
        unit = toolkit.energy_unit(request)
        rounding = toolkit.rounding(request)
        scales = self._scales(quantities, is_oscillator=is_oscillator)
        if subintervals is None or levels is None or half_width is None:
            return None
        check_refinable(settings, _SUBINTERVALS, _SUBINTERVALS_LABEL, subintervals)
        check_resolved_levels(settings, subintervals, levels)
        if scales is None or unit is None or rounding is None:
            return None
        left = -float(half_width) if is_oscillator else 0.0
        return SpectrumProblem(
            context=toolkit.context(
                request,
                settings,
                hypotheses=hypotheses,
                inputs=toolkit.describe_quantities(request, quantities),
                constants=toolkit.constants_used(quantities, unit),
                rounding=rounding,
                estimate=spectrum_estimate(subintervals, levels, is_truncated=is_oscillator),
            ),
            scales=scales,
            grid=ScaledGrid(
                left=left, right=left + 2 * float(half_width), subintervals=subintervals
            ),
            potential=PotentialModel.HARMONIC if is_oscillator else PotentialModel.ZERO,
            levels=levels,
            energy_unit=unit,
            is_truncated_domain=is_oscillator,
        )

    def _scales(
        self, quantities: dict[str, BoundQuantity], *, is_oscillator: bool
    ) -> PhysicalScales | None:
        mass = quantities.get("mass")
        extent = quantities.get("level_spacing" if is_oscillator else "width")
        if mass is None or extent is None:
            return None
        build = oscillator_scales if is_oscillator else well_scales
        return build(
            mass.quantity.magnitude,
            extent.quantity.magnitude,
            self._toolkit.planck.value.magnitude,
        )
