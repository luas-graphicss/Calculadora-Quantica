import json
import re
import zipfile
from email.message import Message
from email.parser import HeaderParser
from pathlib import Path, PurePosixPath

from distribution.checksums import sha256_of
from distribution.documents import DistributionError, InterfacePackage, PythonPackage

_LICENSE_FILE = re.compile(r"(licen[cs]e|copying|notice|authors)", re.IGNORECASE)
_LICENSE_CLASSIFIER = "License :: "
_NOT_DECLARED = "não declarada nos metadados"
_INSTALLED = "node_modules/"


def describe_wheels(wheels: Path, licenses: Path) -> list[PythonPackage]:
    return [_describe(wheel, licenses) for wheel in sorted(wheels.glob("*.whl"))]


def interface_packages(lock_file: Path) -> list[InterfacePackage]:
    lock = json.loads(lock_file.read_text("utf-8"))
    return sorted(
        (
            InterfacePackage(
                name=location.rpartition(_INSTALLED)[2],
                version=str(package["version"]),
                license=str(package.get("license", _NOT_DECLARED)),
            )
            for location, package in lock["packages"].items()
            if location.startswith(_INSTALLED) and not package.get("dev", False)
        ),
        key=lambda package: (package["name"], package["version"]),
    )


def _describe(wheel: Path, licenses: Path) -> PythonPackage:
    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(
            (
                name
                for name in archive.namelist()
                if PurePosixPath(name).match("*.dist-info/METADATA")
            ),
            None,
        )
        if metadata_name is None:
            raise DistributionError(f"{wheel.name} carries no METADATA")
        metadata = HeaderParser().parsestr(archive.read(metadata_name).decode("utf-8"))
        name, version = str(metadata["Name"]), str(metadata["Version"])
        destination = licenses / f"{name}-{version}"
        copied = []
        for member in archive.namelist():
            if _is_license_file(member, PurePosixPath(metadata_name).parent):
                destination.mkdir(parents=True, exist_ok=True)
                target = destination / PurePosixPath(member).name
                target.write_bytes(archive.read(member))
                copied.append(target.relative_to(licenses.parent).as_posix())
    return PythonPackage(
        name=name,
        version=version,
        license=_declared_license(metadata),
        wheel=wheel.name,
        sha256=sha256_of(wheel),
        license_files=sorted(copied),
    )


def _is_license_file(member: str, metadata_directory: PurePosixPath) -> bool:
    path = PurePosixPath(member)
    return (
        metadata_directory in path.parents
        and ".." not in path.parts
        and not member.endswith("/")
        and (path.parent.name == "licenses" or _LICENSE_FILE.search(path.name) is not None)
    )


def _declared_license(metadata: Message) -> str:
    expression = metadata.get("License-Expression")
    if expression:
        return str(expression)
    classifiers = [
        str(classifier).removeprefix(_LICENSE_CLASSIFIER).rpartition(" :: ")[2]
        for classifier in metadata.get_all("Classifier", [])
        if str(classifier).startswith(_LICENSE_CLASSIFIER)
    ]
    if classifiers:
        return "; ".join(classifiers)
    declared = metadata.get("License")
    return str(declared).splitlines()[0] if declared else _NOT_DECLARED
