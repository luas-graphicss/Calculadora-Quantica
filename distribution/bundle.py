import json
import platform
import shutil
import sys
import sysconfig
import tarfile
import tempfile
import tomllib
from datetime import datetime
from pathlib import Path

from distribution.checksums import describe_files, sha256_of, write_checksums
from distribution.documents import (
    MANIFEST_NAME,
    MANIFEST_SCHEMA,
    SCHEMA_VERSION,
    DistributionError,
    Manifest,
    Platform,
)
from distribution.inventory import render_inventory
from distribution.licenses import describe_wheels, interface_packages
from distribution.wheelhouse import (
    build_project_wheel,
    download_wheels,
    export_installer_requirements,
    export_runtime_requirements,
    pin_wheel,
)

REQUIREMENTS_NAME = "requirements.txt"
WHEELS_DIRECTORY = "wheels"
INSTALLER_DIRECTORY = "installer"
LICENSES_DIRECTORY = "licenses"
INVENTORY_NAME = "INVENTORY.md"

_INTERFACE_LOCK = "web/package-lock.json"
_COPIED_DIRECTORIES = (
    ("reference_cases", "reference_cases"),
    ("docs/guide", "docs/guide"),
    ("docs/notation", "docs/notation"),
    ("docs/release", "docs/release"),
)
_COPIED_FILES = (
    ("LICENSE", "LICENSE"),
    ("distribution/install.sh", "install.sh"),
    ("docs/evidence/phase-5/case_matrix.json", "case_matrix.json"),
    ("docs/evidence/phase-4/electron_box_1nm.package.zip", "witness/electron_box_1nm.package.zip"),
)
_QUALIFICATION_TOOL = "qualification"
_EXECUTABLE = 0o755
_READABLE_DIRECTORY = 0o755


def build_bundle(root: Path, output: Path, built_at: datetime) -> Path:
    package, version = _project(root)
    bundle = output / f"{package}-{version}-offline-{_platform_tag()}"
    if bundle.exists():
        raise DistributionError(f"{bundle} already exists; the build does not overwrite it")
    output.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{bundle.name}.", dir=output))
    try:
        _assemble(root, staging, package, version, built_at)
        staging.chmod(_READABLE_DIRECTORY)
        staging.rename(bundle)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return bundle


def archive_bundle(bundle: Path) -> tuple[Path, str]:
    archive = bundle.with_name(f"{bundle.name}.tar.gz")
    with tarfile.open(archive, "w:gz") as packed:
        packed.add(bundle, arcname=bundle.name, filter=_without_owner)
    digest = sha256_of(archive)
    archive.with_name(f"{archive.name}.sha256").write_text(f"{digest}  {archive.name}\n", "utf-8")
    return archive, digest


def _without_owner(member: tarfile.TarInfo) -> tarfile.TarInfo:
    member.uid = member.gid = 0
    member.uname = member.gname = ""
    return member


def _assemble(root: Path, bundle: Path, package: str, version: str, built_at: datetime) -> None:
    wheels = bundle / WHEELS_DIRECTORY
    installer = bundle / INSTALLER_DIRECTORY
    wheels.mkdir()
    installer.mkdir()
    project_wheel = build_project_wheel(root, wheels)
    export_runtime_requirements(root, bundle / REQUIREMENTS_NAME)
    download_wheels(bundle / REQUIREMENTS_NAME, wheels)
    pin_wheel(bundle / REQUIREMENTS_NAME, package, version, project_wheel)
    export_installer_requirements(root, installer / REQUIREMENTS_NAME)
    download_wheels(installer / REQUIREMENTS_NAME, installer)
    _copy_contents(root, bundle)
    licenses = bundle / LICENSES_DIRECTORY
    manifest = Manifest(
        schema=MANIFEST_SCHEMA,
        schema_version=SCHEMA_VERSION,
        package=package,
        version=version,
        built_at=built_at.isoformat(timespec="seconds"),
        built_on=_platform(),
        python_packages=describe_wheels(wheels, licenses),
        installer_packages=describe_wheels(installer, licenses),
        interface_packages=interface_packages(root / _INTERFACE_LOCK),
        files=[],
    )
    (licenses / INVENTORY_NAME).write_text(render_inventory(manifest), "utf-8")
    manifest["files"] = describe_files(bundle)
    (bundle / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", "utf-8"
    )
    write_checksums(bundle, manifest["files"])


def _copy_contents(root: Path, bundle: Path) -> None:
    for source, destination in _COPIED_DIRECTORIES:
        shutil.copytree(_required(root / source), bundle / destination)
    for source, destination in _COPIED_FILES:
        target = bundle / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_required(root / source), target)
    (bundle / "install.sh").chmod(_EXECUTABLE)
    tool = bundle / _QUALIFICATION_TOOL
    tool.mkdir()
    for module in sorted(_required(root / _QUALIFICATION_TOOL).glob("*.py")):
        shutil.copyfile(module, tool / module.name)


def _required(path: Path) -> Path:
    if not path.exists():
        raise DistributionError(f"{path} is missing; the distribution is not built without it")
    return path


def _project(root: Path) -> tuple[str, str]:
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    return str(project["name"]), str(project["version"])


def _platform() -> Platform:
    return Platform(
        operating_system=platform.freedesktop_os_release().get("PRETTY_NAME", platform.system()),
        architecture=platform.machine(),
        python=platform.python_version(),
        python_tag=_python_tag(),
    )


def _platform_tag() -> str:
    return f"{sysconfig.get_platform().replace('-', '_')}-{_python_tag()}"


def _python_tag() -> str:
    return f"cp{sys.version_info.major}{sys.version_info.minor}"
