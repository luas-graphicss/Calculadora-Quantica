import pytest

from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.domain.diagnostics import DiagnosticCategory, DiagnosticCode
from quantum_calculator.domain.verification import VerificationStatus
from quantum_calculator.notation.rendering.text import render_text
from quantum_calculator.solvers.symbolic.first_order_linear_ode import FirstOrderLinearSolver
from quantum_calculator.verification.ode_substitution import OdeSubstitutionVerifier
from support.statements import DECAY, DECAY_CONDITION, DECAY_EQUATION, REAL_VARIABLE
from support.symbolic import SymbolicBench

pytestmark = pytest.mark.algebraic

NOT_ZERO = "\N{NOT EQUAL TO} 0"
RATES = {
    **DECAY,
    "s": {"role": "parameter", "domain": "real", "unit": "1/s"},
    "a": {"role": "parameter", "domain": "real", "unit": "1/s"},
    "m": {"role": "parameter", "domain": "positive", "unit": "1"},
    "t_0": {"role": "parameter", "domain": "real", "unit": "s"},
}
PURE_NUMBERS = {
    "t": REAL_VARIABLE,
    "k": {"role": "parameter", "domain": "positive", "unit": "1"},
    "y": {"role": "function", "domain": "real", "unit": "1", "argument": "t"},
}


@pytest.fixture
def bench(statement_validator: StatementValidator) -> SymbolicBench:
    return SymbolicBench(statement_validator, FirstOrderLinearSolver(), OdeSubstitutionVerifier())


def test_general_solution_of_the_decay_carries_an_arbitrary_constant(bench: SymbolicBench) -> None:
    result = bench.run(DECAY_EQUATION, DECAY)

    assert result.answer == "y(t) = C*exp(-k*t)"
    assert result.report.arbitrary_constants == ("C",)
    assert result.statuses == {
        "equation_residual": VerificationStatus.PASSED,
        "declared_domain_suffices": VerificationStatus.PASSED,
    }
    assert [skipped.identifier for skipped in result.verification.not_performed] == [
        "initial_condition",
        "dimensional_consistency",
    ]


def test_initial_condition_fixes_the_constant(bench: SymbolicBench) -> None:
    result = bench.run(DECAY_EQUATION, DECAY, conditions=[DECAY_CONDITION])

    assert result.answer == "y(t) = y_0*exp(-k*t)"
    assert result.report.arbitrary_constants == ()
    assert result.statuses["equation_residual"] is VerificationStatus.PASSED
    assert result.statuses["initial_condition"] is VerificationStatus.PASSED
    assert result.verification.status is VerificationStatus.PASSED


def test_condition_away_from_the_origin_shifts_the_exponential(bench: SymbolicBench) -> None:
    result = bench.run(DECAY_EQUATION, RATES, conditions=["y(t_0) = y_0"])

    assert result.equals("y_0*exp(-k*(t - t_0))")
    assert result.verification.status is VerificationStatus.PASSED


@pytest.mark.parametrize(
    "equation", ["y' + k*y = s", "y' = s - k*y", "m*y' = m*s - m*k*y", "0 = y' + k*y - s"]
)
def test_equivalent_writings_of_the_equation_give_the_same_relaxation(
    bench: SymbolicBench, equation: str
) -> None:
    result = bench.run(equation, RATES, conditions=[DECAY_CONDITION])

    assert result.equals("s/k + (y_0 - s/k)*exp(-k*t)")
    assert result.assumptions == []
    assert result.verification.status is VerificationStatus.PASSED


def test_solution_is_written_around_its_equilibrium(bench: SymbolicBench) -> None:
    result = bench.run("y' = s - k*y", RATES, conditions=[DECAY_CONDITION])

    assert result.answer == "y(t) = (y_0 - s/k)*exp(-k*t) + s/k"
    assert render_text(result.report.steps[0].expression) == "y'(t) = -k*y(t) + s"


def test_vanishing_rate_gives_the_straight_line(bench: SymbolicBench) -> None:
    particular = bench.run("y' = s", RATES, conditions=[DECAY_CONDITION])
    general = bench.run("y' = s", RATES)

    assert particular.equals("y_0 + s*t")
    assert general.equals("s*t + C")
    assert particular.report.special_cases == ()
    assert particular.verification.status is VerificationStatus.PASSED


def test_rate_of_unconfirmed_sign_makes_the_formula_conditional_and_lists_the_other_case(
    bench: SymbolicBench,
) -> None:
    result = bench.run("y' = a*y + s", RATES, conditions=[DECAY_CONDITION])

    (special,) = result.report.special_cases
    assert result.equals("-s/a + (y_0 + s/a)*exp(a*t)")
    assert result.assumptions == [f"a {NOT_ZERO}"]
    assert render_text(special.when) == "a = 0"
    assert render_text(special.answer) == "y(t) = s*t + y_0"
    assert result.statuses["equation_residual"] is VerificationStatus.PASSED
    assert result.statuses["declared_domain_suffices"] is VerificationStatus.CONDITIONAL
    assert result.verification.status is VerificationStatus.CONDITIONAL


def test_homogeneous_equation_needs_no_hypothesis_on_the_rate(bench: SymbolicBench) -> None:
    result = bench.run("y' = a*y", RATES, conditions=[DECAY_CONDITION])

    assert result.answer == "y(t) = y_0*exp(a*t)"
    assert result.assumptions == []
    assert result.report.special_cases == ()
    assert result.verification.status is VerificationStatus.PASSED


def test_solution_keeps_the_dimension_of_the_unknown(bench: SymbolicBench) -> None:
    result = bench.run("y' = s - k*y", RATES, conditions=[DECAY_CONDITION])

    assert result.statuses["dimensional_consistency"] is VerificationStatus.PASSED


@pytest.mark.parametrize(
    ("equation", "reason"),
    [
        ("y' = -k*y^2", "não é linear"),
        ("y' = -k*sin(y)", "não é linear"),
        ("y*y' = -k", "não é linear"),
        ("y' = -k*t*y", "dependem de t"),
        ("y' = -k*y + exp(-t)", "dependem de t"),
        ("y' - y' = k*y", "se cancela"),
    ],
)
def test_equation_outside_the_linear_constant_family_is_unsupported(
    bench: SymbolicBench, equation: str, reason: str
) -> None:
    diagnostic = bench.refusal(equation, PURE_NUMBERS)

    assert diagnostic.code is DiagnosticCode.OUTSIDE_COVERAGE
    assert diagnostic.category is DiagnosticCategory.UNSUPPORTED_PROBLEM
    assert reason in diagnostic.message
