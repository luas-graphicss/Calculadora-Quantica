import json
import re
from dataclasses import dataclass
from datetime import datetime

from quantum_calculator.adapters.storage.data_directory import ARTIFACTS_DIRECTORY, HISTORY_FILE
from quantum_calculator.domain.workbench.backups import BackupRejectedError

MANIFEST_NAME = "manifest.json"
MAX_MANIFEST_BYTES = 64 * 1024**2

_SCHEMA = "history_backup"
_SCHEMA_VERSION = "1.0"
_ARTIFACT_MEMBER = re.compile(rf"{ARTIFACTS_DIRECTORY}/([0-9a-f]{{2}})/([0-9a-f]{{64}})")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_NOT_A_BACKUP = "O arquivo não é uma cópia do histórico da Calculadora Quântica."


@dataclass(frozen=True, slots=True)
class BackupFile:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class BackupManifest:
    generator_version: str
    created_at: str
    storage_schema: int
    runs: int
    files: tuple[BackupFile, ...]


def artifact_member(sha256: str) -> str:
    return f"{ARTIFACTS_DIRECTORY}/{sha256[:2]}/{sha256}"


def encode_manifest(manifest: BackupManifest, generator_name: str) -> bytes:
    document = {
        "schema": _SCHEMA,
        "schema_version": _SCHEMA_VERSION,
        "generator": {"name": generator_name, "version": manifest.generator_version},
        "created_at": manifest.created_at,
        "storage_schema_version": manifest.storage_schema,
        "runs": manifest.runs,
        "files": [
            {"path": file.path, "size": file.size, "sha256": file.sha256} for file in manifest.files
        ],
    }
    return json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8")


def decode_manifest(content: bytes) -> BackupManifest:
    try:
        document = json.loads(content)
        if (document["schema"], document["schema_version"]) != (_SCHEMA, _SCHEMA_VERSION):
            raise BackupRejectedError(
                f"A cópia declara o formato {document['schema']} {document['schema_version']}; "
                f"esta versão lê {_SCHEMA} {_SCHEMA_VERSION}."
            )
        manifest = BackupManifest(
            generator_version=_text(document["generator"]["version"]),
            created_at=datetime.fromisoformat(_text(document["created_at"])).isoformat(),
            storage_schema=_count(document["storage_schema_version"]),
            runs=_count(document["runs"]),
            files=tuple(
                BackupFile(_text(file["path"]), _count(file["size"]), _text(file["sha256"]))
                for file in document["files"]
            ),
        )
    except (ValueError, KeyError, TypeError) as error:
        raise BackupRejectedError(_NOT_A_BACKUP) from error
    _require_history_layout(manifest)
    return manifest


def _require_history_layout(manifest: BackupManifest) -> None:
    paths = [file.path for file in manifest.files]
    if len(set(paths)) != len(paths) or paths.count(HISTORY_FILE) != 1:
        raise BackupRejectedError(
            "A cópia não traz exatamente um histórico ou repete um caminho; nada foi restaurado."
        )
    for file in manifest.files:
        member = _ARTIFACT_MEMBER.fullmatch(file.path)
        is_artifact = (
            member is not None
            and member.group(2) == file.sha256
            and member.group(1) == file.sha256[:2]
        )
        is_history = file.path == HISTORY_FILE and _SHA256.fullmatch(file.sha256) is not None
        if not is_artifact and not is_history:
            raise BackupRejectedError(
                f"A cópia traz o caminho {file.path!r}, que não é do histórico nem de um "
                "artefato nomeado pelo próprio hash; nada foi restaurado."
            )


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("expected text")
    return value


def _count(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise TypeError("expected a non-negative integer")
    return value
