import io
import stat
import zipfile

import pytest

from quantum_calculator.adapters.storage.zip_packages import MAX_PACKAGE_BYTES, ZipPackageArchive
from quantum_calculator.domain.workbench.packages import PackageFile, PackageRejectedError

_FILES = (
    PackageFile("manifest.json", b'{"document":"reproduction_package"}'),
    PackageFile("input.json", b'{"schema_version":"1.0"}'),
    PackageFile("tables/eigenfunctions.csv", b"x [m]\r\n0.0\r\n"),
)


def _archive_with(name: str, content: bytes = b"content") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, content)
    return buffer.getvalue()


def test_a_package_is_read_back_with_the_files_it_was_written_with() -> None:
    archive = ZipPackageArchive()

    unpacked = archive.unpack(archive.pack(_FILES))

    assert sorted(unpacked, key=lambda file: file.path) == sorted(
        _FILES, key=lambda file: file.path
    )


def test_the_same_files_always_produce_the_same_bytes() -> None:
    archive = ZipPackageArchive()

    assert archive.pack(_FILES) == archive.pack(tuple(reversed(_FILES)))


@pytest.mark.parametrize(
    "name",
    [
        "../outside.json",
        "/etc/passwd",
        "tables/../../outside.csv",
        "C:/Users/someone/file.json",
        "tables\\file.csv",
        "./input.json",
        "folder/",
    ],
)
def test_a_path_that_leaves_the_package_is_refused(name: str) -> None:
    with pytest.raises(PackageRejectedError, match="sai da pasta do pacote"):
        ZipPackageArchive().unpack(_archive_with(name))


def test_a_symbolic_link_is_refused() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        link = zipfile.ZipInfo("input.json")
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link, "/etc/passwd")

    with pytest.raises(PackageRejectedError, match="atalho"):
        ZipPackageArchive().unpack(buffer.getvalue())


def test_a_file_that_expands_beyond_the_limit_is_refused() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("input.json", bytes(40 * 1024**2))

    with pytest.raises(PackageRejectedError, match="passa do tamanho aceito"):
        ZipPackageArchive().unpack(buffer.getvalue())


def test_an_archive_larger_than_the_limit_is_not_opened() -> None:
    with pytest.raises(PackageRejectedError, match="não foi aberto"):
        ZipPackageArchive().unpack(bytes(MAX_PACKAGE_BYTES + 1))


def test_too_many_files_are_refused() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for index in range(65):
            archive.writestr(f"file-{index}.json", b"{}")

    with pytest.raises(PackageRejectedError, match="65 arquivos"):
        ZipPackageArchive().unpack(buffer.getvalue())


def test_content_that_is_not_an_archive_is_refused() -> None:
    with pytest.raises(PackageRejectedError, match="não é um ZIP"):
        ZipPackageArchive().unpack(b"not an archive")
