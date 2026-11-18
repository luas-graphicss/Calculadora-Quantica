import platform
from importlib import metadata

from quantum_calculator.domain.run_record import DependencyVersion, EnvironmentManifest

PACKAGE_NAME = "quantum-calculator"
RUNTIME_DEPENDENCIES = ("sympy", "mpmath")


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
        )
