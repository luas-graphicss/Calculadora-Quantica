from quantum_calculator.domain.numerical.spec import ComplexInput, MatrixInput, VectorInput
from quantum_calculator.interfaces.serialization.decoding.number_literals import (
    NUMBER_EXPECTATION,
)
from quantum_calculator.interfaces.serialization.decoding.object_reader import ObjectReader

MAX_VECTOR_LENGTH = 16
COMPLEX_FORM = 'número real ou objeto {"real", "imaginary"}'
VECTOR_FORM = f"lista de 1 a {MAX_VECTOR_LENGTH} números complexos: {COMPLEX_FORM}"
MATRIX_FORM = f"lista de 1 a {MAX_VECTOR_LENGTH} linhas, cada uma {VECTOR_FORM}"


def decode_vector(items: ObjectReader) -> VectorInput:
    return tuple(_decode_complex(items, index) for index in items.keys)


def decode_matrix(rows: ObjectReader) -> MatrixInput:
    return tuple(
        decode_vector(rows.sequence(index, VECTOR_FORM, MAX_VECTOR_LENGTH)) for index in rows.keys
    )


def _decode_complex(items: ObjectReader, index: str) -> ComplexInput:
    if not items.holds_object(index):
        return ComplexInput(items.number(index, COMPLEX_FORM), None)
    parts = items.nested(index, COMPLEX_FORM)
    value = ComplexInput(
        real=parts.number("real", NUMBER_EXPECTATION),
        imaginary=parts.number("imaginary", NUMBER_EXPECTATION),
    )
    parts.reject_unknown_fields()
    return value
