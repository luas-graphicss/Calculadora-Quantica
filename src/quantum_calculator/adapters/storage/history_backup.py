import hashlib
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime
from pathlib import Path

from quantum_calculator.adapters.storage.backup_layout import (
    MANIFEST_NAME,
    BackupFile,
    BackupManifest,
    artifact_member,
    encode_manifest,
)
from quantum_calculator.adapters.storage.data_directory import HISTORY_FILE
from quantum_calculator.domain.workbench.backups import BackupRejectedError, BackupReport

_EPOCH = (1980, 1, 1, 0, 0, 0)
_CHUNK_BYTES = 1024**2
_REFERENCED_ARTIFACTS = (
    "SELECT DISTINCT artifacts.sha256, artifacts.size FROM run_artifacts "
    "JOIN artifacts ON artifacts.sha256 = run_artifacts.sha256 ORDER BY artifacts.sha256"
)


class HistoryBackupWriter:
    def __init__(self, generator_name: str, generator_version: str) -> None:
        self._generator_name = generator_name
        self._generator_version = generator_version

    def write(self, data_directory: Path, destination: Path, created_at: datetime) -> BackupReport:
        history = data_directory / HISTORY_FILE
        if not history.is_file():
            raise BackupRejectedError(
                f"A pasta {data_directory} não tem histórico; não há o que copiar."
            )
        if destination.exists():
            raise BackupRejectedError(
                f"O arquivo {destination} já existe; a cópia não sobrescreve outro arquivo."
            )
        if not destination.parent.is_dir():
            raise BackupRejectedError(
                f"A pasta {destination.parent} não existe; a cópia não foi gravada."
            )
        with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".qcalc-backup-") as work:
            snapshot = Path(work) / HISTORY_FILE
            _snapshot(history, snapshot)
            storage_schema, runs, artifacts = _contents(snapshot)
            sources = {HISTORY_FILE: snapshot} | {
                artifact_member(sha256): data_directory / artifact_member(sha256)
                for sha256, _ in artifacts
            }
            files = [BackupFile(HISTORY_FILE, snapshot.stat().st_size, _digest(snapshot))]
            files += [_verified_artifact(sources, sha256, size) for sha256, size in artifacts]
            manifest = BackupManifest(
                generator_version=self._generator_version,
                created_at=created_at.isoformat(),
                storage_schema=storage_schema,
                runs=runs,
                files=tuple(files),
            )
            complete = Path(work) / "backup.zip"
            with zipfile.ZipFile(complete, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(
                    zipfile.ZipInfo(MANIFEST_NAME, _EPOCH),
                    encode_manifest(manifest, self._generator_name),
                )
                for file in files:
                    _store(archive, file.path, sources[file.path])
            complete.replace(destination)
        return BackupReport(runs=runs, artifacts=len(artifacts), size=destination.stat().st_size)


def _snapshot(history: Path, snapshot: Path) -> None:
    with closing(sqlite3.connect(history)) as origin, closing(sqlite3.connect(snapshot)) as copy:
        origin.backup(copy)


def _contents(snapshot: Path) -> tuple[int, int, list[tuple[str, int]]]:
    with closing(sqlite3.connect(snapshot)) as connection:
        (storage_schema,) = connection.execute("PRAGMA user_version").fetchone()
        (runs,) = connection.execute("SELECT COUNT(*) FROM runs").fetchone()
        artifacts: list[tuple[str, int]] = connection.execute(_REFERENCED_ARTIFACTS).fetchall()
    return storage_schema, runs, artifacts


def _verified_artifact(sources: dict[str, Path], sha256: str, size: int) -> BackupFile:
    member = artifact_member(sha256)
    source = sources[member]
    try:
        found = (source.stat().st_size, _digest(source))
    except FileNotFoundError as error:
        raise BackupRejectedError(
            f"O artefato {sha256} do histórico não está na pasta de dados; a cópia não foi gravada."
        ) from error
    if found != (size, sha256):
        raise BackupRejectedError(
            f"O artefato {sha256} do histórico não confere com o próprio hash; a cópia não foi "
            "gravada."
        )
    return BackupFile(member, size, sha256)


def _digest(source: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        while chunk := stream.read(_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def _store(archive: zipfile.ZipFile, member: str, source: Path) -> None:
    entry = zipfile.ZipInfo(member, _EPOCH)
    entry.compress_type = zipfile.ZIP_DEFLATED
    with source.open("rb") as stream, archive.open(entry, "w") as stored:
        shutil.copyfileobj(stream, stored, _CHUNK_BYTES)
