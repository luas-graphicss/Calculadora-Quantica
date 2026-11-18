import pytest

from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.statements import Notation
from support.notation import refusal_of, structure_of

ACCEPTED = [
    ("fraction", "\\frac{a}{b}", "(divide (symbol a) (symbol b))"),
    ("power", "x^{2}", "(power (symbol x) (number 2))"),
    ("power", "x^2", "(power (symbol x) (number 2))"),
    ("power", "x^{-2}", "(power (symbol x) (negate (number 2)))"),
    ("function", "\\sin(x)", "(sin (symbol x))"),
    ("function", "\\cos\\left(x\\right)", "(cos (symbol x))"),
    ("function", "\\exp(-x)", "(exp (negate (symbol x)))"),
    ("root", "\\sqrt{x}", "(sqrt (symbol x))"),
    ("modulus", "\\left|x\\right|", "(abs (symbol x))"),
    ("product", "a x", "(multiply (symbol a) (symbol x))"),
    ("product", "a \\cdot x", "(multiply (symbol a) (symbol x))"),
    ("product", "\\frac{1}{2} x", "(multiply (divide (number 1) (number 2)) (symbol x))"),
    ("greek letter", "\\lambda + \\pi", "(add (symbol \N{GREEK SMALL LETTER LAMDA}) pi)"),
    ("subscript", "y_{0} + y_0", "(add (symbol y_0) (symbol y_0))"),
    ("subscript", "\\omega_{0}", "(symbol \N{GREEK SMALL LETTER OMEGA}_0)"),
    (
        "derivative",
        "\\frac{d}{dx}\\left(x^{2}\\right)",
        "(derivative ordinary x 1 (power (symbol x) (number 2)))",
    ),
    (
        "higher derivative",
        "\\frac{d^{2}}{dx^{2}}(x^{3})",
        "(derivative ordinary x 2 (power (symbol x) (number 3)))",
    ),
    (
        "partial derivative",
        "\\frac{\\partial}{\\partial y}(x y)",
        "(derivative partial y 1 (multiply (symbol x) (symbol y)))",
    ),
    ("function derivative", "\\frac{du}{dt}", "(unknown u 1 (symbol t))"),
    ("function derivative", "u'(t)", "(unknown u 1 (symbol t))"),
    ("antiderivative", "\\int x^{2} \\, dx", "(integral x (power (symbol x) (number 2)))"),
    (
        "definite integral",
        "\\int_{0}^{a} x^{2} \\, dx",
        "(integral x (power (symbol x) (number 2)) (number 0) (symbol a))",
    ),
    ("definite integral", "\\int_0^1 x \\, dx", "(integral x (symbol x) (number 0) (number 1))"),
    (
        "equation",
        "\\frac{du}{dt} = -k u",
        "(equation (unknown u 1 (symbol t)) "
        "(negate (multiply (symbol k) (unknown u 0 (symbol t)))))",
    ),
]

REFUSED = [
    ("fraction", "\\frac{a}{b", DiagnosticCode.UNEXPECTED_END),
    ("fraction", "\\frac{a}", DiagnosticCode.UNEXPECTED_END),
    ("power", "x^2^3", DiagnosticCode.AMBIGUOUS_POWER),
    ("function", "\\sin x", DiagnosticCode.AMBIGUOUS_ARGUMENT),
    ("function", "\\sinh(x)", DiagnosticCode.UNSUPPORTED_OPERATION),
    ("root", "\\sqrt x", DiagnosticCode.SYNTAX_ERROR),
    ("modulus", "|x|", DiagnosticCode.UNEXPECTED_CHARACTER),
    ("product", "a2", DiagnosticCode.AMBIGUOUS_JUXTAPOSITION),
    ("product", "1/2x", DiagnosticCode.AMBIGUOUS_DIVISION),
    ("greek letter", "\\sum x", DiagnosticCode.UNSUPPORTED_OPERATION),
    ("subscript", "x_{a+b}", DiagnosticCode.INVALID_SYMBOL_NAME),
    ("derivative", "\\frac{d}{dx} x^{2}", DiagnosticCode.AMBIGUOUS_ARGUMENT),
    ("higher derivative", "\\frac{d^{2}}{dx}(x)", DiagnosticCode.SYNTAX_ERROR),
    ("partial derivative", "\\frac{\\partial}{dx}(x)", DiagnosticCode.SYNTAX_ERROR),
    ("function derivative", "\\frac{dx}{dy}", DiagnosticCode.NOT_A_FUNCTION),
    ("function derivative", "\\frac{du}{dx}", DiagnosticCode.NOT_A_VARIABLE),
    ("antiderivative", "\\int x^{2}", DiagnosticCode.UNEXPECTED_END),
    ("definite integral", "\\int_{0} x \\, dx", DiagnosticCode.SYNTAX_ERROR),
    ("equation", "x = y = a", DiagnosticCode.SYNTAX_ERROR),
    ("stray differential", "x d", DiagnosticCode.SYNTAX_ERROR),
    ("truncated command", "x + \\", DiagnosticCode.UNSUPPORTED_OPERATION),
]


@pytest.mark.parametrize(("construct", "statement", "structure"), ACCEPTED)
def test_latex_construct_is_read_as_the_documented_tree(
    construct: str, statement: str, structure: str
) -> None:
    assert structure_of(Notation.LATEX, statement) == structure, construct


@pytest.mark.parametrize(("construct", "statement", "code"), REFUSED)
def test_latex_construct_misuse_is_refused_with_its_diagnostic(
    construct: str, statement: str, code: DiagnosticCode
) -> None:
    assert refusal_of(Notation.LATEX, statement).code is code, construct


def test_every_accepted_latex_construct_has_a_refused_counterpart() -> None:
    accepted = {construct for construct, _, _ in ACCEPTED}
    refused = {construct for construct, _, _ in REFUSED}

    assert accepted <= refused


def test_undelimited_derivative_operand_points_at_the_operator() -> None:
    refusal = refusal_of(Notation.LATEX, "\\frac{d}{dx} x^{2} + 1")

    assert (refusal.span.start, refusal.span.end) == (0, 14)
