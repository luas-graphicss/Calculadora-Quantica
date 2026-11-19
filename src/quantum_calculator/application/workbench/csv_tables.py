import csv
import io
from collections.abc import Sequence

from quantum_calculator.application.workbench.answers import ReportedAnswer
from quantum_calculator.domain.workbench.documents import Document, object_members, text_member

CSV_MEDIA_TYPE = "text/csv; charset=utf-8"

_ANSWER_HEADER = (
    "grandeza",
    "símbolo",
    "descrição",
    "valor",
    "unidade",
    "erro estimado",
    "origem do erro",
)


def table_csv(table: Document) -> bytes:
    columns = object_members(table, "columns")
    header = [
        f"{text_member(column, 'symbol')} [{text_member(column, 'unit')}]" for column in columns
    ]
    series = [_values(column) for column in columns]
    return _written(
        [header, *([repr(value) for value in row] for row in zip(*series, strict=True))]
    )


def answers_csv(answers: Sequence[ReportedAnswer]) -> bytes:
    rows = [
        [
            answer.name,
            answer.symbol,
            answer.label,
            answer.display,
            answer.unit,
            "" if answer.error is None else answer.error.display,
            "" if answer.error is None else answer.error.origin,
        ]
        for answer in answers
    ]
    return _written([list(_ANSWER_HEADER), *rows])


def _values(column: Document) -> Sequence[object]:
    values = column.get("values")
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise LookupError("a table column was exported before its values were attached")
    return values


def _written(rows: Sequence[Sequence[str]]) -> bytes:
    buffer = io.StringIO(newline="")
    csv.writer(buffer, lineterminator="\r\n").writerows(rows)
    return buffer.getvalue().encode("utf-8")
