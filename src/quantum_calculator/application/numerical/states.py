from quantum_calculator.application.numerical.request import ValidationRequest, pointer_to
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.numerical.complex_algebra import norm
from quantum_calculator.domain.numerical.problems import (
    ComplexMatrix,
    ComplexVector,
    InterpretedInput,
)
from quantum_calculator.domain.numerical.spec import ComplexInput, MatrixInput, VectorInput

_NORMALIZED = 'estado de norma 1 ou "normalize": true, que fica registrado no resultado'


def complex_vector(components: VectorInput) -> ComplexVector:
    return tuple(_complex(component) for component in components)


def complex_matrix(rows: MatrixInput) -> ComplexMatrix:
    return tuple(complex_vector(row) for row in rows)


def check_state(
    request: ValidationRequest,
    section: str,
    state: ComplexVector,
    *,
    normalize: bool,
    tolerance: float,
) -> None:
    magnitude = norm(state)
    if magnitude == 0.0:
        request.refuse(
            DiagnosticCode.ZERO_STATE,
            pointer_to(section),
            "Todas as amplitudes são nulas: o vetor nulo não é um estado físico.",
            "ao menos uma amplitude diferente de zero",
        )
    elif not normalize and abs(magnitude - 1.0) > tolerance:
        request.refuse(
            DiagnosticCode.STATE_NOT_NORMALIZED,
            pointer_to(section),
            f"A norma do estado é {magnitude!r}, não 1, e a normalização não foi pedida.",
            _NORMALIZED,
        )


def describe_state(
    name: str, label: str, state: ComplexVector, *, normalize: bool
) -> InterpretedInput:
    magnitude = norm(state)
    origin = (
        f"normalização pedida: as amplitudes foram divididas pela norma {magnitude!r}"
        if normalize
        else f"usado como informado, com norma {magnitude!r}"
    )
    return InterpretedInput(name, label, describe_vector(state), origin)


def describe_vector(vector: ComplexVector) -> str:
    return f"({', '.join(_shown(component) for component in vector)})"


def _complex(component: ComplexInput) -> complex:
    imaginary = 0.0 if component.imaginary is None else float(component.imaginary.value)
    return complex(float(component.real.value), imaginary)


def _shown(value: complex) -> str:
    if value.imag == 0.0:
        return repr(value.real)
    sign = "+" if value.imag > 0.0 else "-"
    return f"{value.real!r} {sign} {abs(value.imag)!r}i"
