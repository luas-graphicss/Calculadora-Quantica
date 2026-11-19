import io
import stat
import zipfile
from collections.abc import Sequence
from pathlib import PurePosixPath

from quantum_calculator.domain.workbench.packages import PackageFile, PackageRejectedError

MAX_PACKAGE_BYTES = 64 * 1024**2

_MAX_FILES = 64
_MAX_FILE_BYTES = 32 * 1024**2
_EPOCH = (1980, 1, 1, 0, 0, 0)
_REGULAR_FILE = (stat.S_IFREG | 0o644) << 16
_ENCRYPTED = 0x1
_NOT_A_PACKAGE = "O arquivo enviado não é um pacote de reprodução: não é um ZIP legível."


class ZipPackageArchive:
    def pack(self, files: Sequence[PackageFile]) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(files, key=lambda item: item.path):
                entry = zipfile.ZipInfo(file.path, _EPOCH)
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = _REGULAR_FILE
                archive.writestr(entry, file.content)
        return buffer.getvalue()

    def unpack(self, content: bytes) -> tuple[PackageFile, ...]:
        if len(content) > MAX_PACKAGE_BYTES:
            raise PackageRejectedError(
                f"O pacote tem mais de {MAX_PACKAGE_BYTES // 1024**2} MiB e não foi aberto."
            )
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                return _read_entries(archive)
        except zipfile.BadZipFile as error:
            raise PackageRejectedError(_NOT_A_PACKAGE) from error


def _read_entries(archive: zipfile.ZipFile) -> tuple[PackageFile, ...]:
    entries = archive.infolist()
    if len(entries) > _MAX_FILES:
        raise PackageRejectedError(
            f"O pacote traz {len(entries)} arquivos; o limite é {_MAX_FILES}."
        )
    names = [entry.filename for entry in entries]
    if len(set(names)) != len(names):
        raise PackageRejectedError("O pacote traz dois arquivos com o mesmo caminho.")
    remaining = MAX_PACKAGE_BYTES
    files = []
    for entry in entries:
        _require_plain_file(entry)
        file_content = _read_within(archive, entry, min(_MAX_FILE_BYTES, remaining))
        remaining -= len(file_content)
        files.append(PackageFile(entry.filename, file_content))
    return tuple(files)


def _require_plain_file(entry: zipfile.ZipInfo) -> None:
    path = PurePosixPath(entry.filename)
    unsafe = (
        entry.is_dir()
        or path.is_absolute()
        or "\\" in entry.filename
        or ":" in entry.filename
        or any(part in ("", ".", "..") for part in entry.filename.split("/"))
    )
    if unsafe:
        raise PackageRejectedError(
            f"O pacote traz o caminho {entry.filename!r}, que sai da pasta do pacote; "
            "nada foi extraído."
        )
    if stat.S_ISLNK(entry.external_attr >> 16) or entry.flag_bits & _ENCRYPTED:
        raise PackageRejectedError(
            f"O arquivo {entry.filename} do pacote é um atalho ou está cifrado; nada foi extraído."
        )


def _read_within(archive: zipfile.ZipFile, entry: zipfile.ZipInfo, limit: int) -> bytes:
    with archive.open(entry) as stream:
        file_content = stream.read(limit + 1)
    if len(file_content) > limit:
        raise PackageRejectedError(
            f"O arquivo {entry.filename} do pacote passa do tamanho aceito; nada foi importado."
        )
    return file_content
