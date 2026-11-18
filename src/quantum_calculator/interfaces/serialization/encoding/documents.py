from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.problem_spec import ProblemSpec
from quantum_calculator.domain.rounding import ROUNDING_MODE
from quantum_calculator.domain.run_record import EnvironmentManifest, RunRecord
from quantum_calculator.domain.solution import SolvePlan
from quantum_calculator.domain.validated_problem import ValidatedProblem
from quantum_calculator.domain.verification import VerificationReport
from quantum_calculator.interfaces.serialization.encoding.exact_values import (
    JsonObject,
    QuantityEncoder,
    encode_exact,
)
from quantum_calculator.interfaces.serialization.encoding.problem_encoding import ProblemEncoder
from quantum_calculator.interfaces.serialization.encoding.result_encoding import ResultEncoder

OUTPUT_SCHEMA_VERSION = "1.0"


class DocumentEncoder:
    def __init__(self, units: UnitRegistry) -> None:
        self._quantities = QuantityEncoder(units)
        self._problems = ProblemEncoder(self._quantities)
        self._results = ResultEncoder(self._quantities)

    def validation(self, problem: ValidatedProblem, plan: SolvePlan) -> JsonObject:
        return {
            **_header("validation"),
            "input": _encode_input(problem.spec),
            "problem": self._problems.encode(problem),
            "plan": _encode_plan(plan),
        }

    def run_record(self, record: RunRecord) -> JsonObject:
        return {
            **_header("run_record"),
            "input": _encode_input(record.problem.spec),
            "problem": self._problems.encode(record.problem),
            "plan": _encode_plan(record.plan),
            "constants": {
                "edition": record.constants_edition,
                "used": [self._encode_constant(constant) for constant in record.constants],
            },
            "units": {"registry_version": record.unit_registry_version},
            "result": self._results.encode(record),
            "verification": _encode_verification(record.verification),
            "limitations": list(record.problem.card.limitations),
            "environment": _encode_environment(record.environment),
        }

    def _encode_constant(self, constant: PhysicalConstant) -> JsonObject:
        uncertainty = constant.standard_uncertainty
        return {
            "identifier": constant.identifier,
            "symbol": constant.symbol,
            "name": constant.name,
            "value": self._quantities.encode(constant.value),
            "exactness": constant.exactness.value,
            "standard_uncertainty": (
                None
                if uncertainty is None
                else encode_exact(uncertainty, self._quantities.unit_of(constant.value))
            ),
            "source": constant.source,
        }


def encode_rejection(rejection: ProblemRejectedError) -> JsonObject:
    return {
        **_header("rejection"),
        "category": rejection.category.value,
        "diagnostics": [
            {
                "category": item.category.value,
                "code": item.code.value,
                "pointer": item.pointer,
                "message": item.message,
                "expected": item.expected,
            }
            for item in rejection.diagnostics
        ],
    }


def _header(document: str) -> JsonObject:
    return {"document": document, "schema_version": OUTPUT_SCHEMA_VERSION}


def _encode_input(spec: ProblemSpec) -> JsonObject:
    return {
        "sha256": spec.source.sha256,
        "schema_version": spec.schema_version,
        "description": spec.description,
        "text": spec.source.text,
    }


def _encode_plan(plan: SolvePlan) -> JsonObject:
    return {
        "method": plan.method.identifier,
        "nature": plan.method.nature.value,
        "justification": plan.method.justification,
        "rounding": {
            "mode": ROUNDING_MODE,
            "significant_digits": plan.rounding.significant_digits,
        },
    }


def _encode_verification(report: VerificationReport) -> JsonObject:
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


def _encode_environment(manifest: EnvironmentManifest) -> JsonObject:
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
    }
