import hashlib
from pathlib import Path

import pytest

from quantum_calculator.adapters.storage.file_artifacts import FileArtifactStore
from quantum_calculator.domain.workbench.artifacts import ArtifactIntegrityError, ArtifactReference

_CONTENT = b'{"document":"run_record"}'
_DIGEST = hashlib.sha256(_CONTENT).hexdigest()


@pytest.fixture
def store(tmp_path: Path) -> FileArtifactStore:
    return FileArtifactStore(tmp_path / "artifacts")


def test_content_is_published_under_its_digest_and_read_back(
    store: FileArtifactStore, tmp_path: Path
) -> None:
    reference = store.publish(_CONTENT, "application/json")

    assert reference == ArtifactReference(_DIGEST, "application/json", len(_CONTENT))
    assert (tmp_path / "artifacts" / _DIGEST[:2] / _DIGEST).read_bytes() == _CONTENT
    assert store.read(reference) == _CONTENT


def test_publishing_the_same_content_twice_keeps_one_file(
    store: FileArtifactStore, tmp_path: Path
) -> None:
    store.publish(_CONTENT, "application/json")
    store.publish(_CONTENT, "application/json")

    assert [path.name for path in (tmp_path / "artifacts").glob("*/*")] == [_DIGEST]


def test_altered_content_is_refused(store: FileArtifactStore, tmp_path: Path) -> None:
    reference = store.publish(_CONTENT, "application/json")
    (tmp_path / "artifacts" / _DIGEST[:2] / _DIGEST).write_bytes(_CONTENT.replace(b"run", b"fun"))

    with pytest.raises(ArtifactIntegrityError, match="does not match its digest"):
        store.read(reference)


def test_content_of_another_size_is_refused(store: FileArtifactStore) -> None:
    reference = store.publish(_CONTENT, "application/json")

    with pytest.raises(ArtifactIntegrityError, match="expected 3 bytes"):
        store.read(ArtifactReference(reference.sha256, reference.media_type, 3))


def test_a_missing_file_is_refused(store: FileArtifactStore) -> None:
    with pytest.raises(ArtifactIntegrityError, match="missing"):
        store.read(ArtifactReference(_DIGEST, "application/json", len(_CONTENT)))


@pytest.mark.parametrize("digest", ["../../etc/passwd", "A" * 64, "abc", ""])
def test_a_digest_that_is_not_a_sha256_never_reaches_the_file_system(
    store: FileArtifactStore, digest: str
) -> None:
    with pytest.raises(ArtifactIntegrityError, match="not a SHA-256"):
        store.read(ArtifactReference(digest, "application/json", 1))


def test_only_unreferenced_files_are_removed(store: FileArtifactStore) -> None:
    kept = store.publish(_CONTENT, "application/json")
    orphan = store.publish(b"orphan", "application/json")

    removed = store.remove_unreferenced({kept.sha256})

    assert removed == 1
    assert store.read(kept) == _CONTENT
    with pytest.raises(ArtifactIntegrityError, match="missing"):
        store.read(orphan)
