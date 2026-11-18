from quantum_calculator.domain.run_record import EnvironmentManifest
from quantum_calculator.domain.verification import VerificationReport
from quantum_calculator.interfaces.cli.rendering.text.formatting import section


def verification_section(report: VerificationReport) -> list[str]:
    lines = []
    for check in report.checks:
        lines.append(f"{check.status.value} [{check.kind.value}] {check.identifier}")
        lines.append(f"  {check.statement}")
        lines.append(f"  observado: {check.observed}")
    lines.extend(
        f"não realizada: {skipped.identifier}. {skipped.reason}" for skipped in report.not_performed
    )
    lines.extend(f"referência: {reference}" for reference in report.references)
    return section(f"Verificação: {report.status.value}", lines)


def limitations_section(limitations: tuple[str, ...]) -> list[str]:
    return section("Limitações", list(limitations))


def environment_section(environment: EnvironmentManifest, versions: str) -> list[str]:
    dependencies = "; ".join(
        f"{dependency.name} {dependency.version}" for dependency in environment.dependencies
    )
    return section(
        "Ambiente",
        [
            f"{environment.package_name} {environment.package_version}; "
            f"{environment.python_implementation} {environment.python_version}; "
            f"{environment.platform}",
            dependencies,
            versions,
        ],
    )
