from dataclasses import dataclass
from enum import StrEnum


class DiagnosticCategory(StrEnum):
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED_PROBLEM = "unsupported_problem"
    AMBIGUOUS_INPUT = "ambiguous_input"
    BUDGET_EXCEEDED = "budget_exceeded"
    NON_CONVERGENT = "non_convergent"


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
    UNEXPECTED_CHARACTER = "unexpected_character"
    SYNTAX_ERROR = "syntax_error"
    UNEXPECTED_END = "unexpected_end"
    UNDECLARED_SYMBOL = "undeclared_symbol"
    RESERVED_NAME = "reserved_name"
    INVALID_SYMBOL_NAME = "invalid_symbol_name"
    UNKNOWN_OPTION = "unknown_option"
    NOT_A_VARIABLE = "not_a_variable"
    NOT_A_FUNCTION = "not_a_function"
    BOUND_VARIABLE_MISUSE = "bound_variable_misuse"
    DIMENSIONAL_ARGUMENT = "dimensional_argument"
    UNDEFINED_EXPRESSION = "undefined_expression"
    CARD_MISMATCH = "card_mismatch"
    MALFORMED_CONDITION = "malformed_condition"
    MALFORMED_CANDIDATE = "malformed_candidate"
    AMBIGUOUS_DIVISION = "ambiguous_division"
    AMBIGUOUS_POWER = "ambiguous_power"
    AMBIGUOUS_APPLICATION = "ambiguous_application"
    AMBIGUOUS_ARGUMENT = "ambiguous_argument"
    AMBIGUOUS_JUXTAPOSITION = "ambiguous_juxtaposition"
    AMBIGUOUS_DERIVATIVE = "ambiguous_derivative"
    AMBIGUOUS_PROBLEM = "ambiguous_problem"
    UNSUPPORTED_OPERATION = "unsupported_operation"
    NO_COMPATIBLE_CARD = "no_compatible_card"
    OUTSIDE_COVERAGE = "outside_coverage"
    SINGULARITY_IN_INTERVAL = "singularity_in_interval"
    STATEMENT_TOO_LONG = "statement_too_long"
    EXPRESSION_TOO_DEEP = "expression_too_deep"
    EXPRESSION_TOO_LARGE = "expression_too_large"
    TIME_BUDGET_EXCEEDED = "time_budget_exceeded"
    MEMORY_BUDGET_EXCEEDED = "memory_budget_exceeded"
    INVALID_SHAPE = "invalid_shape"
    ZERO_STATE = "zero_state"
    STATE_NOT_NORMALIZED = "state_not_normalized"
    NON_HERMITIAN_OPERATOR = "non_hermitian_operator"
    BASIS_NOT_ORTHONORMAL = "basis_not_orthonormal"
    INCOMPATIBLE_CONDITION = "incompatible_condition"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    METHOD_NOT_CONVERGED = "method_not_converged"
    NON_FINITE_RESULT = "non_finite_result"


_CATEGORY_BY_CODE = {
    **dict.fromkeys(
        (
            DiagnosticCode.UNKNOWN_PROBLEM,
            DiagnosticCode.UNSUPPORTED_HYPOTHESIS,
            DiagnosticCode.UNSUPPORTED_QUANTITY,
            DiagnosticCode.UNSUPPORTED_COVARIANCE,
            DiagnosticCode.UNSUPPORTED_OPERATION,
            DiagnosticCode.NO_COMPATIBLE_CARD,
            DiagnosticCode.OUTSIDE_COVERAGE,
            DiagnosticCode.SINGULARITY_IN_INTERVAL,
        ),
        DiagnosticCategory.UNSUPPORTED_PROBLEM,
    ),
    **dict.fromkeys(
        (
            DiagnosticCode.AMBIGUOUS_DIVISION,
            DiagnosticCode.AMBIGUOUS_POWER,
            DiagnosticCode.AMBIGUOUS_APPLICATION,
            DiagnosticCode.AMBIGUOUS_ARGUMENT,
            DiagnosticCode.AMBIGUOUS_JUXTAPOSITION,
            DiagnosticCode.AMBIGUOUS_DERIVATIVE,
            DiagnosticCode.AMBIGUOUS_PROBLEM,
        ),
        DiagnosticCategory.AMBIGUOUS_INPUT,
    ),
    **dict.fromkeys(
        (
            DiagnosticCode.STATEMENT_TOO_LONG,
            DiagnosticCode.EXPRESSION_TOO_DEEP,
            DiagnosticCode.EXPRESSION_TOO_LARGE,
            DiagnosticCode.TIME_BUDGET_EXCEEDED,
            DiagnosticCode.MEMORY_BUDGET_EXCEEDED,
            DiagnosticCode.RESOURCE_LIMIT_EXCEEDED,
        ),
        DiagnosticCategory.BUDGET_EXCEEDED,
    ),
    **dict.fromkeys(
        (DiagnosticCode.METHOD_NOT_CONVERGED, DiagnosticCode.NON_FINITE_RESULT),
        DiagnosticCategory.NON_CONVERGENT,
    ),
}

_MOST_ACTIONABLE_FIRST = (
    DiagnosticCategory.INVALID_INPUT,
    DiagnosticCategory.BUDGET_EXCEEDED,
    DiagnosticCategory.AMBIGUOUS_INPUT,
    DiagnosticCategory.UNSUPPORTED_PROBLEM,
    DiagnosticCategory.NON_CONVERGENT,
)

_QUOTED_TEXT_LIMIT = 64


def quote_user_text(text: str) -> str:
    shown = text if len(text) <= _QUOTED_TEXT_LIMIT else f"{text[:_QUOTED_TEXT_LIMIT]}..."
    return f'"{shown}"'


def json_pointer(*segments: str) -> str:
    return "".join(f"/{segment.replace('~', '~0').replace('/', '~1')}" for segment in segments)


@dataclass(frozen=True, slots=True)
class SourceExcerpt:
    text: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: DiagnosticCode
    pointer: str
    message: str
    expected: str
    excerpt: SourceExcerpt | None = None

    @property
    def category(self) -> DiagnosticCategory:
        return _CATEGORY_BY_CODE.get(self.code, DiagnosticCategory.INVALID_INPUT)


class ProblemRejectedError(Exception):
    def __init__(self, diagnostics: tuple[Diagnostic, ...]) -> None:
        super().__init__(
            "; ".join(f"{item.pointer or '/'}: {item.message}" for item in diagnostics)
        )
        self.diagnostics = diagnostics

    def __reduce__(self) -> tuple[type["ProblemRejectedError"], tuple[tuple[Diagnostic, ...]]]:
        return type(self), (self.diagnostics,)

    @property
    def category(self) -> DiagnosticCategory:
        present = {item.category for item in self.diagnostics}
        for category in _MOST_ACTIONABLE_FIRST:
            if category in present:
                return category
        return DiagnosticCategory.INVALID_INPUT
