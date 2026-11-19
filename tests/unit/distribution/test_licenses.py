import json
import zipfile
from pathlib import Path

import pytest

from distribution.checksums import sha256_of
from distribution.documents import DistributionError
from distribution.licenses import describe_wheels, interface_packages
from support.wheels import write_wheel

_BSD = "Copyright (c) NumPy Developers.\n"


def test_a_wheel_is_described_with_its_declared_license_and_its_license_files(
    tmp_path: Path,
) -> None:
    wheels = tmp_path / "bundle" / "wheels"
    wheels.mkdir(parents=True)
    wheel = write_wheel(
        wheels,
        "numpy",
        "2.5.5",
        "License-Expression: BSD-3-Clause\n",
        {"licenses/LICENSE.txt": _BSD, "RECORD": ""},
    )

    (package,) = describe_wheels(wheels, tmp_path / "bundle" / "licenses")

    assert package == {
        "name": "numpy",
        "version": "2.5.5",
        "license": "BSD-3-Clause",
        "wheel": wheel.name,
        "sha256": sha256_of(wheel),
        "license_files": ["licenses/numpy-2.5.5/LICENSE.txt"],
    }
    copied = tmp_path / "bundle" / "licenses" / "numpy-2.5.5" / "LICENSE.txt"
    assert copied.read_text("utf-8") == _BSD


def test_a_license_classifier_is_used_when_no_expression_is_declared(tmp_path: Path) -> None:
    write_wheel(
        tmp_path,
        "mpmath",
        "1.3.0",
        "Classifier: License :: OSI Approved :: BSD License\nClassifier: Topic :: Scientific\n",
    )

    (package,) = describe_wheels(tmp_path, tmp_path / "licenses")

    assert package["license"] == "BSD License"
    assert package["license_files"] == []


def test_the_first_line_of_a_free_text_license_is_reported(tmp_path: Path) -> None:
    write_wheel(tmp_path, "sympy", "1.14.0", "License: BSD\n        with a longer notice\n")

    (package,) = describe_wheels(tmp_path, tmp_path / "licenses")

    assert package["license"] == "BSD"


def test_a_wheel_that_declares_no_license_says_so(tmp_path: Path) -> None:
    write_wheel(tmp_path, "anonymous", "0.1.0", "")

    (package,) = describe_wheels(tmp_path, tmp_path / "licenses")

    assert package["license"] == "não declarada nos metadados"


def test_a_license_file_outside_the_metadata_directory_is_not_copied(tmp_path: Path) -> None:
    write_wheel(tmp_path, "vendoring", "1.0.0", "", {"../vendoring/vendor/LICENSE": _BSD})

    (package,) = describe_wheels(tmp_path, tmp_path / "licenses")

    assert package["license_files"] == []


def test_a_wheel_without_metadata_stops_the_build(tmp_path: Path) -> None:
    with zipfile.ZipFile(tmp_path / "broken-1.0.0-py3-none-any.whl", "w") as archive:
        archive.writestr("broken/__init__.py", "")

    with pytest.raises(DistributionError, match="carries no METADATA"):
        describe_wheels(tmp_path, tmp_path / "licenses")


def test_only_the_packages_compiled_into_the_interface_are_listed(tmp_path: Path) -> None:
    lock = tmp_path / "package-lock.json"
    lock.write_text(
        json.dumps(
            {
                "packages": {
                    "": {"name": "web", "version": "1.0.0"},
                    "node_modules/react": {"version": "19.2.0", "license": "MIT"},
                    "node_modules/vite": {"version": "8.0.0", "license": "MIT", "dev": True},
                    "node_modules/@scope/charts": {"version": "2.1.0"},
                    "node_modules/react/node_modules/scheduler": {
                        "version": "0.27.0",
                        "license": "MIT",
                    },
                }
            }
        ),
        "utf-8",
    )

    assert interface_packages(lock) == [
        {"name": "@scope/charts", "version": "2.1.0", "license": "não declarada nos metadados"},
        {"name": "react", "version": "19.2.0", "license": "MIT"},
        {"name": "scheduler", "version": "0.27.0", "license": "MIT"},
    ]
