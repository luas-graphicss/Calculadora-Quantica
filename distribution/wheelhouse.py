import importlib.util
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from distribution.checksums import sha256_of
from distribution.documents import DistributionError

INSTALLER_GROUP = "distribution"

_PACKAGED_INTERFACE = "quantum_calculator/interfaces/api/static/index.html"
_SECONDS = 1800.0


def build_project_wheel(root: Path, wheels: Path) -> Path:
    _run([_uv(), "build", "--wheel", "--out-dir", str(wheels)], root)
    built = sorted(wheels.glob("quantum_calculator-*.whl"))
    if len(built) != 1:
        raise DistributionError(f"expected one project wheel in {wheels}, found {len(built)}")
    with zipfile.ZipFile(built[0]) as archive:
        if _PACKAGED_INTERFACE not in archive.namelist():
            raise DistributionError(
                "the wheel carries no compiled interface; run npm ci and npm run build in web/ "
                "before building the distribution"
            )
    return built[0]


def export_runtime_requirements(root: Path, destination: Path) -> None:
    _export(root, destination, "--no-dev")


def export_installer_requirements(root: Path, destination: Path) -> None:
    _export(root, destination, "--only-group", INSTALLER_GROUP)


def pin_wheel(requirements: Path, name: str, version: str, wheel: Path) -> None:
    pinned = f"{name}=={version} \\\n    --hash=sha256:{sha256_of(wheel)}\n"
    requirements.write_text(requirements.read_text("utf-8") + pinned, "utf-8")


def download_wheels(requirements: Path, destination: Path) -> None:
    if importlib.util.find_spec("pip") is None:
        raise DistributionError(
            "pip is not installed in this environment; run the build with "
            f"uv run --group {INSTALLER_GROUP} python -m distribution build"
        )
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--requirement",
            str(requirements),
            "--dest",
            str(destination),
            "--only-binary=:all:",
            "--require-hashes",
            "--no-deps",
            "--disable-pip-version-check",
            "--quiet",
        ],
        requirements.parent,
    )


def _export(root: Path, destination: Path, *selection: str) -> None:
    _run(
        [
            _uv(),
            "export",
            "--locked",
            *selection,
            "--no-emit-project",
            "--no-header",
            "--no-annotate",
            "--format",
            "requirements-txt",
            "--output-file",
            str(destination),
            "--quiet",
        ],
        root,
    )


def _uv() -> str:
    found = shutil.which("uv")
    if found is None:
        raise DistributionError("uv is not installed; the distribution is built from uv.lock")
    return found


def _run(command: list[str], working_directory: Path) -> None:
    completed = subprocess.run(  # noqa: S603 - fixed tools and arguments, no outside input
        command,
        cwd=working_directory,
        capture_output=True,
        check=False,
        encoding="utf-8",
        timeout=_SECONDS,
    )
    if completed.returncode != 0:
        raise DistributionError(
            f"{' '.join(command[:3])} ended with code {completed.returncode}: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
