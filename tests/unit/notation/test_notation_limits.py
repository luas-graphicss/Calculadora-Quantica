import pytest

from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCategory, DiagnosticCode
from quantum_calculator.domain.statements import Notation
from quantum_calculator.notation.limits import (
    MAX_NESTING_DEPTH,
    MAX_NODE_COUNT,
    MAX_STATEMENT_LENGTH,
)
from support.notation import read, refusal_of, refusal_or_none

COMPLETE_STATEMENTS = [
    (Notation.TEXT, "diff((x^2 - 1)/(x - 1), x, 2) + integral(sin(x)^2, x, 0, pi)"),
    (Notation.TEXT, "u'(t) = -k*u(t) + a*exp(-t)"),
    (Notation.LATEX, "\\frac{d^{2}}{dx^{2}}\\left(\\frac{x^{2} - 1}{x - 1}\\right)"),
    (Notation.LATEX, "\\int_{0}^{\\pi} \\left|\\sin(x)\\right|^{2} \\, dx + \\sqrt{\\lambda_{0}}"),
    (Notation.LATEX, "\\frac{du}{dt} = -k u(t) + \\mathrm{a} \\exp\\left(-t\\right)"),
]


def _category(code: DiagnosticCode) -> DiagnosticCategory:
    return Diagnostic(code, "/statement", "m", "e").category


@pytest.mark.parametrize(("notation", "statement"), COMPLETE_STATEMENTS)
def test_every_truncation_of_a_statement_is_read_or_refused_never_crashes(
    notation: Notation, statement: str
) -> None:
    outcomes = [refusal_or_none(notation, statement[:length]) for length in range(len(statement))]

    spans = [(refusal.span.start, refusal.span.end) for refusal in outcomes if refusal is not None]
    assert spans
    assert all(0 <= start <= end <= len(statement) for start, end in spans)


@pytest.mark.parametrize("notation", list(Notation))
def test_empty_statement_is_refused_as_truncated(notation: Notation) -> None:
    assert refusal_of(notation, "").code is DiagnosticCode.UNEXPECTED_END


@pytest.mark.parametrize(
    ("notation", "opening", "closing"),
    [(Notation.TEXT, "(", ")"), (Notation.LATEX, "{", "}"), (Notation.TEXT, "sin(", ")")],
)
def test_nesting_beyond_the_limit_is_refused_without_exhausting_the_stack(
    notation: Notation, opening: str, closing: str
) -> None:
    levels = 20_000
    refusal = refusal_of(notation, opening * levels + "x" + closing * levels)

    assert refusal.code in {DiagnosticCode.STATEMENT_TOO_LONG, DiagnosticCode.EXPRESSION_TOO_DEEP}
    assert _category(refusal.code) is DiagnosticCategory.BUDGET_EXCEEDED


def test_nesting_just_over_the_limit_is_too_deep_and_at_the_limit_is_read() -> None:
    def nested(levels: int) -> str:
        return "(" * levels + "x" + ")" * levels

    too_deep = refusal_of(Notation.TEXT, nested(MAX_NESTING_DEPTH + 1))

    assert too_deep.code is DiagnosticCode.EXPRESSION_TOO_DEEP
    assert read(Notation.TEXT, nested(MAX_NESTING_DEPTH)) == read(Notation.TEXT, "x")


def test_chain_of_signs_counts_as_nesting() -> None:
    refusal = refusal_of(Notation.TEXT, "-" * (MAX_NESTING_DEPTH + 1) + "x")

    assert refusal.code is DiagnosticCode.EXPRESSION_TOO_DEEP


def test_statement_over_the_length_limit_is_refused_before_tokenizing() -> None:
    refusal = refusal_of(Notation.TEXT, "$" * (MAX_STATEMENT_LENGTH + 1))

    assert refusal.code is DiagnosticCode.STATEMENT_TOO_LONG


def test_tree_over_the_node_limit_is_refused() -> None:
    terms = MAX_NODE_COUNT // 2 + 1
    refusal = refusal_of(Notation.TEXT, "+".join(["x"] * terms))

    assert refusal.code is DiagnosticCode.EXPRESSION_TOO_LARGE
    assert _category(refusal.code) is DiagnosticCategory.BUDGET_EXCEEDED


@pytest.mark.parametrize(
    ("notation", "statement"),
    [
        (Notation.TEXT, "gamma(x)"),
        (Notation.TEXT, "log(x)"),
        (Notation.TEXT, "erf(x) + 1"),
        (Notation.LATEX, "\\sum x"),
        (Notation.LATEX, "\\lim x"),
        (Notation.LATEX, "\\sinh(x)"),
    ],
)
def test_operation_outside_the_registered_list_is_unsupported(
    notation: Notation, statement: str
) -> None:
    refusal = refusal_of(notation, statement)

    assert refusal.code is DiagnosticCode.UNSUPPORTED_OPERATION
    assert _category(refusal.code) is DiagnosticCategory.UNSUPPORTED_PROBLEM
