from typing import TypedDict

MANIFEST_SCHEMA = "offline_distribution_manifest"
SCHEMA_VERSION = "1.0"
MANIFEST_NAME = "MANIFEST.json"
CHECKSUMS_NAME = "SHA256SUMS"


class DistributionError(Exception):
    pass


class BundleFile(TypedDict):
    path: str
    size: int
    sha256: str


class PythonPackage(TypedDict):
    name: str
    version: str
    license: str
    wheel: str
    sha256: str
    license_files: list[str]


class InterfacePackage(TypedDict):
    name: str
    version: str
    license: str


class Platform(TypedDict):
    operating_system: str
    architecture: str
    python: str
    python_tag: str


class Manifest(TypedDict):
    schema: str
    schema_version: str
    package: str
    version: str
    built_at: str
    built_on: Platform
    python_packages: list[PythonPackage]
    installer_packages: list[PythonPackage]
    interface_packages: list[InterfacePackage]
    files: list[BundleFile]
