from quantum_calculator.application.numerical.estimates import evolution_estimate
from quantum_calculator.application.numerical.limits import (
    MAX_MODES,
    MAX_SAMPLES,
    MAX_STEPS,
    MAX_SUBINTERVALS,
    MIN_SUBINTERVALS,
    NORMALIZATION_TOLERANCE,
    REFINEMENT_DIVISOR,
)
from quantum_calculator.application.numerical.mesh import check_refinable, check_saved_instants
from quantum_calculator.application.numerical.request import ValidationRequest, pointer_to
from quantum_calculator.application.numerical.scales import well_scales
from quantum_calculator.application.numerical.states import (
    check_state,
    complex_vector,
    describe_state,
)
from quantum_calculator.application.numerical.toolkit import ValidationToolkit
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.numerical.problems import (
    EvolutionProblem,
    NumericalProblem,
    PotentialModel,
    ScaledGrid,
)

_INITIAL_STATE = "initial_state"
_STEPS = "steps"
_STEPS_LABEL = "passos de tempo iguais"


class EvolutionValidator:
    def __init__(self, toolkit: ValidationToolkit) -> None:
        self._toolkit = toolkit

    def validate(self, request: ValidationRequest) -> NumericalProblem | None:
        toolkit = self._toolkit
        given = request.spec.initial_state
        hypotheses = toolkit.hypotheses(request)
        quantities = toolkit.quantities(request)
        settings = toolkit.settings(request)
        subintervals = settings.count(
            "subintervals", "subintervalos da malha uniforme", MIN_SUBINTERVALS, MAX_SUBINTERVALS
        )
        steps = settings.count(_STEPS, _STEPS_LABEL, REFINEMENT_DIVISOR, MAX_STEPS)
        samples = settings.count("samples", "instantes salvos, com o inicial", 2, MAX_SAMPLES)
        settings.reject_unknown()
        toolkit.refuse_display_unit(request)
        rounding = toolkit.rounding(request)
        if given is None or subintervals is None or steps is None or samples is None:
            return None
        coefficients = complex_vector(given.components)
        modes = len(coefficients)
        if modes > MAX_MODES or modes >= subintervals:
            request.refuse(
                DiagnosticCode.RESOURCE_LIMIT_EXCEEDED,
                pointer_to(_INITIAL_STATE),
                f"O estado inicial usa {modes} modos; o perfil homologado vai até {MAX_MODES}, "
                f"e a malha de {subintervals} subintervalos tem {subintervals - 1} incógnitas.",
                f"até {MAX_MODES} coeficientes, menos que as incógnitas da malha",
            )
            return None
        check_state(
            request,
            _INITIAL_STATE,
            coefficients,
            normalize=given.normalize,
            tolerance=NORMALIZATION_TOLERANCE,
        )
        check_refinable(settings, _STEPS, _STEPS_LABEL, steps)
        check_saved_instants(settings, steps, samples)
        mass, width = quantities.get("mass"), quantities.get("width")
        duration = quantities.get("duration")
        if mass is None or width is None or duration is None or rounding is None:
            return None
        scales = well_scales(
            mass.quantity.magnitude, width.quantity.magnitude, toolkit.planck.value.magnitude
        )
        return EvolutionProblem(
            context=toolkit.context(
                request,
                settings,
                hypotheses=hypotheses,
                inputs=(
                    *toolkit.describe_quantities(request, quantities),
                    describe_state(
                        _INITIAL_STATE,
                        "coeficientes sobre os primeiros modos discretos do poço",
                        coefficients,
                        normalize=given.normalize,
                    ),
                ),
                constants=toolkit.constants_used(quantities, None),
                rounding=rounding,
                estimate=evolution_estimate(subintervals, modes, steps, samples),
            ),
            scales=scales,
            grid=ScaledGrid(left=0.0, right=1.0, subintervals=subintervals),
            potential=PotentialModel.ZERO,
            coefficients=coefficients,
            normalize=given.normalize,
            scaled_duration=float(duration.quantity.magnitude) / scales.time,
            steps=steps,
            samples=samples,
        )
