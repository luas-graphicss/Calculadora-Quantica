import hashlib
import os
import re
import tempfile
from collections.abc import Collection
from pathlib import Path

from quantum_calculator.domain.workbench.artifacts import ArtifactIntegrityError, ArtifactReference

_SHA256 = re.compile(r"[0-9a-f]{64}")
_SHARD_LENGTH = 2
_PRIVATE_DIRECTORY = 0o700


class FileArtifactStore:
    def __init__(self, root: Path) -> None:
        self._root = root
        root.mkdir(mode=_PRIVATE_DIRECTORY, parents=True, exist_ok=True)

    def publish(self, content: bytes, media_type: str) -> ArtifactReference:
        digest = hashlib.sha256(content).hexdigest()
        destination = self._path(digest)
        if not destination.exists():
            destination.parent.mkdir(mode=_PRIVATE_DIRECTORY, exist_ok=True)
            _write_completely(destination, content)
        return ArtifactReference(digest, media_type, len(content))

    def read(self, reference: ArtifactReference) -> bytes:
        try:
            content = self._path(reference.sha256).read_bytes()
        except FileNotFoundError as error:
            raise ArtifactIntegrityError(reference.sha256, "the file is missing") from error
        if len(content) != reference.size:
            raise ArtifactIntegrityError(
                reference.sha256, f"expected {reference.size} bytes, found {len(content)}"
            )
        if hashlib.sha256(content).hexdigest() != reference.sha256:
            raise ArtifactIntegrityError(reference.sha256, "the content does not match its digest")
        return content

    def remove_unreferenced(self, referenced: Collection[str]) -> int:
        orphans = [
            path
            for path in self._root.glob("*/*")
            if path.is_file() and path.name not in referenced
        ]
        for orphan in orphans:
            orphan.unlink()
        return len(orphans)

    def _path(self, digest: str) -> Path:
        if _SHA256.fullmatch(digest) is None:
            raise ArtifactIntegrityError(digest, "the digest is not a SHA-256 in hexadecimal")
        return self._root / digest[:_SHARD_LENGTH] / digest


def _write_completely(destination: Path, content: bytes) -> None:
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as partial:
        partial.write(content)
        partial.flush()
        os.fsync(partial.fileno())
    Path(partial.name).replace(destination)
