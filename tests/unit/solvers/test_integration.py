from dataclasses import replace

import pytest

from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.domain.diagnostics import DiagnosticCategory, DiagnosticCode
from quantum_calculator.domain.expressions import Equation
from quantum_calculator.domain.verification import EvidenceKind, VerificationStatus
from quantum_calculator.solvers.symbolic.integration import (
    AntiderivativeSolver,
    DefiniteIntegralSolver,
)
from quantum_calculator.verification.integration import (
    AntiderivativeVerifier,
    DefiniteIntegralVerifier,
)
from support.statements import CALCULUS, KINEMATICS, POSITIVE_PARAMETER, REAL_VARIABLE
from support.symbolic import SymbolicBench, parsed

pytestmark = pytest.mark.algebraic

NOT_ZERO = "\N{NOT EQUAL TO} 0"
POSITIVE_VARIABLE = {"role": "variable", "domain": "positive", "unit": "1"}
WHOLE_INTERVAL = "em todo o intervalo de integração"


@pytest.fixture
def primitives(statement_validator: StatementValidator) -> SymbolicBench:
    return SymbolicBench(statement_validator, AntiderivativeSolver(), AntiderivativeVerifier())


@pytest.fixture
def integrals(statement_validator: StatementValidator) -> SymbolicBench:
    return SymbolicBench(statement_validator, DefiniteIntegralSolver(), DefiniteIntegralVerifier())


@pytest.mark.parametrize(
    ("statement", "primitive"),
    [
        ("integral(3 x^2 + 1, x)", "x^3 + x + C"),
        ("integral(cos(x), x)", "sin(x) + C"),
        ("integral(x*exp(x), x)", "(x - 1)*exp(x) + C"),
        ("integral(exp(-b x), x)", "-exp(-b*x)/b + C"),
        ("integral(2*x/(x^2 + 1)^2, x)", "-1/(x^2 + 1) + C"),
    ],
)
def test_covered_integrand_gets_a_primitive_with_its_integration_constant(
    primitives: SymbolicBench, statement: str, primitive: str
) -> None:
    result = primitives.run(statement, CALCULUS)

    assert result.equals(primitive)
    assert result.report.arbitrary_constants == ("C",)
    assert result.verification.status is VerificationStatus.PASSED


def test_primitive_is_verified_by_differentiating_it_back(primitives: SymbolicBench) -> None:
    check = primitives.run("integral(x^2*sin(x), x)", CALCULUS).check("primitive_derivative")

    assert check.kind is EvidenceKind.PROOF
    assert check.status is VerificationStatus.PASSED


def test_integration_constant_avoids_the_names_already_declared(primitives: SymbolicBench) -> None:
    symbols = {"x": REAL_VARIABLE, "C": POSITIVE_PARAMETER, "C_1": POSITIVE_PARAMETER}

    result = primitives.run("integral(C*x + C_1, x)", symbols)

    assert result.report.arbitrary_constants == ("C_2",)
    assert result.equals("C*x^2/2 + C_1*x + C_2")


def test_primitive_of_the_reciprocal_is_the_logarithm_of_the_modulus_on_the_real_line(
    primitives: SymbolicBench,
) -> None:
    result = primitives.run("integral(1/x, x)", CALCULUS)

    assert result.answer == "integral(1/x, x) = ln(abs(x)) + C"
    assert result.validity == [f"x {NOT_ZERO}"]
    assert result.statuses["primitive_derivative"] is VerificationStatus.PASSED


def test_modulus_is_dropped_once_the_variable_is_declared_positive(
    primitives: SymbolicBench,
) -> None:
    result = primitives.run("integral(1/x, x)", {"x": POSITIVE_VARIABLE})

    assert result.answer == "integral(1/x, x) = ln(x) + C"
    assert result.validity == []


def test_primitive_of_the_tangent_keeps_the_zeros_of_the_cosine_excluded(
    primitives: SymbolicBench,
) -> None:
    result = primitives.run("integral(tan(x), x)", CALCULUS)

    assert result.equals("-ln(abs(cos(x))) + C")
    assert result.validity == [f"cos(x) {NOT_ZERO}"]
    assert result.verification.status is VerificationStatus.PASSED


@pytest.mark.parametrize("statement", ["integral(exp(-x^2), x)", "integral(sin(x)/x, x)"])
def test_integrand_without_a_covered_primitive_is_unsupported_and_offers_no_numerical_method(
    primitives: SymbolicBench, statement: str
) -> None:
    diagnostic = primitives.refusal(statement, CALCULUS)

    assert diagnostic.code is DiagnosticCode.OUTSIDE_COVERAGE
    assert diagnostic.category is DiagnosticCategory.UNSUPPORTED_PROBLEM
    assert "aproxima" not in f"{diagnostic.message} {diagnostic.expected}".lower()


def test_primitive_that_depends_on_the_case_of_a_parameter_asks_for_its_domain(
    primitives: SymbolicBench,
) -> None:
    diagnostic = primitives.refusal("integral(exp(a x), x)", CALCULUS)

    assert diagnostic.code is DiagnosticCode.OUTSIDE_COVERAGE
    assert "nonzero" in diagnostic.expected


def test_wrong_primitive_fails_the_derivative_check(primitives: SymbolicBench) -> None:
    honest = primitives.run("integral(cos(x), x)", CALCULUS)
    claim = Equation(
        honest.report.answer.left, parsed(honest.problem, honest.report, "-sin(x) + C")
    )

    tampered = primitives.verify(honest, replace(honest.report, answer=claim))

    assert tampered.statuses["primitive_derivative"] is VerificationStatus.FAILED


@pytest.mark.parametrize(
    ("statement", "value"),
    [
        ("integral(x^2, x, 0, 1)", "1/3"),
        ("integral(x, x, 1, 0)", "-1/2"),
        ("integral(1/x^2, x, 1, 2)", "1/2"),
        ("integral(sin(x)^2, x, 0, pi)", "pi/2"),
        ("integral(exp(-b x), x, 0, 1)", "(1 - exp(-b))/b"),
        ("integral(x, x, a, a + 1)", "a + 1/2"),
    ],
)
def test_definite_integral_is_the_exact_difference_of_a_primitive(
    integrals: SymbolicBench, statement: str, value: str
) -> None:
    result = integrals.run(statement, CALCULUS)

    assert result.equals(value)
    assert result.verification.status is VerificationStatus.PASSED
    assert set(result.statuses) == {
        "primitive_derivative",
        "interval_free_of_singularities",
        "fundamental_theorem_value",
        "dimensional_consistency",
    }


@pytest.mark.parametrize(
    ("statement", "location"),
    [
        ("integral(1/x^2, x, -1, 1)", "{0}"),
        ("integral(1/x, x, -2, 3)", "{0}"),
        ("integral(1/(x - 1), x, 0, 2)", "{1}"),
        ("integral(tan(x), x, 0, 2)", "{pi/2}"),
        ("integral(ln(x), x, 0, 1)", "{0}"),
        ("integral(1/sqrt(x), x, 0, 1)", "{0}"),
        ("integral(1/x^2, x, 1, -1)", "{0}"),
    ],
)
def test_definite_integral_does_not_cross_a_singularity(
    integrals: SymbolicBench, statement: str, location: str
) -> None:
    diagnostic = integrals.refusal(statement, CALCULUS)

    assert diagnostic.code is DiagnosticCode.SINGULARITY_IN_INTERVAL
    assert diagnostic.category is DiagnosticCategory.UNSUPPORTED_PROBLEM
    assert location in diagnostic.message
    assert "impróprias" in diagnostic.expected


def test_singularity_that_depends_on_a_parameter_makes_the_value_conditional(
    integrals: SymbolicBench,
) -> None:
    result = integrals.run("integral(1/(x - a), x, 1, 2)", CALCULUS)

    assert result.assumptions == [f"x - a {NOT_ZERO} {WHOLE_INTERVAL}"]
    assert result.statuses["interval_free_of_singularities"] is VerificationStatus.CONDITIONAL
    assert result.verification.status is VerificationStatus.CONDITIONAL


def test_definite_integral_carries_the_primitive_it_used_as_a_certificate(
    integrals: SymbolicBench,
) -> None:
    result = integrals.run("integral(x^2, x, 0, 1)", CALCULUS)

    assert result.report.certificate == parsed(result.problem, result.report, "x^3/3")
    assert [step.description for step in result.report.steps] == [
        "Primitiva contínua no intervalo de integração",
        "Diferença da primitiva entre o limite superior e o inferior",
    ]


def test_wrong_value_fails_the_fundamental_theorem_check_only(integrals: SymbolicBench) -> None:
    honest = integrals.run("integral(x^2, x, 0, 1)", CALCULUS)
    claim = Equation(honest.report.answer.left, parsed(honest.problem, honest.report, "1/2"))

    tampered = integrals.verify(honest, replace(honest.report, answer=claim))

    assert tampered.statuses["fundamental_theorem_value"] is VerificationStatus.FAILED
    assert tampered.statuses["primitive_derivative"] is VerificationStatus.PASSED


def test_wrong_certificate_fails_the_derivative_check(integrals: SymbolicBench) -> None:
    honest = integrals.run("integral(x^2, x, 0, 1)", CALCULUS)
    certificate = parsed(honest.problem, honest.report, "x^2/3")

    tampered = integrals.verify(honest, replace(honest.report, certificate=certificate))

    assert tampered.statuses["primitive_derivative"] is VerificationStatus.FAILED
    assert tampered.verification.status is VerificationStatus.FAILED


def test_value_without_its_certificate_is_not_accepted(integrals: SymbolicBench) -> None:
    honest = integrals.run("integral(x^2, x, 0, 1)", CALCULUS)

    stripped = integrals.verify(honest, replace(honest.report, certificate=None))

    assert stripped.verification.status is VerificationStatus.FAILED


def test_integral_over_time_carries_the_dimension_of_the_declared_units(
    integrals: SymbolicBench,
) -> None:
    result = integrals.run("integral(g*t, t, 0, tau)", KINEMATICS)

    assert result.equals("g*tau^2/2")
    assert result.statuses["dimensional_consistency"] is VerificationStatus.PASSED
