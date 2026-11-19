import hashlib
from pathlib import Path

from distribution.documents import CHECKSUMS_NAME, MANIFEST_NAME, BundleFile

_CHUNK_BYTES = 1024**2


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def describe_files(bundle: Path) -> list[BundleFile]:
    return [
        BundleFile(
            path=path.relative_to(bundle).as_posix(),
            size=path.stat().st_size,
            sha256=sha256_of(path),
        )
        for path in sorted(bundle.rglob("*"))
        if path.is_file() and path.name not in (MANIFEST_NAME, CHECKSUMS_NAME)
    ]


def write_checksums(bundle: Path, files: list[BundleFile]) -> None:
    lines = [f"{file['sha256']}  {file['path']}" for file in files]
    lines.append(f"{sha256_of(bundle / MANIFEST_NAME)}  {MANIFEST_NAME}")
    (bundle / CHECKSUMS_NAME).write_text("\n".join(lines) + "\n", "utf-8")


def changed_files(bundle: Path) -> list[str]:
    changed = []
    for line in (bundle / CHECKSUMS_NAME).read_text("utf-8").splitlines():
        recorded, _, relative = line.partition("  ")
        path = bundle / relative
        if not path.is_file() or sha256_of(path) != recorded:
            changed.append(relative)
    return changed
