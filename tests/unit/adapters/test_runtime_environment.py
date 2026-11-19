import platform
import re
from importlib import metadata

from quantum_calculator.adapters.execution.runtime_environment import (
    PACKAGE_NAME,
    RuntimeEnvironmentProbe,
)


def test_manifest_describes_the_running_interpreter() -> None:
    manifest = RuntimeEnvironmentProbe().describe()

    assert manifest.package_name == "quantum-calculator"
    assert manifest.python_implementation == platform.python_implementation()
    assert manifest.python_version == platform.python_version()
    assert manifest.platform


def test_manifest_covers_every_declared_runtime_requirement() -> None:
    declared = {
        re.split(r"[^A-Za-z0-9_.-]", requirement, maxsplit=1)[0]
        for requirement in metadata.requires(PACKAGE_NAME) or []
        if "extra ==" not in requirement
    }

    manifest = RuntimeEnvironmentProbe().describe()

    recorded = {dependency.name: dependency.version for dependency in manifest.dependencies}
    assert declared <= set(recorded)
    assert all(recorded.values())


def test_manifest_names_the_blas_and_lapack_each_numerical_library_links_to() -> None:
    manifest = RuntimeEnvironmentProbe().describe()

    linked = {(library.consumer, library.interface) for library in manifest.linear_algebra}
    assert linked == {
        ("numpy", "blas"),
        ("numpy", "lapack"),
        ("scipy", "blas"),
        ("scipy", "lapack"),
    }
    assert all(library.name and library.version for library in manifest.linear_algebra)
