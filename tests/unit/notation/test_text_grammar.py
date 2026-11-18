import pytest

from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCategory, DiagnosticCode
from quantum_calculator.domain.statements import Notation
from support.notation import refusal_of, structure_of

ACCEPTED = [
    ("decimal number", "2.5", "(number 5/2)"),
    ("scientific notation", "1.5e3", "(number 1500)"),
    ("constant", "pi", "pi"),
    ("symbol", "y_0", "(symbol y_0)"),
    ("sum", "x + y - a", "(subtract (add (symbol x) (symbol y)) (symbol a))"),
    ("negation", "-x^2", "(negate (power (symbol x) (number 2)))"),
    ("explicit product", "a*x", "(multiply (symbol a) (symbol x))"),
    ("implicit product", "2 a x", "(multiply (multiply (number 2) (symbol a)) (symbol x))"),
    (
        "product of groups",
        "(x + 1)(x - 1)",
        "(multiply (add (symbol x) (number 1)) (subtract (symbol x) (number 1)))",
    ),
    ("division", "a*x/b", "(divide (multiply (symbol a) (symbol x)) (symbol b))"),
    ("power", "x^(y + 1)", "(power (symbol x) (add (symbol y) (number 1)))"),
    ("negative exponent", "x^-2", "(power (symbol x) (negate (number 2)))"),
    ("grouping", "a*(x + y)", "(multiply (symbol a) (add (symbol x) (symbol y)))"),
    ("function", "sin(x)^2", "(power (sin (symbol x)) (number 2))"),
    ("derivative", "diff(x^2, x)", "(derivative ordinary x 1 (power (symbol x) (number 2)))"),
    (
        "higher derivative",
        "diff(x^3, x, 2)",
        "(derivative ordinary x 2 (power (symbol x) (number 3)))",
    ),
    (
        "partial derivative",
        "partial(x*y, y)",
        "(derivative partial y 1 (multiply (symbol x) (symbol y)))",
    ),
    ("antiderivative", "integral(x^2, x)", "(integral x (power (symbol x) (number 2)))"),
    (
        "definite integral",
        "integral(x^2, x, 0, a)",
        "(integral x (power (symbol x) (number 2)) (number 0) (symbol a))",
    ),
    ("unknown function", "u(0)", "(unknown u 0 (number 0))"),
    ("unknown function at its declared argument", "u'", "(unknown u 1 (symbol t))"),
    (
        "equation",
        "u'(t) = -k u(t)",
        "(equation (unknown u 1 (symbol t)) "
        "(negate (multiply (symbol k) (unknown u 0 (symbol t)))))",
    ),
]

REFUSED = [
    ("decimal number", "1.5.2", DiagnosticCode.MALFORMED_NUMBER),
    ("decimal number", ".5", DiagnosticCode.MALFORMED_NUMBER),
    ("scientific notation", "1e100", DiagnosticCode.NUMBER_OUT_OF_RANGE),
    ("decimal comma", "1,5", DiagnosticCode.SYNTAX_ERROR),
    ("symbol", "z + 1", DiagnosticCode.UNDECLARED_SYMBOL),
    ("symbol", "x_1_2", DiagnosticCode.INVALID_SYMBOL_NAME),
    ("sum", "x +", DiagnosticCode.UNEXPECTED_END),
    ("negation", "a*-x", DiagnosticCode.SYNTAX_ERROR),
    ("implicit product", "x 2", DiagnosticCode.AMBIGUOUS_JUXTAPOSITION),
    ("division", "1/2x", DiagnosticCode.AMBIGUOUS_DIVISION),
    ("division", "a/b/x", DiagnosticCode.AMBIGUOUS_DIVISION),
    ("division", "a/b*x", DiagnosticCode.AMBIGUOUS_DIVISION),
    ("power", "x^y^a", DiagnosticCode.AMBIGUOUS_POWER),
    ("power", "x^", DiagnosticCode.UNEXPECTED_END),
    ("grouping", "(x + 1", DiagnosticCode.UNEXPECTED_END),
    ("grouping", "x + 1)", DiagnosticCode.SYNTAX_ERROR),
    ("function", "sin x", DiagnosticCode.AMBIGUOUS_ARGUMENT),
    ("function", "sinh(x)", DiagnosticCode.UNSUPPORTED_OPERATION),
    ("function", "a(x + 1)", DiagnosticCode.AMBIGUOUS_APPLICATION),
    ("derivative", "diff(x^2)", DiagnosticCode.SYNTAX_ERROR),
    ("derivative", "diff(x^2, z)", DiagnosticCode.UNDECLARED_SYMBOL),
    ("higher derivative", "diff(x^2, x, 0)", DiagnosticCode.NUMBER_OUT_OF_RANGE),
    ("definite integral", "integral(x, x, 0)", DiagnosticCode.SYNTAX_ERROR),
    ("unknown function", "u'''''''''", DiagnosticCode.NUMBER_OUT_OF_RANGE),
    ("equation", "x = y = a", DiagnosticCode.SYNTAX_ERROR),
    ("alphabet", "x $ 2", DiagnosticCode.UNEXPECTED_CHARACTER),
    ("reserved differential", "d/x", DiagnosticCode.SYNTAX_ERROR),
]


@pytest.mark.parametrize(("construct", "statement", "structure"), ACCEPTED)
def test_text_construct_is_read_as_the_documented_tree(
    construct: str, statement: str, structure: str
) -> None:
    assert structure_of(Notation.TEXT, statement) == structure, construct


@pytest.mark.parametrize(("construct", "statement", "code"), REFUSED)
def test_text_construct_misuse_is_refused_with_its_diagnostic(
    construct: str, statement: str, code: DiagnosticCode
) -> None:
    assert refusal_of(Notation.TEXT, statement).code is code, construct


def test_every_accepted_text_construct_has_a_refused_counterpart() -> None:
    refused = {construct for construct, _, _ in REFUSED}

    assert {
        "decimal number",
        "sum",
        "negation",
        "implicit product",
        "division",
        "power",
        "grouping",
        "function",
        "derivative",
        "definite integral",
        "unknown function",
        "equation",
    } <= refused


def test_ambiguous_division_points_at_the_ambiguous_excerpt() -> None:
    refusal = refusal_of(Notation.TEXT, "x + 1/2x")

    assert (refusal.span.start, refusal.span.end) == (4, 8)
    assert "(a/b)*c ou a/(b*c)" in refusal.expected


def test_decimal_comma_is_refused_with_the_decimal_point_as_the_expected_form() -> None:
    assert "o separador decimal é o ponto" in refusal_of(Notation.TEXT, "1,5").expected


def test_ambiguity_is_a_category_of_its_own() -> None:
    codes = {code for _, _, code in REFUSED if code.value.startswith("ambiguous_")}

    assert codes
    assert all(_category(code) is DiagnosticCategory.AMBIGUOUS_INPUT for code in codes)


def _category(code: DiagnosticCode) -> DiagnosticCategory:
    return Diagnostic(code, "/statement", "m", "e").category
