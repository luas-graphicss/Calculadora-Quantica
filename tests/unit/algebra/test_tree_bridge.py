import pytest
import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.algebra.reader import UnregisteredOperationError, read_expression
from quantum_calculator.domain.statements import Notation, SymbolDomain, SymbolRole
from quantum_calculator.notation.rendering.structure import render_structure
from quantum_calculator.notation.rendering.text import render_text
from support.notation import SYMBOLS, declared, read, read_expression_text, symbol_table

EXPRESSIONS = [
    "3*x^4 - 2*x + 7",
    "x^2*sin(x)",
    "-k*y_0*exp(-k*t)/(2*x)",
    "(x^2 - 1)/(x - 1)",
    "sqrt(x^2) + abs(y)",
    "ln(x)/x - tan(y)^2",
    "x^(3/2) + x^-1 + x^(-1/2)",
    "a*cos(pi*x) - exp(1)",
    "0.5*x - 1.25",
]


@pytest.fixture(scope="module")
def builder() -> ExpressionBuilder:
    return ExpressionBuilder(SYMBOLS.values())


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_result_read_back_from_the_algebra_system_is_valid_input_notation(
    builder: ExpressionBuilder, expression: str
) -> None:
    value = builder.build(read_expression_text(expression))

    tree = read_expression(value)

    assert read(Notation.TEXT, render_text(tree)) == tree
    assert sympy.simplify(builder.build(tree) - value) == 0


@pytest.mark.parametrize(
    ("value", "structure"),
    [
        (sympy.Rational(-3, 2), "(negate (divide (number 3) (number 2)))"),
        (sympy.Integer(-4), "(negate (number 4))"),
        (sympy.E, "(exp (number 1))"),
        (sympy.pi / 2, "(divide pi (number 2))"),
        (sympy.sqrt(sympy.Symbol("x")), "(sqrt (symbol x))"),
        (1 / sympy.Symbol("x") ** 2, "(divide (number 1) (power (symbol x) (number 2)))"),
        (sympy.sign(sympy.Symbol("x")), "(divide (symbol x) (abs (symbol x)))"),
    ],
)
def test_algebra_value_is_read_in_the_normal_form_the_parser_produces(
    value: sympy.Expr, structure: str
) -> None:
    assert render_structure(read_expression(value)) == structure


@pytest.mark.parametrize(
    ("value", "operation"),
    [
        (sympy.erf(sympy.Symbol("x")), "erf"),
        (sympy.Piecewise((1, sympy.Symbol("x") > 0), (0, True)), "Piecewise"),
        (sympy.oo, "Infinity"),
        (sympy.zoo, "ComplexInfinity"),
    ],
)
def test_value_outside_the_registered_operations_is_not_read(
    value: sympy.Expr, operation: str
) -> None:
    with pytest.raises(UnregisteredOperationError) as refusal:
        read_expression(value)

    assert refusal.value.operation == operation


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        (SymbolDomain.REAL, "abs(x)"),
        (SymbolDomain.NONZERO, "abs(x)"),
        (SymbolDomain.POSITIVE, "x"),
        (SymbolDomain.NONNEGATIVE, "x"),
        (SymbolDomain.NEGATIVE, "-x"),
    ],
)
def test_root_of_a_square_is_reduced_only_as_far_as_the_declared_sign_allows(
    domain: SymbolDomain, expected: str
) -> None:
    symbols = symbol_table(declared("x", domain=domain))
    builder = ExpressionBuilder(symbols.values())

    value = builder.build(read_expression_text("sqrt(x^2)", symbols))

    assert render_text(read_expression(value)) == expected


def test_unknown_function_is_built_at_its_argument_and_at_a_point() -> None:
    builder = ExpressionBuilder(SYMBOLS.values())
    unknown = builder.unknown("u")

    slope = builder.build(read_expression_text("u'(t)"))
    at_origin = builder.build(read_expression_text("u(0)"))

    assert slope == sympy.Derivative(unknown, builder.symbol("t"))
    assert at_origin == unknown.subs(builder.symbol("t"), 0)
    assert SYMBOLS["u"].role is SymbolRole.FUNCTION
