from distribution.documents import (
    MANIFEST_SCHEMA,
    SCHEMA_VERSION,
    InterfacePackage,
    Manifest,
    Platform,
    PythonPackage,
)
from distribution.inventory import render_inventory

_SHA256 = "ab" * 32


def _package(name: str, version: str, license_name: str) -> PythonPackage:
    return PythonPackage(
        name=name,
        version=version,
        license=license_name,
        wheel=f"{name}-{version}-py3-none-any.whl",
        sha256=_SHA256,
        license_files=[],
    )


def _manifest() -> Manifest:
    return Manifest(
        schema=MANIFEST_SCHEMA,
        schema_version=SCHEMA_VERSION,
        package="quantum-calculator",
        version="1.0.0rc1",
        built_at="2026-11-19T12:00:00+00:00",
        built_on=Platform(
            operating_system="Ubuntu 24.04.3 LTS",
            architecture="x86_64",
            python="3.12.15",
            python_tag="cp312",
        ),
        python_packages=[_package("numpy", "2.5.5", "BSD-3-Clause")],
        installer_packages=[_package("pip", "26.3", "MIT")],
        interface_packages=[InterfacePackage(name="react", version="19.2.0", license="MIT")],
        files=[],
    )


def test_the_inventory_names_the_version_and_the_platform_it_was_built_for() -> None:
    inventory = render_inventory(_manifest())

    assert "`quantum-calculator` 1.0.0rc1" in inventory
    assert "Ubuntu 24.04.3 LTS, x86_64, CPython 3.12.15" in inventory


def test_every_python_package_has_its_version_license_wheel_and_digest() -> None:
    inventory = render_inventory(_manifest())

    assert (
        "| [numpy](https://pypi.org/project/numpy/2.5.5/) | 2.5.5 | BSD-3-Clause | "
        f"`numpy-2.5.5-py3-none-any.whl` | `{_SHA256}` |"
    ) in inventory


def test_the_installer_and_the_interface_packages_are_listed_apart() -> None:
    sections = render_inventory(_manifest()).split("\n## ")

    assert [section.splitlines()[0] for section in sections[1:]] == [
        "Pacotes Python instalados",
        "Ferramenta de instalação",
        "Pacotes compilados na interface",
    ]
    assert "pip" in sections[2]
    assert "numpy" not in sections[2]
    assert "| `react` | 19.2.0 | MIT |" in sections[3]
