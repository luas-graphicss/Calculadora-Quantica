import math
import re
import struct
from collections.abc import Sequence

from quantum_calculator.domain.workbench.artifacts import ArtifactIntegrityError, ArtifactReference
from quantum_calculator.domain.workbench.documents import (
    Document,
    member,
    object_member,
    object_members,
    text_member,
)
from quantum_calculator.domain.workbench.ports import ArtifactStore
from quantum_calculator.domain.workbench.runs import RunArtifact

FLOAT64_MEDIA_TYPE = "application/vnd.quantum-calculator.float64"
TABLE_ROLE_PREFIX = "table:"

_DTYPE = "float64"
_BYTE_ORDER = "little"
_ITEM_BYTES = 8
_RESULT = "result"
_TABLES = "tables"
_COLUMNS = "columns"
_VALUES = "values"
_SAMPLES = "samples"
_NAME = "name"
_TABLE_NAME = re.compile(r"[a-z][a-z0-9_]{0,63}")
_UNKNOWN_DIGEST = "unknown"


class MalformedTableError(ValueError):
    pass


def detach_tables(
    document: Document, artifacts: ArtifactStore
) -> tuple[Document, tuple[RunArtifact, ...]]:
    result = object_member(document, _RESULT)
    tables = object_members(document, _RESULT, _TABLES)
    if result is None or not tables:
        return document, ()
    names = [_table_name(table) for table in tables]
    if len(set(names)) != len(names):
        raise MalformedTableError("two tables of the record share one name")
    detached = [_detach(table, artifacts) for table in tables]
    stored = {**document, _RESULT: {**result, _TABLES: [table for table, _ in detached]}}
    return stored, tuple(artifact for _, artifact in detached)


def attach_tables(document: Document, artifacts: ArtifactStore) -> Document:
    result = object_member(document, _RESULT)
    tables = object_members(document, _RESULT, _TABLES)
    if result is None or not tables:
        return document
    attached = [attach_table(table, artifacts) for table in tables]
    return {**document, _RESULT: {**result, _TABLES: attached}}


def attach_table(table: Document, artifacts: ArtifactStore) -> Document:
    layout = object_member(table, _SAMPLES)
    if layout is None:
        return table
    columns = object_members(table, _COLUMNS)
    series = _read_series(layout, len(columns), artifacts)
    return {
        **{key: value for key, value in table.items() if key not in (_COLUMNS, _SAMPLES)},
        _COLUMNS: [
            {**column, _VALUES: list(samples)}
            for column, samples in zip(columns, series, strict=True)
        ],
    }


def find_table(document: Document, name: str) -> Document | None:
    for table in object_members(document, _RESULT, _TABLES):
        if text_member(table, _NAME) == name:
            return table
    return None


def _detach(table: Document, artifacts: ArtifactStore) -> tuple[Document, RunArtifact]:
    columns = object_members(table, _COLUMNS)
    series = [_samples(column) for column in columns]
    rows = len(series[0]) if series else 0
    if any(len(samples) != rows for samples in series):
        raise MalformedTableError("the columns of a table have different lengths")
    flattened = [value for samples in series for value in samples]
    reference = artifacts.publish(
        struct.pack(f"<{len(flattened)}d", *flattened), FLOAT64_MEDIA_TYPE
    )
    described = {
        **{key: value for key, value in table.items() if key != _COLUMNS},
        _COLUMNS: [
            {key: value for key, value in column.items() if key != _VALUES} for column in columns
        ],
        _SAMPLES: {
            "sha256": reference.sha256,
            "dtype": _DTYPE,
            "byte_order": _BYTE_ORDER,
            "shape": [len(series), rows],
            "size": reference.size,
        },
    }
    return described, RunArtifact(f"{TABLE_ROLE_PREFIX}{_table_name(table)}", reference)


def _table_name(table: Document) -> str:
    name = text_member(table, _NAME)
    if name is None or _TABLE_NAME.fullmatch(name) is None:
        raise MalformedTableError("a table of the record has no usable name")
    return name


def _samples(column: Document) -> list[float]:
    values = column.get(_VALUES)
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise MalformedTableError("a table column has no list of values")
    return [_finite_sample(value) for value in values]


def _finite_sample(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise MalformedTableError("a table holds a value that is not a number")
    try:
        sample = float(value)
    except OverflowError as error:
        raise MalformedTableError("a table holds a number outside double precision") from error
    if not math.isfinite(sample):
        raise MalformedTableError("a table holds a non-finite number")
    return sample


def _read_series(
    layout: Document, column_count: int, artifacts: ArtifactStore
) -> list[tuple[float, ...]]:
    digest = text_member(layout, "sha256") or _UNKNOWN_DIGEST
    shape = member(layout, "shape")
    size = member(layout, "size")
    if layout.get("dtype") != _DTYPE or layout.get("byte_order") != _BYTE_ORDER:
        raise ArtifactIntegrityError(digest, "the array is not little-endian float64")
    if (
        not isinstance(shape, Sequence)
        or len(shape) != 2
        or not all(_is_count(extent) for extent in shape)
        or shape[0] != column_count
    ):
        raise ArtifactIntegrityError(digest, "the array shape does not match the table columns")
    rows: int = shape[1]
    if size != column_count * rows * _ITEM_BYTES:
        raise ArtifactIntegrityError(digest, "the array size does not match its shape")
    content = artifacts.read(ArtifactReference(digest, FLOAT64_MEDIA_TYPE, size))
    flattened = struct.unpack(f"<{column_count * rows}d", content)
    return [flattened[index * rows : (index + 1) * rows] for index in range(column_count)]


def _is_count(extent: object) -> bool:
    return isinstance(extent, int) and not isinstance(extent, bool) and extent >= 0
