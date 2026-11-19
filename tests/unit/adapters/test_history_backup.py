import sqlite3
import stat
import zipfile
from contextlib import closing
from pathlib import Path

import pytest

from quantum_calculator.adapters.storage.file_artifacts import FileArtifactStore
from quantum_calculator.adapters.storage.history_restore import HistoryBackupReader
from quantum_calculator.adapters.storage.migrations import SCHEMA_VERSION
from quantum_calculator.adapters.storage.sqlite_runs import SqliteRunRepository
from quantum_calculator.application.workbench.read_history import ReadHistory
from quantum_calculator.application.workbench.recover_history import RecoverHistory
from quantum_calculator.application.workbench.submit_run import Submission
from quantum_calculator.domain.workbench.backups import BackupRejectedError
from quantum_calculator.domain.workbench.runs import ArtifactRole, RunState
from support.history import (
    HISTORY,
    MANIFEST,
    WRITTEN_BY,
    Members,
    back_up,
    recorded_history,
    rewritten,
    with_manifest,
)
from support.workbench import RECORD, SOURCE, SteppingClock, build_bench


def _artifact_file(directory: Path, sha256: str) -> Path:
    return directory / "artifacts" / sha256[:2] / sha256


def _restore_leftovers(directory: Path) -> list[str]:
    return sorted(path.name for path in directory.iterdir() if path.name.startswith(".qcalc-"))


def test_a_restored_history_has_the_same_runs_records_and_provenance(tmp_path: Path) -> None:
    origin = recorded_history(tmp_path / "origin")
    archive = tmp_path / "history.zip"

    written = back_up(tmp_path / "origin", archive)
    restored = HistoryBackupReader().restore(archive, tmp_path / "restored")

    runs = SqliteRunRepository(tmp_path / "restored" / HISTORY)
    history = ReadHistory(runs, FileArtifactStore(tmp_path / "restored" / "artifacts"))
    assert runs.recent() == origin.runs.recent()
    assert [history.complete_outcome(run.identifier) for run in runs.recent()] == [RECORD, RECORD]
    assert written.runs == restored.runs == 2
    assert written.artifacts == restored.artifacts == len(origin.runs.referenced_artifacts())
    assert written.size == archive.stat().st_size
    assert (restored.written_by, restored.storage_schema, restored.current_storage_schema) == (
        WRITTEN_BY,
        SCHEMA_VERSION,
        SCHEMA_VERSION,
    )


def test_the_same_history_is_always_copied_to_the_same_bytes(tmp_path: Path) -> None:
    recorded_history(tmp_path / "origin")

    back_up(tmp_path / "origin", tmp_path / "first.zip")
    back_up(tmp_path / "origin", tmp_path / "second.zip")

    with (
        zipfile.ZipFile(tmp_path / "first.zip") as first,
        zipfile.ZipFile(tmp_path / "second.zip") as second,
    ):
        assert first.namelist() == second.namelist()
        assert first.read(MANIFEST) == second.read(MANIFEST)


def test_the_restored_directory_is_readable_by_its_owner_only(tmp_path: Path) -> None:
    recorded_history(tmp_path / "origin")
    back_up(tmp_path / "origin", tmp_path / "history.zip")

    HistoryBackupReader().restore(tmp_path / "history.zip", tmp_path / "restored")

    restored = tmp_path / "restored"
    assert stat.S_IMODE(restored.stat().st_mode) == 0o700
    assert stat.S_IMODE((restored / HISTORY).stat().st_mode) == 0o600
    assert _restore_leftovers(tmp_path) == []


def test_runs_that_were_waiting_when_copied_come_back_interrupted(tmp_path: Path) -> None:
    bench = build_bench(tmp_path / "origin")
    waiting = bench.submit.execute(Submission(SOURCE, "submission-key-0001", wall_seconds=30.0))
    back_up(tmp_path / "origin", tmp_path / "history.zip")

    HistoryBackupReader().restore(tmp_path / "history.zip", tmp_path / "restored")

    runs = SqliteRunRepository(tmp_path / "restored" / HISTORY)
    artifacts = FileArtifactStore(tmp_path / "restored" / "artifacts")
    report = RecoverHistory(runs, artifacts, SteppingClock()).execute()
    restored = runs.find(waiting.run.identifier)
    assert report.interrupted_runs == 1
    assert restored is not None
    assert restored.state is RunState.INTERRUPTED


def test_files_left_without_a_record_stay_out_of_the_copy(tmp_path: Path) -> None:
    origin = recorded_history(tmp_path / "origin")
    orphan = origin.artifacts.publish(b"published before a transaction that never committed", "x")

    written = back_up(tmp_path / "origin", tmp_path / "history.zip")

    with zipfile.ZipFile(tmp_path / "history.zip") as archive:
        assert not any(orphan.sha256 in name for name in archive.namelist())
    assert written.artifacts == len(origin.runs.referenced_artifacts())


def test_a_copy_does_not_replace_a_file_that_already_exists(tmp_path: Path) -> None:
    recorded_history(tmp_path / "origin")
    occupied = tmp_path / "history.zip"
    occupied.write_bytes(b"another file")

    with pytest.raises(BackupRejectedError, match="já existe"):
        back_up(tmp_path / "origin", occupied)

    assert occupied.read_bytes() == b"another file"


def test_a_directory_without_a_history_has_nothing_to_copy(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()

    with pytest.raises(BackupRejectedError, match="não tem histórico"):
        back_up(tmp_path / "empty", tmp_path / "history.zip")


def test_a_copy_into_a_missing_folder_is_refused(tmp_path: Path) -> None:
    recorded_history(tmp_path / "origin")

    with pytest.raises(BackupRejectedError, match="não existe"):
        back_up(tmp_path / "origin", tmp_path / "missing" / "history.zip")


@pytest.mark.parametrize("damage", ["corrupted", "missing"])
def test_a_history_with_a_damaged_artifact_is_not_copied(tmp_path: Path, damage: str) -> None:
    origin = recorded_history(tmp_path / "origin")
    outcome = origin.runs.recent()[0].require_artifact(ArtifactRole.OUTCOME)
    stored = _artifact_file(tmp_path / "origin", outcome.sha256)
    if damage == "corrupted":
        stored.write_bytes(stored.read_bytes()[:-1] + b"!")
    else:
        stored.unlink()

    with pytest.raises(BackupRejectedError, match=outcome.sha256):
        back_up(tmp_path / "origin", tmp_path / "history.zip")

    assert not (tmp_path / "history.zip").exists()
    assert _restore_leftovers(tmp_path) == []


def test_restoring_over_existing_research_is_refused(tmp_path: Path) -> None:
    recorded_history(tmp_path / "origin")
    back_up(tmp_path / "origin", tmp_path / "history.zip")
    research = recorded_history(tmp_path / "research").runs.recent()

    with pytest.raises(BackupRejectedError, match="já tem conteúdo"):
        HistoryBackupReader().restore(tmp_path / "history.zip", tmp_path / "research")

    assert SqliteRunRepository(tmp_path / "research" / HISTORY).recent() == research


def test_restoring_into_an_empty_directory_is_accepted(tmp_path: Path) -> None:
    recorded_history(tmp_path / "origin")
    back_up(tmp_path / "origin", tmp_path / "history.zip")
    (tmp_path / "restored").mkdir()

    report = HistoryBackupReader().restore(tmp_path / "history.zip", tmp_path / "restored")

    assert report.runs == 2


def _tampered_artifact(members: Members) -> None:
    artifact = next(name for name in members if name.startswith("artifacts/"))
    members[artifact] = members[artifact][:-1] + b"!"


def _undeclared_file(members: Members) -> None:
    members["artifacts/notes.txt"] = b"not declared by the manifest"


def _path_outside_the_history(members: Members) -> None:
    def declare(manifest: dict[str, object]) -> None:
        files = manifest["files"]
        assert isinstance(files, list)
        files.append({"path": "../outside.txt", "size": 1, "sha256": "0" * 64})

    with_manifest(members, declare)
    members["../outside.txt"] = b"x"


def _newer_storage_schema(members: Members) -> None:
    with_manifest(
        members, lambda manifest: manifest.update(storage_schema_version=SCHEMA_VERSION + 1)
    )


def _another_format(members: Members) -> None:
    with_manifest(members, lambda manifest: manifest.update(schema_version="2.0"))


def _without_manifest(members: Members) -> None:
    del members[MANIFEST]


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (_tampered_artifact, "não confere com o tamanho e o hash do manifesto"),
        (_undeclared_file, "não são os que o manifesto declara"),
        (_path_outside_the_history, "não é do histórico nem de um artefato"),
        (_newer_storage_schema, "mais novo que o esquema"),
        (_another_format, "declara o formato history_backup 2.0"),
        (_without_manifest, "não é uma cópia legível"),
    ],
)
def test_a_copy_that_was_changed_is_refused_and_nothing_is_restored(
    tmp_path: Path, change: object, reason: str
) -> None:
    recorded_history(tmp_path / "origin")
    back_up(tmp_path / "origin", tmp_path / "history.zip")
    assert callable(change)
    changed = rewritten(tmp_path / "history.zip", tmp_path / "changed.zip", change)

    with pytest.raises(BackupRejectedError, match=reason):
        HistoryBackupReader().restore(changed, tmp_path / "restored")

    assert not (tmp_path / "restored").exists()
    assert _restore_leftovers(tmp_path) == []
    assert not (tmp_path.parent / "outside.txt").exists()


def test_a_history_written_by_a_newer_storage_schema_is_refused(tmp_path: Path) -> None:
    recorded_history(tmp_path / "origin")
    with closing(sqlite3.connect(tmp_path / "origin" / HISTORY)) as connection:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1:d}")
    back_up(tmp_path / "origin", tmp_path / "history.zip")

    with pytest.raises(BackupRejectedError, match="mais novo"):
        HistoryBackupReader().restore(tmp_path / "history.zip", tmp_path / "restored")

    assert not (tmp_path / "restored").exists()


def test_a_symbolic_link_in_the_copy_is_refused(tmp_path: Path) -> None:
    recorded_history(tmp_path / "origin")
    back_up(tmp_path / "origin", tmp_path / "history.zip")
    with zipfile.ZipFile(tmp_path / "history.zip") as source:
        members = {name: source.read(name) for name in source.namelist()}
    with zipfile.ZipFile(tmp_path / "linked.zip", "w") as target:
        for name, content in members.items():
            entry = zipfile.ZipInfo(name)
            if name == HISTORY:
                entry.external_attr = (stat.S_IFLNK | 0o777) << 16
            target.writestr(entry, content)

    with pytest.raises(BackupRejectedError, match="atalho"):
        HistoryBackupReader().restore(tmp_path / "linked.zip", tmp_path / "restored")

    assert not (tmp_path / "restored").exists()


def test_content_that_is_not_a_copy_is_refused(tmp_path: Path) -> None:
    (tmp_path / "notes.zip").write_bytes(b"not an archive")

    with pytest.raises(BackupRejectedError, match="não é uma cópia legível"):
        HistoryBackupReader().restore(tmp_path / "notes.zip", tmp_path / "restored")


def test_a_missing_copy_is_refused(tmp_path: Path) -> None:
    with pytest.raises(BackupRejectedError, match="não existe"):
        HistoryBackupReader().restore(tmp_path / "history.zip", tmp_path / "restored")
