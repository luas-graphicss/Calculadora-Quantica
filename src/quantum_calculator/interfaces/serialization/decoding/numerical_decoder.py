from quantum_calculator.domain.diagnostics import Diagnostic, ProblemRejectedError
from quantum_calculator.domain.numerical.spec import (
    NumericalSpec,
    ObservableInput,
    RequestedDisplay,
    SettingInput,
    StateInput,
    SymbolInput,
)
from quantum_calculator.domain.problem_spec import SourceDocument
from quantum_calculator.interfaces.serialization.decoding.complex_values import (
    MATRIX_FORM,
    MAX_VECTOR_LENGTH,
    VECTOR_FORM,
    decode_matrix,
    decode_vector,
)
from quantum_calculator.interfaces.serialization.decoding.json_document import (
    MAX_DOCUMENT_BYTES,
    read_document,
)
from quantum_calculator.interfaces.serialization.decoding.number_literals import (
    NUMBER_EXPECTATION,
)
from quantum_calculator.interfaces.serialization.decoding.object_reader import (
    MAX_LIST_LENGTH,
    ObjectReader,
)
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import (
    decode_hypotheses,
    decode_parameters,
)
from quantum_calculator.interfaces.serialization.decoding.schema_version import (
    decode_schema_version,
)
from quantum_calculator.interfaces.serialization.decoding.statement_decoder import (
    read_symbol_declaration,
)

NUMERICAL_SCHEMA_VERSION = "1.0"
NUMERICS_FIELD = "numerics"

_SYMBOL_FORM = (
    'objeto {"role", "domain", "unit"}, com "argument" nas funções e "value" nos parâmetros'
)
_STATE_FORM = 'objeto com a lista de amplitudes e, se desejado, "normalize"'
_NOTATED_LIST = "lista de textos na notação declarada"
_FLAG = "true ou false"


def decode_numerical(raw: bytes) -> NumericalSpec:
    return decode_numerical_document(*read_document(raw))


def decode_numerical_document(source: SourceDocument, content: dict[str, object]) -> NumericalSpec:
    diagnostics: list[Diagnostic] = []
    document = ObjectReader(content, "", diagnostics)
    hypotheses = document.optional_nested("hypotheses", "objeto com as hipóteses confirmadas")
    parameters = document.optional_nested("parameters", "objeto com os parâmetros do problema")
    symbols = document.optional_nested("symbols", "objeto com a declaração de cada símbolo")
    basis = document.optional_sequence("basis", MATRIX_FORM, MAX_VECTOR_LENGTH)
    numerics = document.optional_nested(NUMERICS_FIELD, "objeto com a resolução e as tolerâncias")
    spec = NumericalSpec(
        source=source,
        schema_version=decode_schema_version(document, NUMERICAL_SCHEMA_VERSION),
        card_identifier=document.text("problem", "identificador de uma ficha numérica do catálogo"),
        description=document.optional_text("description", "texto livre que descreve o caso"),
        hypotheses=None if hypotheses is None else decode_hypotheses(hypotheses),
        parameters=None if parameters is None else decode_parameters(parameters),
        notation=document.optional_text("notation", '"text" ou "latex"'),
        symbols=None if symbols is None else _decode_symbols(symbols),
        statement=document.optional_text(
            "statement", "a integral na notação declarada", MAX_DOCUMENT_BYTES
        ),
        equations=_decode_texts(document, "equations"),
        conditions=_decode_texts(document, "conditions"),
        state=_decode_state(document, "state", "components"),
        observable=_decode_observable(
            document.optional_nested("observable", 'objeto {"matrix", "unit"}')
        ),
        basis=None if basis is None else decode_matrix(basis),
        initial_state=_decode_state(document, "initial_state", "coefficients"),
        numerics=None if numerics is None else _decode_settings(numerics),
        requested=_decode_requested(
            document.optional_nested("requested", "objeto com a unidade e os algarismos pedidos")
        ),
    )
    document.reject_unknown_fields()
    if diagnostics:
        raise ProblemRejectedError(tuple(diagnostics))
    return spec


def _decode_symbols(fields: ObjectReader) -> tuple[SymbolInput, ...]:
    return tuple(_decode_symbol(name, fields.nested(name, _SYMBOL_FORM)) for name in fields.keys)


def _decode_symbol(name: str, fields: ObjectReader) -> SymbolInput:
    symbol = SymbolInput(
        declaration=read_symbol_declaration(name, fields),
        value=fields.optional_number("value", "o valor do parâmetro, na unidade declarada"),
    )
    fields.reject_unknown_fields()
    return symbol


def _decode_texts(document: ObjectReader, key: str) -> tuple[str, ...] | None:
    items = document.optional_sequence(key, _NOTATED_LIST, MAX_LIST_LENGTH)
    if items is None:
        return None
    return tuple(items.text(index, _NOTATED_LIST, MAX_DOCUMENT_BYTES) for index in items.keys)


def _decode_state(document: ObjectReader, key: str, amplitudes: str) -> StateInput | None:
    fields = document.optional_nested(key, _STATE_FORM)
    if fields is None:
        return None
    state = StateInput(
        components=decode_vector(fields.sequence(amplitudes, VECTOR_FORM, MAX_VECTOR_LENGTH)),
        normalize=fields.optional_flag("normalize", _FLAG) or False,
    )
    fields.reject_unknown_fields()
    return state


def _decode_observable(fields: ObjectReader | None) -> ObservableInput | None:
    if fields is None:
        return None
    observable = ObservableInput(
        matrix=decode_matrix(fields.sequence("matrix", MATRIX_FORM, MAX_VECTOR_LENGTH)),
        unit=fields.text("unit", 'a unidade dos autovalores, ou "1" para adimensional'),
    )
    fields.reject_unknown_fields()
    return observable


def _decode_settings(fields: ObjectReader) -> tuple[SettingInput, ...]:
    return tuple(
        SettingInput(name, fields.number(name, NUMBER_EXPECTATION)) for name in fields.keys
    )


def _decode_requested(fields: ObjectReader | None) -> RequestedDisplay | None:
    if fields is None:
        return None
    requested = RequestedDisplay(
        unit=fields.optional_text("unit", "símbolo da unidade de exibição"),
        significant_digits=fields.optional_number(
            "significant_digits", "inteiro de algarismos significativos"
        ),
    )
    fields.reject_unknown_fields()
    return requested
