import json
from pathlib import Path

from quantum_calculator.domain.statements import StatementSpec
from support.statements import statement_document, statement_spec

CORPUS = json.loads(
    (
        Path(__file__).resolve().parents[2] / "reference_cases" / "notation" / "corpus.json"
    ).read_text("utf-8")
)
ITEMS: list[dict[str, object]] = CORPUS["items"]
ACCEPTED = "accepted"

_OPTIONAL_FIELDS = ("problem", "conditions", "candidate")


def expected_of(item: dict[str, object]) -> dict[str, str]:
    expected = item["expected"]
    assert isinstance(expected, dict)
    return expected


def corpus_spec(item: dict[str, object]) -> StatementSpec:
    return statement_spec(
        str(item["statement"]),
        CORPUS["symbol_sets"][item["symbols"]],
        str(item["notation"]),
        **_given_fields(item),
    )


def corpus_document(item: dict[str, object]) -> bytes:
    return statement_document(
        str(item["statement"]),
        CORPUS["symbol_sets"][item["symbols"]],
        str(item["notation"]),
        **_given_fields(item),
    )


def _given_fields(item: dict[str, object]) -> dict[str, object]:
    return {field: item[field] for field in _OPTIONAL_FIELDS if field in item}
