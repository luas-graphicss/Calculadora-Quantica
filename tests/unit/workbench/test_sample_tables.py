from pathlib import Path

import pytest

from quantum_calculator.adapters.storage.file_artifacts import FileArtifactStore
from quantum_calculator.application.workbench.sample_tables import (
    FLOAT64_MEDIA_TYPE,
    MalformedTableError,
    attach_tables,
    detach_tables,
)
from quantum_calculator.domain.workbench.artifacts import ArtifactIntegrityError
from quantum_calculator.domain.workbench.documents import (
    Document,
    object_member,
    object_members,
)
from support.workbench import RECORD


@pytest.fixture
def artifacts(tmp_path: Path) -> FileArtifactStore:
    return FileArtifactStore(tmp_path / "artifacts")


def _with_column_values(values: list[object]) -> Document:
    return {
        "result": {
            "tables": [
                {
                    "name": "series",
                    "columns": [{"name": "x", "symbol": "x", "unit": "1", "values": values}],
                }
            ]
        }
    }


def test_detached_tables_are_restored_to_the_same_record(artifacts: FileArtifactStore) -> None:
    stored, published = detach_tables(RECORD, artifacts)

    assert attach_tables(stored, artifacts) == RECORD
    assert [artifact.role for artifact in published] == ["table:eigenfunctions"]


def test_a_detached_table_keeps_type_shape_size_and_digest_instead_of_values(
    artifacts: FileArtifactStore,
) -> None:
    stored, published = detach_tables(RECORD, artifacts)

    (table,) = object_members(stored, "result", "tables")
    reference = published[0].reference
    assert all("values" not in column for column in object_members(table, "columns"))
    assert table["samples"] == {
        "sha256": reference.sha256,
        "dtype": "float64",
        "byte_order": "little",
        "shape": [2, 3],
        "size": 48,
    }
    assert reference.media_type == FLOAT64_MEDIA_TYPE


def test_a_record_without_tables_is_stored_as_it_is(artifacts: FileArtifactStore) -> None:
    record: Document = {"document": "run_record", "result": {"value": {"decimal": "1"}}}

    assert detach_tables(record, artifacts) == (record, ())


def test_an_altered_array_is_refused_when_the_table_is_read(
    artifacts: FileArtifactStore, tmp_path: Path
) -> None:
    stored, published = detach_tables(RECORD, artifacts)
    digest = published[0].reference.sha256
    (tmp_path / "artifacts" / digest[:2] / digest).write_bytes(bytes(48))

    with pytest.raises(ArtifactIntegrityError):
        attach_tables(stored, artifacts)


def test_a_declared_shape_that_disagrees_with_the_size_is_refused(
    artifacts: FileArtifactStore,
) -> None:
    stored, _ = detach_tables(RECORD, artifacts)
    (table,) = object_members(stored, "result", "tables")
    layout = object_member(table, "samples")
    assert layout is not None
    reshaped = {**table, "samples": {**layout, "shape": [2, 4]}}

    with pytest.raises(ArtifactIntegrityError):
        attach_tables({"result": {"tables": [reshaped]}}, artifacts)


@pytest.mark.parametrize("value", ["1.0", True, None, float("nan"), float("inf"), 10**400])
def test_a_value_that_is_not_a_finite_number_is_refused(
    artifacts: FileArtifactStore, value: object
) -> None:
    with pytest.raises(MalformedTableError):
        detach_tables(_with_column_values([0.0, value]), artifacts)


def test_columns_of_different_lengths_are_refused(artifacts: FileArtifactStore) -> None:
    uneven: Document = {
        "result": {
            "tables": [
                {
                    "name": "series",
                    "columns": [
                        {"name": "x", "values": [0.0, 1.0]},
                        {"name": "y", "values": [0.0]},
                    ],
                }
            ]
        }
    }

    with pytest.raises(MalformedTableError):
        detach_tables(uneven, artifacts)


@pytest.mark.parametrize("name", ["../escape", "Upper", "", "with space"])
def test_a_table_name_that_cannot_be_a_path_segment_is_refused(
    artifacts: FileArtifactStore, name: str
) -> None:
    unnamed: Document = {"result": {"tables": [{"name": name, "columns": []}]}}

    with pytest.raises(MalformedTableError):
        detach_tables(unnamed, artifacts)
