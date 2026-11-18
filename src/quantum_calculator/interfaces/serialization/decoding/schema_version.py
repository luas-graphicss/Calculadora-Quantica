from quantum_calculator.domain.diagnostics import DiagnosticCode, quote_user_text
from quantum_calculator.interfaces.serialization.decoding.object_reader import ObjectReader

_FIELD = "schema_version"


def decode_schema_version(document: ObjectReader, supported: str) -> str:
    expected = f'"{supported}"'
    version = document.text(_FIELD, expected)
    if version and version != supported:
        document.report(
            DiagnosticCode.UNSUPPORTED_SCHEMA_VERSION,
            _FIELD,
            f"A versão {quote_user_text(version)} do esquema de entrada não é suportada.",
            expected,
        )
    return version
