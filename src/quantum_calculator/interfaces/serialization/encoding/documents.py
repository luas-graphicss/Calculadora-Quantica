from quantum_calculator.domain.diagnostics import Diagnostic, ProblemRejectedError
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.rounding import ROUNDING_MODE
from quantum_calculator.domain.run_record import RunRecord
from quantum_calculator.domain.solution import SolvePlan
from quantum_calculator.domain.validated_problem import ValidatedProblem
from quantum_calculator.interfaces.serialization.encoding.common_sections import (
    document_header,
    encode_environment,
    encode_input,
    encode_verification,
)
from quantum_calculator.interfaces.serialization.encoding.constants import encode_constant
from quantum_calculator.interfaces.serialization.encoding.exact_values import (
    JsonObject,
    QuantityEncoder,
)
from quantum_calculator.interfaces.serialization.encoding.problem_encoding import ProblemEncoder
from quantum_calculator.interfaces.serialization.encoding.result_encoding import ResultEncoder


class DocumentEncoder:
    def __init__(self, units: UnitRegistry) -> None:
        self._quantities = QuantityEncoder(units)
        self._problems = ProblemEncoder(self._quantities)
        self._results = ResultEncoder(self._quantities)

    def validation(self, problem: ValidatedProblem, plan: SolvePlan) -> JsonObject:
        return {
            **document_header("validation"),
            "input": encode_input(problem.spec),
            "problem": self._problems.encode(problem),
            "plan": _encode_plan(plan),
        }

    def run_record(self, record: RunRecord) -> JsonObject:
        return {
            **document_header("run_record"),
            "input": encode_input(record.problem.spec),
            "problem": self._problems.encode(record.problem),
            "plan": _encode_plan(record.plan),
            "constants": {
                "edition": record.constants_edition,
                "used": [
                    encode_constant(constant, self._quantities) for constant in record.constants
                ],
            },
            "units": {"registry_version": record.unit_registry_version},
            "result": self._results.encode(record),
            "verification": encode_verification(record.verification),
            "limitations": list(record.problem.card.limitations),
            "environment": encode_environment(record.environment),
        }


def encode_rejection(rejection: ProblemRejectedError) -> JsonObject:
    return {
        **document_header("rejection"),
        "category": rejection.category.value,
        "diagnostics": [_encode_diagnostic(item) for item in rejection.diagnostics],
    }


def _encode_diagnostic(item: Diagnostic) -> JsonObject:
    excerpt = item.excerpt
    return {
        "category": item.category.value,
        "code": item.code.value,
        "pointer": item.pointer,
        "message": item.message,
        "expected": item.expected,
        "excerpt": (
            None
            if excerpt is None
            else {"text": excerpt.text, "start": excerpt.start, "end": excerpt.end}
        ),
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
