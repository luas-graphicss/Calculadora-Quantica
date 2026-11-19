import hashlib
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path

from quantum_calculator.adapters.storage.backup_layout import (
    MANIFEST_NAME,
    MAX_MANIFEST_BYTES,
    BackupFile,
    BackupManifest,
    decode_manifest,
)
from quantum_calculator.adapters.storage.data_directory import (
    ARTIFACTS_DIRECTORY,
    HISTORY_FILE,
    PRIVATE_DIRECTORY,
)
from quantum_calculator.adapters.storage.file_artifacts import FileArtifactStore
from quantum_calculator.adapters.storage.migrations import SCHEMA_VERSION, NewerHistoryError
from quantum_calculator.adapters.storage.sqlite_runs import SqliteRunRepository
from quantum_calculator.domain.workbench.artifacts import ArtifactIntegrityError
from quantum_calculator.domain.workbench.backups import BackupRejectedError, RestoreReport

_CHUNK_BYTES = 1024**2
_OWNER_ONLY = 0o600
_ENCRYPTED = 0x1
_NOTHING_RESTORED = "nada foi restaurado"


class HistoryBackupReader:
    def restore(self, backup: Path, data_directory: Path) -> RestoreReport:
        if not backup.is_file():
            raise BackupRejectedError(f"O arquivo {backup} não existe; {_NOTHING_RESTORED}.")
        if data_directory.exists() and any(data_directory.iterdir()):
            raise BackupRejectedError(
                f"A pasta {data_directory} já tem conteúdo; a restauração só grava em pasta nova "
                "ou vazia, para não sobrescrever uma pesquisa."
            )
        data_directory.parent.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(dir=data_directory.parent, prefix=".qcalc-restore-"))
        try:
            manifest = _extract(backup, work)
            report = _opened(work, manifest)
            if data_directory.exists():
                data_directory.rmdir()
            work.replace(data_directory)
        except BaseException:
            shutil.rmtree(work, ignore_errors=True)
            raise
        return report


def _extract(backup: Path, destination: Path) -> BackupManifest:
    try:
        with zipfile.ZipFile(backup) as archive:
            manifest = decode_manifest(_read_within(archive, MANIFEST_NAME, MAX_MANIFEST_BYTES))
            _require_declared_members(archive, manifest)
            for file in manifest.files:
                _extract_verified(archive, file, destination / file.path)
    except (zipfile.BadZipFile, KeyError) as error:
        raise BackupRejectedError(
            f"O arquivo {backup} não é uma cópia legível do histórico; {_NOTHING_RESTORED}."
        ) from error
    return manifest


def _require_declared_members(archive: zipfile.ZipFile, manifest: BackupManifest) -> None:
    declared = {MANIFEST_NAME, *(file.path for file in manifest.files)}
    entries = archive.infolist()
    names = [entry.filename for entry in entries]
    if len(names) != len(set(names)) or set(names) != declared:
        raise BackupRejectedError(
            f"Os arquivos da cópia não são os que o manifesto declara; {_NOTHING_RESTORED}."
        )
    for entry in entries:
        if (
            entry.is_dir()
            or stat.S_ISLNK(entry.external_attr >> 16)
            or entry.flag_bits & _ENCRYPTED
        ):
            raise BackupRejectedError(
                f"O arquivo {entry.filename} da cópia é uma pasta, um atalho ou está cifrado; "
                f"{_NOTHING_RESTORED}."
            )


def _extract_verified(archive: zipfile.ZipFile, file: BackupFile, destination: Path) -> None:
    destination.parent.mkdir(mode=PRIVATE_DIRECTORY, parents=True, exist_ok=True)
    digest = hashlib.sha256()
    written = 0
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, _OWNER_ONLY)
    with os.fdopen(descriptor, "wb") as restored, archive.open(file.path) as stored:
        while chunk := stored.read(min(_CHUNK_BYTES, file.size - written + 1)):
            written += len(chunk)
            if written > file.size:
                break
            digest.update(chunk)
            restored.write(chunk)
        restored.flush()
        os.fsync(restored.fileno())
    if written != file.size or digest.hexdigest() != file.sha256:
        raise BackupRejectedError(
            f"O arquivo {file.path} da cópia não confere com o tamanho e o hash do manifesto; "
            f"{_NOTHING_RESTORED}."
        )


def _opened(directory: Path, manifest: BackupManifest) -> RestoreReport:
    if manifest.storage_schema > SCHEMA_VERSION:
        raise BackupRejectedError(
            f"A cópia foi escrita com o esquema de armazenamento {manifest.storage_schema}, mais "
            f"novo que o esquema {SCHEMA_VERSION} desta versão; {_NOTHING_RESTORED}."
        )
    try:
        runs = SqliteRunRepository(directory / HISTORY_FILE).recent()
        artifacts = FileArtifactStore(directory / ARTIFACTS_DIRECTORY)
        references = {
            artifact.reference.sha256: artifact.reference
            for run in runs
            for artifact in run.artifacts
        }
        for reference in references.values():
            artifacts.read(reference)
    except (NewerHistoryError, ArtifactIntegrityError) as error:
        raise BackupRejectedError(
            f"O histórico da cópia não abre inteiro nesta versão ({error}); {_NOTHING_RESTORED}."
        ) from error
    return RestoreReport(
        runs=len(runs),
        artifacts=len(references),
        written_by=manifest.generator_version,
        storage_schema=manifest.storage_schema,
        current_storage_schema=SCHEMA_VERSION,
    )


def _read_within(archive: zipfile.ZipFile, member: str, limit: int) -> bytes:
    with archive.open(member) as stream:
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise BackupRejectedError(
            f"O arquivo {member} da cópia passa do tamanho aceito; {_NOTHING_RESTORED}."
        )
    return content
