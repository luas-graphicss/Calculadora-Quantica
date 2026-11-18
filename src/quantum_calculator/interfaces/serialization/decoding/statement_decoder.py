from quantum_calculator.domain.diagnostics import Diagnostic, ProblemRejectedError
from quantum_calculator.domain.problem_spec import SourceDocument
from quantum_calculator.domain.statements import StatementSpec, SymbolDeclaration
from quantum_calculator.interfaces.serialization.decoding.json_document import (
    MAX_DOCUMENT_BYTES,
    read_document,
)
from quantum_calculator.interfaces.serialization.decoding.object_reader import ObjectReader
from quantum_calculator.interfaces.serialization.decoding.schema_version import (
    decode_schema_version,
)

STATEMENT_SCHEMA_VERSION = "1.0"
STATEMENT_FIELD = "statement"

_SYMBOL_FORM = 'objeto {"role", "domain", "unit"} e, para funções, "argument"'


def decode_statement(raw: bytes) -> StatementSpec:
    return decode_statement_document(*read_document(raw))


def decode_statement_document(source: SourceDocument, content: dict[str, object]) -> StatementSpec:
    diagnostics: list[Diagnostic] = []
    document = ObjectReader(content, "", diagnostics)
    spec = StatementSpec(
        source=source,
        schema_version=decode_schema_version(document, STATEMENT_SCHEMA_VERSION),
        notation=document.text("notation", '"text" ou "latex"'),
        statement=document.text(
            STATEMENT_FIELD, "o enunciado na notação declarada", MAX_DOCUMENT_BYTES
        ),
        symbols=_decode_symbols(
            document.nested("symbols", "objeto com a declaração de cada símbolo do enunciado")
        ),
        card_identifier=document.optional_text("problem", "identificador de uma ficha do catálogo"),
        conditions=document.optional_texts(
            "conditions", "lista de condições na mesma notação do enunciado", MAX_DOCUMENT_BYTES
        ),
        candidate=document.optional_text(
            "candidate", "solução candidata na mesma notação do enunciado", MAX_DOCUMENT_BYTES
        ),
        description=document.optional_text("description", "texto livre que descreve o caso"),
    )
    document.reject_unknown_fields()
    if diagnostics:
        raise ProblemRejectedError(tuple(diagnostics))
    return spec


def _decode_symbols(fields: ObjectReader) -> tuple[SymbolDeclaration, ...]:
    return tuple(_decode_symbol(name, fields.nested(name, _SYMBOL_FORM)) for name in fields.keys)


def _decode_symbol(name: str, fields: ObjectReader) -> SymbolDeclaration:
    declaration = SymbolDeclaration(
        name=name,
        role=fields.text("role", '"variable", "parameter" ou "function"'),
        domain=fields.text("domain", "o domínio do símbolo, por exemplo real ou positive"),
        unit=fields.text("unit", 'a unidade do símbolo, ou "1" para grandeza adimensional'),
        argument=fields.optional_text("argument", "a variável de que a função depende"),
    )
    fields.reject_unknown_fields()
    return declaration
