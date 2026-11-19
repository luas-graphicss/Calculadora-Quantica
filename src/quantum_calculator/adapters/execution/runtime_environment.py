import platform
from collections.abc import Callable, Iterator
from importlib import metadata

import numpy
import scipy

from quantum_calculator.domain.run_record import (
    DependencyVersion,
    EnvironmentManifest,
    LinearAlgebraLibrary,
)

PACKAGE_NAME = "quantum-calculator"
RUNTIME_DEPENDENCIES = ("sympy", "mpmath", "numpy", "scipy", "fastapi", "uvicorn")

_BUILD_DEPENDENCIES = "Build Dependencies"
_INTERFACES = ("blas", "lapack")
_UNREPORTED = "unreported"
_CONFIGURATION_READERS: tuple[tuple[str, Callable[..., object]], ...] = (
    ("numpy", numpy.show_config),
    ("scipy", scipy.show_config),
)


class RuntimeEnvironmentProbe:
    def describe(self) -> EnvironmentManifest:
        return EnvironmentManifest(
            package_name=PACKAGE_NAME,
            package_version=metadata.version(PACKAGE_NAME),
            python_implementation=platform.python_implementation(),
            python_version=platform.python_version(),
            platform=platform.platform(),
            dependencies=tuple(
                DependencyVersion(name, metadata.version(name)) for name in RUNTIME_DEPENDENCIES
            ),
            linear_algebra=tuple(
                library
                for consumer, read_configuration in _CONFIGURATION_READERS
                for library in _linked_libraries(consumer, read_configuration(mode="dicts"))
            ),
        )


def _linked_libraries(consumer: str, configuration: object) -> Iterator[LinearAlgebraLibrary]:
    if not isinstance(configuration, dict):
        return
    dependencies = configuration.get(_BUILD_DEPENDENCIES)
    if not isinstance(dependencies, dict):
        return
    for interface in _INTERFACES:
        details = dependencies.get(interface)
        if isinstance(details, dict):
            yield LinearAlgebraLibrary(
                consumer=consumer,
                interface=interface,
                name=str(details.get("name", _UNREPORTED)),
                version=str(details.get("version", _UNREPORTED)),
            )
