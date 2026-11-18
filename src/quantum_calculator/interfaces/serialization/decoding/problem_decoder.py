from quantum_calculator.domain.diagnostics import Diagnostic, ProblemRejectedError
from quantum_calculator.domain.problem_spec import (
    ConstantInput,
    HypothesisInput,
    ParameterContent,
    ParameterInput,
    ProblemSpec,
    QuantityInput,
    RequestedOutput,
    SourceDocument,
    UncertaintyDeclaration,
    UncertaintyInput,
)
from quantum_calculator.interfaces.serialization.decoding.json_document import read_document
from quantum_calculator.interfaces.serialization.decoding.number_literals import (
    NUMBER_EXPECTATION,
)
from quantum_calculator.interfaces.serialization.decoding.object_reader import ObjectReader
from quantum_calculator.interfaces.serialization.decoding.schema_version import (
    decode_schema_version,
)

PROBLEM_SCHEMA_VERSION = "1.0"

_QUANTITY_FORM = 'objeto {"value", "unit"}'
_PARAMETER_FORMS = f'número, {_QUANTITY_FORM} ou objeto {{"constant"}}'


def decode_problem(raw: bytes) -> ProblemSpec:
    return decode_problem_document(*read_document(raw))


def decode_problem_document(source: SourceDocument, content: dict[str, object]) -> ProblemSpec:
    diagnostics: list[Diagnostic] = []
    document = ObjectReader(content, "", diagnostics)
    spec = ProblemSpec(
        source=source,
        schema_version=decode_schema_version(document, PROBLEM_SCHEMA_VERSION),
        card_identifier=document.text("problem", "identificador de uma ficha do catálogo"),
        description=document.optional_text("description", "texto livre que descreve o caso"),
        hypotheses=_decode_hypotheses(
            document.nested("hypotheses", "objeto com as hipóteses confirmadas")
        ),
        parameters=_decode_parameters(
            document.nested("parameters", "objeto com os parâmetros do problema")
        ),
        requested=_decode_requested(
            document.nested("requested", "objeto com a grandeza pedida e a unidade de exibição")
        ),
        uncertainty=_decode_uncertainty(
            document.optional_nested(
                "uncertainty", "objeto com a hipótese de covariância e as incertezas-padrão"
            )
        ),
    )
    document.reject_unknown_fields()
    if diagnostics:
        raise ProblemRejectedError(tuple(diagnostics))
    return spec


def _decode_hypotheses(fields: ObjectReader) -> tuple[HypothesisInput, ...]:
    return tuple(
        HypothesisInput(key, fields.text(key, "texto com o valor confirmado da hipótese"))
        for key in fields.keys
    )


def _decode_parameters(fields: ObjectReader) -> tuple[ParameterInput, ...]:
    return tuple(ParameterInput(name, _decode_parameter(fields, name)) for name in fields.keys)


def _decode_parameter(fields: ObjectReader, name: str) -> ParameterContent:
    if fields.holds_object_with(name, "constant"):
        return _decode_constant(fields.nested(name, _PARAMETER_FORMS))
    if fields.holds_object(name):
        return _decode_quantity(fields.nested(name, _PARAMETER_FORMS))
    return fields.number(name, _PARAMETER_FORMS)


def _decode_constant(fields: ObjectReader) -> ConstantInput:
    constant = ConstantInput(fields.text("constant", "identificador de uma constante do catálogo"))
    fields.reject_unknown_fields()
    return constant


def _decode_quantity(fields: ObjectReader) -> QuantityInput:
    quantity = QuantityInput(
        number=fields.number("value", NUMBER_EXPECTATION),
        unit=fields.text("unit", "símbolo de uma unidade do registro"),
    )
    fields.reject_unknown_fields()
    return quantity


def _decode_requested(fields: ObjectReader) -> RequestedOutput:
    requested = RequestedOutput(
        quantity=fields.text("quantity", "nome de uma grandeza oferecida pela ficha"),
        unit=fields.text("unit", "símbolo da unidade de exibição"),
        significant_digits=fields.optional_number(
            "significant_digits", "inteiro de algarismos significativos"
        ),
    )
    fields.reject_unknown_fields()
    return requested


def _decode_uncertainty(fields: ObjectReader | None) -> UncertaintyDeclaration | None:
    if fields is None:
        return None
    entries = fields.nested(
        "standard_uncertainties", "objeto com a incerteza-padrão de cada grandeza"
    )
    declaration = UncertaintyDeclaration(
        covariance=fields.text(
            "covariance", 'hipótese de covariância declarada, por exemplo "independent"'
        ),
        standard_uncertainties=tuple(
            UncertaintyInput(name, _decode_quantity(entries.nested(name, _QUANTITY_FORM)))
            for name in entries.keys
        ),
    )
    fields.reject_unknown_fields()
    return declaration
