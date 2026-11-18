import hashlib
import json
from dataclasses import dataclass

from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    ProblemRejectedError,
    quote_user_text,
)
from quantum_calculator.domain.problem_spec import SourceDocument

MAX_DOCUMENT_BYTES = 65_536
_DOCUMENT_EXPECTATION = "objeto JSON conforme o esquema de entrada"


@dataclass(frozen=True, slots=True)
class NumberToken:
    literal: str


class _DuplicateFieldError(ValueError):
    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


def read_document(raw: bytes) -> tuple[SourceDocument, dict[str, object]]:
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise _rejection(
            DiagnosticCode.DOCUMENT_TOO_LARGE,
            f"O documento tem mais de {MAX_DOCUMENT_BYTES} bytes.",
            f"documento de até {MAX_DOCUMENT_BYTES} bytes",
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _rejection(
            DiagnosticCode.INVALID_ENCODING,
            f"O documento não está em UTF-8: byte inválido na posição {error.start}.",
            "texto codificado em UTF-8",
        ) from error
    content = _parse(text)
    if not isinstance(content, dict):
        raise _rejection(
            DiagnosticCode.INVALID_TYPE,
            "O documento deve ser um objeto JSON.",
            _DOCUMENT_EXPECTATION,
        )
    return SourceDocument(text=text, sha256=hashlib.sha256(raw).hexdigest()), content


def _parse(text: str) -> object:
    try:
        return json.loads(
            text,
            parse_float=NumberToken,
            parse_int=NumberToken,
            parse_constant=NumberToken,
            object_pairs_hook=_unique_fields,
        )
    except json.JSONDecodeError as error:
        raise _rejection(
            DiagnosticCode.MALFORMED_JSON,
            f"JSON malformado na linha {error.lineno}, coluna {error.colno}: {error.msg}.",
            _DOCUMENT_EXPECTATION,
        ) from error
    except _DuplicateFieldError as error:
        raise _rejection(
            DiagnosticCode.DUPLICATE_FIELD,
            f"O campo {quote_user_text(error.key)} aparece mais de uma vez no mesmo objeto.",
            "cada campo uma única vez",
        ) from error
    except RecursionError as error:
        raise _rejection(
            DiagnosticCode.DOCUMENT_TOO_DEEP,
            "O documento tem níveis de aninhamento demais.",
            _DOCUMENT_EXPECTATION,
        ) from error


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    fields: dict[str, object] = {}
    for key, value in pairs:
        if key in fields:
            raise _DuplicateFieldError(key)
        fields[key] = value
    return fields


def _rejection(code: DiagnosticCode, message: str, expected: str) -> ProblemRejectedError:
    return ProblemRejectedError((Diagnostic(code, "", message, expected),))
