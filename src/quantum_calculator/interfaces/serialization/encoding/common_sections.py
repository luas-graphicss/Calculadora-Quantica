from quantum_calculator.domain.problem_spec import ProblemSpec
from quantum_calculator.domain.run_record import EnvironmentManifest
from quantum_calculator.domain.statements import StatementSpec
from quantum_calculator.domain.verification import VerificationReport
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject

OUTPUT_SCHEMA_VERSION = "1.1"


def document_header(document: str) -> JsonObject:
    return {"document": document, "schema_version": OUTPUT_SCHEMA_VERSION}


def encode_input(spec: ProblemSpec | StatementSpec) -> JsonObject:
    return {
        "sha256": spec.source.sha256,
        "schema_version": spec.schema_version,
        "description": spec.description,
        "text": spec.source.text,
    }


def encode_verification(report: VerificationReport) -> JsonObject:
    return {
        "status": report.status.value,
        "checks": [
            {
                "identifier": check.identifier,
                "kind": check.kind.value,
                "status": check.status.value,
                "statement": check.statement,
                "observed": check.observed,
            }
            for check in report.checks
        ],
        "not_performed": [
            {"identifier": skipped.identifier, "reason": skipped.reason}
            for skipped in report.not_performed
        ],
        "references": list(report.references),
    }


def encode_environment(manifest: EnvironmentManifest) -> JsonObject:
    return {
        "package": {"name": manifest.package_name, "version": manifest.package_version},
        "python": {
            "implementation": manifest.python_implementation,
            "version": manifest.python_version,
        },
        "platform": manifest.platform,
        "dependencies": [
            {"name": dependency.name, "version": dependency.version}
            for dependency in manifest.dependencies
        ],
        "linear_algebra": [
            {
                "consumer": library.consumer,
                "interface": library.interface,
                "name": library.name,
                "version": library.version,
            }
            for library in manifest.linear_algebra
        ],
    }
