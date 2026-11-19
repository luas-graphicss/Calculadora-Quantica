import json

from quantum_calculator.domain.workbench.documents import Document

_INPUT_SECTION = "input"


class MalformedDocumentError(ValueError):
    pass


def canonical_json(document: Document) -> bytes:
    return json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def parse_document(content: bytes) -> Document:
    try:
        parsed = json.loads(content, parse_constant=_refuse_non_finite)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MalformedDocumentError("the content is not a JSON document") from error
    if not isinstance(parsed, dict):
        raise MalformedDocumentError("the JSON document is not an object")
    return parsed


def canonical_problem(interpretation: Document) -> Document:
    return {key: value for key, value in interpretation.items() if key != _INPUT_SECTION}


def _refuse_non_finite(literal: str) -> float:
    raise MalformedDocumentError(f"the JSON document holds the non-finite number {literal}")
