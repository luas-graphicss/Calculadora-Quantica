import sympy

from quantum_calculator.algebra.identity import IdentityOutcome, IdentityTester

REAL = sympy.Symbol("x", real=True)
POSITIVE = sympy.Symbol("p", positive=True)
NEGATIVE = sympy.Symbol("n", negative=True)
RATE = sympy.Symbol("k", positive=True)


def _unsimplified(value: sympy.Expr) -> sympy.Expr:
    return value


def test_residual_that_simplifies_to_zero_is_proven() -> None:
    residual = sympy.diff(sympy.log(sympy.Abs(REAL)), REAL) - 1 / REAL

    assert IdentityTester().test(residual).outcome is IdentityOutcome.PROVEN


def test_residual_that_cannot_vanish_in_the_declared_domain_is_refuted_without_sampling() -> None:
    verdict = IdentityTester().test(2 * RATE * POSITIVE * sympy.exp(RATE * REAL))

    assert verdict.outcome is IdentityOutcome.REFUTED_EXACTLY
    assert verdict.witness is None


def test_identity_that_fails_only_for_negative_values_is_refuted_at_a_negative_point() -> None:
    verdict = IdentityTester().test(sympy.sqrt(REAL**2) - REAL)

    assert verdict.outcome is IdentityOutcome.REFUTED_EXACTLY
    assert verdict.witness == "x = -3/2"
    assert verdict.value_at_witness == "3"


def test_same_identity_holds_when_the_symbol_is_declared_positive() -> None:
    assert IdentityTester().test(sympy.sqrt(POSITIVE**2) - POSITIVE).outcome is (
        IdentityOutcome.PROVEN
    )


def test_agreement_at_the_sampled_points_is_not_reported_as_proof() -> None:
    identity = sympy.sin(REAL) ** 2 + sympy.cos(REAL) ** 2 - 1

    verdict = IdentityTester(simplify=_unsimplified).test(identity)

    assert verdict.outcome is IdentityOutcome.UNDECIDED
    assert verdict.witness is None


def test_numerical_disagreement_is_a_refutation_labelled_as_numerical() -> None:
    bound = sympy.Symbol("u", real=True)
    area = sympy.Integral(sympy.exp(-(bound**2)), (bound, 0, REAL))

    verdict = IdentityTester(simplify=_unsimplified).test(area)

    assert verdict.outcome is IdentityOutcome.REFUTED_NUMERICALLY
    assert verdict.witness == "x = 2"
    assert verdict.value_at_witness == "0.882081"


def test_sampled_points_stay_inside_the_declared_domain() -> None:
    verdict = IdentityTester(simplify=_unsimplified).test(sympy.sqrt(NEGATIVE**2) + NEGATIVE)

    assert verdict.outcome is IdentityOutcome.PROVEN
