from dataclasses import replace

import pytest

from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.domain.diagnostics import DiagnosticCategory, DiagnosticCode
from quantum_calculator.domain.expressions import Equation
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.verification import EvidenceKind, VerificationStatus
from quantum_calculator.solvers.symbolic.differentiation import DifferentiationSolver
from quantum_calculator.verification.differentiation import DifferentiationVerifier
from support.statements import CALCULUS, KINEMATICS, POSITIVE_PARAMETER, REAL_VARIABLE
from support.symbolic import SymbolicBench, parsed

pytestmark = pytest.mark.algebraic

NOT_ZERO = "\N{NOT EQUAL TO} 0"
POSITIVE_VARIABLE = {"role": "variable", "domain": "positive", "unit": "1"}


@pytest.fixture
def bench(statement_validator: StatementValidator) -> SymbolicBench:
    return SymbolicBench(statement_validator, DifferentiationSolver(), DifferentiationVerifier())


@pytest.mark.parametrize(
    ("statement", "derivative"),
    [
        ("diff(3 x^4 - 2 x + 7, x)", "12*x^3 - 2"),
        ("diff(x^5/5 - x^2, x)", "x^4 - 2*x"),
        ("diff(7, x)", "0"),
        ("diff(x^3, x, 2)", "6*x"),
        ("diff(x^2*sin(x), x)", "2*x*sin(x) + x^2*cos(x)"),
        ("diff(sin(x^2), x)", "2*x*cos(x^2)"),
        ("diff(exp(sin(x)), x)", "cos(x)*exp(sin(x))"),
        ("diff(ln(x^2 + 1), x)", "2*x/(x^2 + 1)"),
        ("diff(sin(x)/x, x)", "(x*cos(x) - sin(x))/x^2"),
        ("diff(b^x, x)", "b^x*ln(b)"),
    ],
)
def test_polynomials_products_quotients_and_compositions_are_differentiated(
    bench: SymbolicBench, statement: str, derivative: str
) -> None:
    result = bench.run(statement, CALCULUS)

    assert result.equals(derivative)
    assert result.report.nature is ResultNature.EXACT
    assert result.verification.status is VerificationStatus.PASSED


@pytest.mark.parametrize(
    ("statement", "derivative"),
    [
        ("partial(x^2 y + a y^3, x)", "2*x*y"),
        ("partial(x^2 y + a y^3, y)", "x^2 + 3*a*y^2"),
        ("partial(sin(x y), x)", "y*cos(x*y)"),
    ],
)
def test_partial_derivative_keeps_the_other_variables_fixed(
    bench: SymbolicBench, statement: str, derivative: str
) -> None:
    result = bench.run(statement, CALCULUS)

    assert result.equals(derivative)
    assert result.verification.status is VerificationStatus.PASSED


def test_cancelled_factor_keeps_the_exclusion_of_its_zero(bench: SymbolicBench) -> None:
    result = bench.run("diff((x^2 - 1)/(x - 1), x)", CALCULUS)

    assert result.answer == "diff((x^2 - 1)/(x - 1), x) = 1"
    assert result.validity == [f"x - 1 {NOT_ZERO}"]
    assert result.verification.status is VerificationStatus.PASSED


def test_root_of_the_square_of_a_real_variable_is_not_reduced_to_the_variable(
    bench: SymbolicBench,
) -> None:
    result = bench.run("diff(sqrt(x^2), x)", CALCULUS)

    assert result.answer == "diff(sqrt(x^2), x) = x/abs(x)"
    assert not result.equals("1")
    assert result.validity == [f"x {NOT_ZERO}"]


def test_root_of_the_square_reduces_once_the_sign_is_declared(bench: SymbolicBench) -> None:
    result = bench.run("diff(sqrt(x^2), x)", {"x": POSITIVE_VARIABLE})

    assert result.answer == "diff(sqrt(x^2), x) = 1"
    assert result.validity == []


def test_derivative_of_a_root_excludes_the_point_where_it_does_not_exist(
    bench: SymbolicBench,
) -> None:
    result = bench.run("diff(sqrt(x), x)", CALCULUS)

    assert result.equals("1/(2*sqrt(x))")
    assert f"x {NOT_ZERO}" in result.validity


def test_division_by_a_parameter_of_unconfirmed_sign_makes_the_result_conditional(
    bench: SymbolicBench,
) -> None:
    unconfirmed = bench.run("diff(x/a, x)", CALCULUS)
    confirmed = bench.run("diff(x/b, x)", CALCULUS)

    assert unconfirmed.assumptions == [f"a {NOT_ZERO}"]
    assert unconfirmed.verification.status is VerificationStatus.CONDITIONAL
    assert unconfirmed.statuses["declared_domain_suffices"] is VerificationStatus.CONDITIONAL
    assert confirmed.assumptions == []
    assert confirmed.verification.status is VerificationStatus.PASSED


def test_expression_defined_nowhere_is_refused_before_differentiating(
    bench: SymbolicBench,
) -> None:
    diagnostic = bench.refusal("diff(x/(a - a), x)", CALCULUS)

    assert diagnostic.code is DiagnosticCode.UNDEFINED_EXPRESSION
    assert diagnostic.category is DiagnosticCategory.INVALID_INPUT
    assert f"a - a {NOT_ZERO}" in diagnostic.message


def test_result_carries_the_dimension_of_the_declared_units(bench: SymbolicBench) -> None:
    result = bench.run("diff(h - g t^2/2, t)", KINEMATICS)

    assert result.equals("-g*t")
    assert result.statuses["dimensional_consistency"] is VerificationStatus.PASSED
    assert "m s^-1" in result.check("dimensional_consistency").observed


def test_calculation_memory_shows_the_derivative_before_and_after_simplifying(
    bench: SymbolicBench,
) -> None:
    result = bench.run("diff((x^2 - 1)/(x - 1), x)", CALCULUS)

    descriptions = [step.description for step in result.report.steps]

    assert descriptions == [
        "Derivada pelas regras de derivação, antes de simplificar",
        "Resultado simplificado",
    ]
    assert result.report.steps[-1].expression == result.value


def test_verification_is_a_proof_by_the_differentiation_rules(bench: SymbolicBench) -> None:
    check = bench.run("diff(x^2*sin(x), x)", CALCULUS).check("rule_by_rule_derivative")

    assert check.kind is EvidenceKind.PROOF
    assert check.status is VerificationStatus.PASSED


@pytest.mark.parametrize("wrong", ["2*x*cos(x)", "x^2*cos(x)", "-2*x*sin(x) - x^2*cos(x)"])
def test_verifier_refuses_a_derivative_that_is_not_the_one_the_rules_give(
    bench: SymbolicBench, wrong: str
) -> None:
    honest = bench.run("diff(x^2*sin(x), x)", CALCULUS)
    claim = Equation(honest.report.answer.left, parsed(honest.problem, honest.report, wrong))

    tampered = bench.verify(honest, replace(honest.report, answer=claim))

    assert tampered.verification.status is VerificationStatus.FAILED
    assert tampered.statuses["rule_by_rule_derivative"] is VerificationStatus.FAILED
    assert tampered.check("rule_by_rule_derivative").kind is EvidenceKind.PROOF


def test_verifier_checks_higher_orders_by_repeating_the_rules(bench: SymbolicBench) -> None:
    result = bench.run("diff(sin(x)*exp(x), x, 3)", CALCULUS)

    assert result.equals("2*exp(x)*(cos(x) - sin(x))")
    assert result.statuses["rule_by_rule_derivative"] is VerificationStatus.PASSED


def test_declared_symbols_do_not_leak_between_statements(bench: SymbolicBench) -> None:
    symbols = {"x": REAL_VARIABLE, "c": POSITIVE_PARAMETER}

    assert bench.run("diff(c*x^2, x)", symbols).equals("2*c*x")
