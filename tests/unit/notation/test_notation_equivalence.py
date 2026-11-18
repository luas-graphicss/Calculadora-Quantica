import pytest

from quantum_calculator.domain.statements import Notation
from quantum_calculator.notation.rendering.latex import render_latex
from quantum_calculator.notation.rendering.text import render_text
from support.notation import read

EQUIVALENT = [
    ("diff(x^2*sin(x), x)", "\\frac{d}{dx}\\left(x^{2} \\sin(x)\\right)"),
    ("partial(x^2 y, x)", "\\frac{\\partial}{\\partial x}(x^2 y)"),
    (
        "diff((x^2 - 1)/(x - 1), x, 2)",
        "\\frac{d^{2}}{dx^{2}}\\left(\\frac{x^{2} - 1}{x - 1}\\right)",
    ),
    ("integral(x^2, x, 0, 1)", "\\int_{0}^{1} x^{2} \\, dx"),
    ("integral(1/x, x)", "\\int \\frac{1}{x} \\, dx"),
    ("u'(t) = -k u(t)", "\\frac{du}{dt} = -k u(t)"),
    ("u' = -k*u", "u' = -k \\cdot u"),
    ("u(0) = y_0", "u(0) = y_{0}"),
    ("u(t) = y_0 exp(-k t)", "u(t) = y_0 \\exp(-k t)"),
    ("lambda*x + 2 pi", "\\lambda x + 2 \\pi"),
    ("abs(x)^3 - sqrt(x)", "\\left|x\\right|^{3} - \\sqrt{x}"),
    ("-x^2 + 0.5 x^-1", "-x^{2} + 0.5 x^{-1}"),
    ("omega_0 t", "\\omega_{0} t"),
]

UNICODE_AND_TEXTUAL = [
    ("x\N{SUPERSCRIPT TWO}\N{MIDDLE DOT}sin(x)", "x^2*sin(x)"),
    ("x\N{SUPERSCRIPT ONE}\N{SUPERSCRIPT TWO}", "x^12"),
    ("\N{GREEK SMALL LETTER LAMDA} x \N{MINUS SIGN} \N{GREEK SMALL LETTER PI}", "lambda*x - pi"),
    ("\N{SQUARE ROOT}(x) \N{DOT OPERATOR} a", "sqrt(x)*a"),
    ("u\N{PRIME}(t)", "u'(t)"),
    ("\N{GREEK SMALL LETTER OMEGA}_0", "omega_0"),
]


@pytest.mark.parametrize(("text", "latex"), EQUIVALENT)
def test_text_and_latex_notations_give_the_same_tree(text: str, latex: str) -> None:
    assert read(Notation.TEXT, text) == read(Notation.LATEX, latex)


@pytest.mark.parametrize(("unicode", "textual"), UNICODE_AND_TEXTUAL)
def test_unicode_symbols_and_their_textual_equivalents_give_the_same_tree(
    unicode: str, textual: str
) -> None:
    assert read(Notation.TEXT, unicode) == read(Notation.TEXT, textual)


@pytest.mark.parametrize("text", [text for text, _ in EQUIVALENT])
def test_rendered_interpretation_reads_back_as_the_same_tree_in_both_notations(text: str) -> None:
    tree = read(Notation.TEXT, text)

    assert read(Notation.TEXT, render_text(tree)) == tree
    assert read(Notation.LATEX, render_latex(tree)) == tree


def test_rendered_interpretation_makes_grouping_and_products_explicit() -> None:
    tree = read(Notation.TEXT, "-a x/(2 b) + (x + 1)^2")

    assert render_text(tree) == "-a*x/(2*b) + (x + 1)^2"
    assert render_latex(tree) == "-\\frac{a \\cdot x}{2 \\cdot b} + \\left(x + 1\\right)^{2}"


def test_trees_differing_only_in_source_positions_are_equal() -> None:
    assert read(Notation.TEXT, "a*x") == read(Notation.TEXT, "  a   *   (x)")
