from quantum_calculator.application.numerical.estimates import finite_basis_estimate
from quantum_calculator.application.numerical.limits import (
    LOOSEST_ALGEBRAIC_TOLERANCE,
    MAX_DIMENSION,
    NO_TOLERANCE,
)
from quantum_calculator.application.numerical.request import ValidationRequest, pointer_to
from quantum_calculator.application.numerical.states import (
    check_state,
    complex_matrix,
    complex_vector,
    describe_state,
)
from quantum_calculator.application.numerical.toolkit import ValidationToolkit
from quantum_calculator.application.statements.unit_expressions import (
    UNIT_EXPRESSION_FORM,
    UnitExpressionError,
    measure_of_unit,
)
from quantum_calculator.domain.diagnostics import DiagnosticCode, quote_user_text
from quantum_calculator.domain.numerical.complex_algebra import (
    hermiticity_defect,
    is_square,
    orthonormality_defect,
)
from quantum_calculator.domain.numerical.problems import (
    ComplexMatrix,
    FiniteBasisProblem,
    InterpretedInput,
    NumericalProblem,
)
from quantum_calculator.domain.numerical.spec import ObservableInput

_STATE = "state"
_OBSERVABLE = "observable"
_BASIS = "basis"
_HERMITIAN = "matriz igual à sua transposta conjugada"
_ORTHONORMAL = "vetores ortonormais, um por linha, escritos na base em que o estado foi dado"


class FiniteBasisValidator:
    def __init__(self, toolkit: ValidationToolkit) -> None:
        self._toolkit = toolkit

    def validate(self, request: ValidationRequest) -> NumericalProblem | None:
        toolkit = self._toolkit
        spec = request.spec
        hypotheses = toolkit.hypotheses(request)
        settings = toolkit.settings(request)
        tolerance = settings.within(
            "tolerance",
            "tolerância das checagens de norma, hermiticidade e base",
            NO_TOLERANCE,
            LOOSEST_ALGEBRAIC_TOLERANCE,
        )
        settings.reject_unknown()
        toolkit.refuse_display_unit(request)
        rounding = toolkit.rounding(request)
        if spec.state is None or spec.observable is None:
            return None
        if tolerance is None or rounding is None:
            return None
        limit = float(tolerance)
        state = complex_vector(spec.state.components)
        dimension = len(state)
        if dimension > MAX_DIMENSION:
            request.refuse(
                DiagnosticCode.RESOURCE_LIMIT_EXCEEDED,
                pointer_to(_STATE),
                f"O estado tem {dimension} amplitudes, acima do perfil homologado, que vai até "
                f"{MAX_DIMENSION}. Nada foi alocado.",
                f"até {MAX_DIMENSION} amplitudes",
            )
            return None
        check_state(request, _STATE, state, normalize=spec.state.normalize, tolerance=limit)
        observable = complex_matrix(spec.observable.matrix)
        self._check_observable(request, spec.observable, observable, dimension, limit)
        basis = None if spec.basis is None else complex_matrix(spec.basis)
        if basis is not None:
            _check_basis(request, basis, dimension, limit)
        inputs = [
            describe_state(_STATE, "estado informado", state, normalize=spec.state.normalize),
            InterpretedInput(
                _OBSERVABLE,
                "observável",
                f"matriz hermitiana {dimension} x {dimension}, autovalores na unidade "
                f"{spec.observable.unit}",
                "matriz informada na base do estado",
            ),
        ]
        if basis is not None:
            inputs.append(
                InterpretedInput(
                    _BASIS,
                    "mudança de base",
                    f"{dimension} vetores ortonormais",
                    "estado e observável são reescritos na base informada antes da medição",
                )
            )
        return FiniteBasisProblem(
            context=toolkit.context(
                request,
                settings,
                hypotheses=hypotheses,
                inputs=tuple(inputs),
                rounding=rounding,
                estimate=finite_basis_estimate(dimension),
            ),
            state=state,
            normalize=spec.state.normalize,
            observable=observable,
            unit=spec.observable.unit,
            basis=basis,
            tolerance=limit,
        )

    def _check_observable(
        self,
        request: ValidationRequest,
        given: ObservableInput,
        observable: ComplexMatrix,
        dimension: int,
        tolerance: float,
    ) -> None:
        try:
            measure_of_unit(given.unit, self._toolkit.units)
        except UnitExpressionError as error:
            request.refuse(
                DiagnosticCode.UNKNOWN_UNIT,
                pointer_to(_OBSERVABLE, "unit"),
                f"A unidade {quote_user_text(given.unit)} não foi aceita: {error}.",
                UNIT_EXPRESSION_FORM,
            )
        pointer = pointer_to(_OBSERVABLE, "matrix")
        if not is_square(observable, dimension):
            request.refuse(
                DiagnosticCode.INVALID_SHAPE,
                pointer,
                f"O observável deve ser uma matriz {dimension} x {dimension}, do tamanho do "
                f"estado de {dimension} amplitudes.",
                f"{dimension} linhas de {dimension} números",
            )
            return
        defect = hermiticity_defect(observable)
        scale = max(1.0, max(abs(entry) for row in observable for entry in row))
        if defect > tolerance * scale:
            request.refuse(
                DiagnosticCode.NON_HERMITIAN_OPERATOR,
                pointer,
                f"O observável difere do seu adjunto conjugado em até {defect!r}: só um "
                "operador hermitiano tem medição projetiva com resultados reais.",
                _HERMITIAN,
            )


def _check_basis(
    request: ValidationRequest, basis: ComplexMatrix, dimension: int, tolerance: float
) -> None:
    pointer = pointer_to(_BASIS)
    if not is_square(basis, dimension):
        request.refuse(
            DiagnosticCode.INVALID_SHAPE,
            pointer,
            f"A base deve trazer {dimension} vetores de {dimension} componentes.",
            _ORTHONORMAL,
        )
        return
    defect = orthonormality_defect(basis)
    if defect > tolerance:
        request.refuse(
            DiagnosticCode.BASIS_NOT_ORTHONORMAL,
            pointer,
            f"Os vetores da base diferem da ortonormalidade em até {defect!r}.",
            _ORTHONORMAL,
        )
