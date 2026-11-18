from dataclasses import dataclass
from enum import StrEnum


class DiagnosticCategory(StrEnum):
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED_PROBLEM = "unsupported_problem"


class DiagnosticCode(StrEnum):
    DOCUMENT_TOO_LARGE = "document_too_large"
    INVALID_ENCODING = "invalid_encoding"
    MALFORMED_JSON = "malformed_json"
    DOCUMENT_TOO_DEEP = "document_too_deep"
    DUPLICATE_FIELD = "duplicate_field"
    MISSING_FIELD = "missing_field"
    UNEXPECTED_FIELD = "unexpected_field"
    INVALID_TYPE = "invalid_type"
    MALFORMED_NUMBER = "malformed_number"
    NON_FINITE_NUMBER = "non_finite_number"
    NUMBER_OUT_OF_RANGE = "number_out_of_range"
    UNSUPPORTED_SCHEMA_VERSION = "unsupported_schema_version"
    UNKNOWN_UNIT = "unknown_unit"
    UNKNOWN_CONSTANT = "unknown_constant"
    DIMENSION_MISMATCH = "dimension_mismatch"
    NON_POSITIVE_QUANTITY = "non_positive_quantity"
    NOT_A_POSITIVE_INTEGER = "not_a_positive_integer"
    NEGATIVE_UNCERTAINTY = "negative_uncertainty"
    HYPOTHESIS_NOT_CONFIRMED = "hypothesis_not_confirmed"
    UNKNOWN_PROBLEM = "unknown_problem"
    UNSUPPORTED_HYPOTHESIS = "unsupported_hypothesis"
    UNSUPPORTED_QUANTITY = "unsupported_quantity"
    UNSUPPORTED_COVARIANCE = "unsupported_covariance"


_UNSUPPORTED_PROBLEM_CODES = frozenset(
    {
        DiagnosticCode.UNKNOWN_PROBLEM,
        DiagnosticCode.UNSUPPORTED_HYPOTHESIS,
        DiagnosticCode.UNSUPPORTED_QUANTITY,
        DiagnosticCode.UNSUPPORTED_COVARIANCE,
    }
)


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: DiagnosticCode
    pointer: str
    message: str
    expected: str

    @property
    def category(self) -> DiagnosticCategory:
        if self.code in _UNSUPPORTED_PROBLEM_CODES:
            return DiagnosticCategory.UNSUPPORTED_PROBLEM
        return DiagnosticCategory.INVALID_INPUT


class ProblemRejectedError(Exception):
    def __init__(self, diagnostics: tuple[Diagnostic, ...]) -> None:
        super().__init__(
            "; ".join(f"{item.pointer or '/'}: {item.message}" for item in diagnostics)
        )
        self.diagnostics = diagnostics

    @property
    def category(self) -> DiagnosticCategory:
        categories = {item.category for item in self.diagnostics}
        if DiagnosticCategory.INVALID_INPUT in categories:
            return DiagnosticCategory.INVALID_INPUT
        return DiagnosticCategory.UNSUPPORTED_PROBLEM
