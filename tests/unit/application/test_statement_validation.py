import pytest

from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCategory,
    DiagnosticCode,
    ProblemRejectedError,
)
from quantum_calculator.domain.dimensions import LENGTH, TIME, Dimension
from quantum_calculator.domain.statements import CardSelection, StatementSpec, ValidatedStatement
from support.statements import (
    CALCULUS,
    DECAY,
    DECAY_CONDITION,
    DECAY_EQUATION,
    DECAY_SOLUTION,
    KINEMATICS,
    LAMBDA,
    POSITIVE_PARAMETER,
    REAL_VARIABLE,
    statement_spec,
)

GENERAL_SOLUTION = "ode.first_order_linear.general_solution"
INITIAL_VALUE = "ode.first_order_linear.initial_value"
CANDIDATE_REVIEW = "ode.first_order_linear.candidate_review"


def _validate(validator: StatementValidator, spec: StatementSpec) -> ValidatedStatement:
    return validator.validate(spec)


def _diagnostics(validator: StatementValidator, spec: StatementSpec) -> tuple[Diagnostic, ...]:
    with pytest.raises(ProblemRejectedError) as rejection:
        validator.validate(spec)
    return rejection.value.diagnostics


def _only(validator: StatementValidator, spec: StatementSpec) -> Diagnostic:
    (diagnostic,) = _diagnostics(validator, spec)
    return diagnostic


def _excerpt(diagnostic: Diagnostic) -> str:
    excerpt = diagnostic.excerpt
    assert excerpt is not None
    return excerpt.text[excerpt.start : excerpt.end]


def test_the_only_compatible_card_is_suggested(statement_validator: StatementValidator) -> None:
    problem = _validate(statement_validator, statement_spec("diff(x^2, x)", CALCULUS))

    assert problem.card.identifier == "calculus.derivative"
    assert problem.selection is CardSelection.SUGGESTED


def test_card_named_in_the_input_is_confirmed(statement_validator: StatementValidator) -> None:
    spec = statement_spec("integral(x^2, x, 0, 1)", CALCULUS, problem="calculus.definite_integral")

    assert _validate(statement_validator, spec).selection is CardSelection.CONFIRMED


@pytest.mark.parametrize(
    ("fields", "card"),
    [
        ({}, GENERAL_SOLUTION),
        ({"conditions": [DECAY_CONDITION]}, INITIAL_VALUE),
        ({"conditions": [DECAY_CONDITION], "candidate": DECAY_SOLUTION}, CANDIDATE_REVIEW),
    ],
)
def test_fields_given_with_an_equation_select_its_card(
    statement_validator: StatementValidator, fields: dict[str, object], card: str
) -> None:
    problem = _validate(statement_validator, statement_spec(DECAY_EQUATION, DECAY, **fields))

    assert problem.card.identifier == card
    assert len(problem.conditions) == len(problem.spec.conditions)
    assert (problem.candidate is None) is (problem.spec.candidate is None)


def test_expression_without_an_operation_asks_which_one_is_meant(
    statement_validator: StatementValidator,
) -> None:
    diagnostic = _only(statement_validator, statement_spec("x^2*sin(x)", CALCULUS))

    assert diagnostic.code is DiagnosticCode.AMBIGUOUS_PROBLEM
    assert diagnostic.category is DiagnosticCategory.AMBIGUOUS_INPUT
    assert "diff(...)" in diagnostic.expected
    assert "integral(...)" in diagnostic.expected


def test_candidate_without_condition_lists_the_cards_and_what_each_requires(
    statement_validator: StatementValidator,
) -> None:
    spec = statement_spec(DECAY_EQUATION, DECAY, candidate=DECAY_SOLUTION)

    diagnostic = _only(statement_validator, spec)

    assert diagnostic.code is DiagnosticCode.AMBIGUOUS_PROBLEM
    assert diagnostic.pointer == "/problem"
    assert f"{GENERAL_SOLUTION} (sem conditions nem candidate)" in diagnostic.expected
    assert f"{INITIAL_VALUE} (exige conditions)" in diagnostic.expected
    assert f"{CANDIDATE_REVIEW} (exige conditions e candidate)" in diagnostic.expected


def test_confirmed_card_requests_its_missing_condition_before_calculating(
    statement_validator: StatementValidator,
) -> None:
    spec = statement_spec(DECAY_EQUATION, DECAY, problem=INITIAL_VALUE)

    diagnostic = _only(statement_validator, spec)

    assert diagnostic.code is DiagnosticCode.MISSING_FIELD
    assert diagnostic.pointer == "/conditions"
    assert diagnostic.category is DiagnosticCategory.INVALID_INPUT


def test_confirmed_review_card_requests_condition_and_candidate_together(
    statement_validator: StatementValidator,
) -> None:
    spec = statement_spec(DECAY_EQUATION, DECAY, problem=CANDIDATE_REVIEW)

    diagnostics = _diagnostics(statement_validator, spec)

    assert [(item.code, item.pointer) for item in diagnostics] == [
        (DiagnosticCode.MISSING_FIELD, "/conditions"),
        (DiagnosticCode.MISSING_FIELD, "/candidate"),
    ]


def test_confirmed_card_refuses_a_field_it_does_not_use(
    statement_validator: StatementValidator,
) -> None:
    spec = statement_spec(
        DECAY_EQUATION, DECAY, problem=GENERAL_SOLUTION, conditions=[DECAY_CONDITION]
    )

    diagnostic = _only(statement_validator, spec)

    assert diagnostic.code is DiagnosticCode.UNEXPECTED_FIELD
    assert diagnostic.pointer == "/conditions"


def test_card_of_another_shape_is_refused_with_the_compatible_ones(
    statement_validator: StatementValidator,
) -> None:
    spec = statement_spec("integral(x^2, x)", CALCULUS, problem="calculus.derivative")

    diagnostic = _only(statement_validator, spec)

    assert diagnostic.code is DiagnosticCode.CARD_MISMATCH
    assert "calculus.antiderivative" in diagnostic.expected


def test_card_outside_the_catalog_is_an_unsupported_problem(
    statement_validator: StatementValidator,
) -> None:
    spec = statement_spec("diff(x^2, x)", CALCULUS, problem="calculus.limit")

    diagnostic = _only(statement_validator, spec)

    assert diagnostic.code is DiagnosticCode.UNKNOWN_PROBLEM
    assert diagnostic.category is DiagnosticCategory.UNSUPPORTED_PROBLEM
    assert "calculus.derivative" in diagnostic.expected


def test_equation_no_card_covers_is_an_unsupported_problem(
    statement_validator: StatementValidator,
) -> None:
    diagnostic = _only(statement_validator, statement_spec("x^2 = 4", CALCULUS))

    assert diagnostic.code is DiagnosticCode.NO_COMPATIBLE_CARD
    assert diagnostic.category is DiagnosticCategory.UNSUPPORTED_PROBLEM


def test_undeclared_free_variable_is_refused_at_its_position(
    statement_validator: StatementValidator,
) -> None:
    diagnostic = _only(statement_validator, statement_spec("diff(x^2 + z, x)", CALCULUS))

    assert diagnostic.code is DiagnosticCode.UNDECLARED_SYMBOL
    assert diagnostic.pointer == "/statement"
    assert _excerpt(diagnostic) == "z"
    assert "x, y, a, b" in diagnostic.expected


def test_dimensional_argument_of_a_transcendental_function_is_refused(
    statement_validator: StatementValidator,
) -> None:
    diagnostic = _only(statement_validator, statement_spec("diff(exp(-t), t)", KINEMATICS))

    assert diagnostic.code is DiagnosticCode.DIMENSIONAL_ARGUMENT
    assert _excerpt(diagnostic) == "-t"
    assert "adimensional" in diagnostic.expected


def test_argument_divided_by_a_scale_of_the_same_unit_is_accepted(
    statement_validator: StatementValidator,
) -> None:
    problem = _validate(statement_validator, statement_spec("diff(exp(-t/tau), t)", KINEMATICS))

    assert problem.result_dimension == Dimension(time=-1)


def test_terms_of_different_dimensions_are_refused(statement_validator: StatementValidator) -> None:
    diagnostic = _only(statement_validator, statement_spec("diff(h + t, t)", KINEMATICS))

    assert diagnostic.code is DiagnosticCode.DIMENSION_MISMATCH
    assert _excerpt(diagnostic) == "h + t"
    assert "m" in diagnostic.message
    assert "s" in diagnostic.message


def test_exponent_with_dimension_is_refused(statement_validator: StatementValidator) -> None:
    diagnostic = _only(statement_validator, statement_spec("diff(h^t, t)", KINEMATICS))

    assert diagnostic.code is DiagnosticCode.DIMENSIONAL_ARGUMENT
    assert _excerpt(diagnostic) == "t"


@pytest.mark.parametrize(
    ("statement", "dimension"),
    [
        ("diff(h - g t^2/2, t)", LENGTH / TIME),
        ("diff(h - g t^2/2, t, 2)", LENGTH / TIME**2),
        ("integral(g t, t)", LENGTH),
        ("integral(g, t, 0, tau)", LENGTH / TIME),
        ("diff(sqrt(h/g), t)", Dimension()),
    ],
)
def test_result_dimension_follows_the_declared_units(
    statement_validator: StatementValidator, statement: str, dimension: Dimension
) -> None:
    problem = _validate(statement_validator, statement_spec(statement, KINEMATICS))

    assert problem.result_dimension == dimension


def test_integration_limit_must_have_the_dimension_of_the_variable(
    statement_validator: StatementValidator,
) -> None:
    diagnostic = _only(statement_validator, statement_spec("integral(g, t, 0, h)", KINEMATICS))

    assert diagnostic.code is DiagnosticCode.DIMENSION_MISMATCH
    assert _excerpt(diagnostic) == "h"


def test_derivative_with_respect_to_a_parameter_is_refused(
    statement_validator: StatementValidator,
) -> None:
    diagnostic = _only(statement_validator, statement_spec("diff(a*x^2, a)", CALCULUS))

    assert diagnostic.code is DiagnosticCode.NOT_A_VARIABLE


def test_ordinary_derivative_with_a_second_variable_is_ambiguous_and_the_partial_is_not(
    statement_validator: StatementValidator,
) -> None:
    ordinary = _only(statement_validator, statement_spec("diff(x^2*y, x)", CALCULUS))
    partial = _validate(statement_validator, statement_spec("partial(x^2*y, x)", CALCULUS))

    assert ordinary.code is DiagnosticCode.AMBIGUOUS_DERIVATIVE
    assert "partial(...)" in ordinary.expected
    assert partial.card.identifier == "calculus.derivative"


def test_integration_variable_in_its_own_limit_is_refused(
    statement_validator: StatementValidator,
) -> None:
    diagnostic = _only(statement_validator, statement_spec("integral(x^2, x, 0, x)", CALCULUS))

    assert diagnostic.code is DiagnosticCode.BOUND_VARIABLE_MISUSE
    assert _excerpt(diagnostic) == "x"


@pytest.mark.parametrize(
    ("statement", "symbols", "excerpt"),
    [
        ("diff(diff(x^3, x), x)", CALCULUS, "diff(x^3, x)"),
        ("integral(diff(x^3, x), x)", CALCULUS, "diff(x^3, x)"),
        ("y'' = -k*k*y", DECAY, "y''"),
        ("y'(t) = -k*y(2*t)", DECAY, "y(2*t)"),
    ],
)
def test_statement_outside_the_card_family_is_an_unsupported_problem(
    statement_validator: StatementValidator,
    statement: str,
    symbols: dict[str, dict[str, str]],
    excerpt: str,
) -> None:
    diagnostic = _only(statement_validator, statement_spec(statement, symbols))

    assert diagnostic.code is DiagnosticCode.OUTSIDE_COVERAGE
    assert diagnostic.category is DiagnosticCategory.UNSUPPORTED_PROBLEM
    assert _excerpt(diagnostic) == excerpt


def test_equation_with_two_unknown_functions_is_outside_the_coverage(
    statement_validator: StatementValidator,
) -> None:
    symbols = {**DECAY, "z": DECAY["y"]}

    diagnostic = _only(statement_validator, statement_spec("y' = -k*z", symbols))

    assert diagnostic.code is DiagnosticCode.OUTSIDE_COVERAGE
    assert "y, z" in diagnostic.message


@pytest.mark.parametrize("condition", ["y(t) = y_0", "y'(0) = y_0", "y(0) = y_0*t", "y_0 = y(0)"])
def test_condition_that_does_not_fix_the_function_at_a_point_is_refused(
    statement_validator: StatementValidator, condition: str
) -> None:
    spec = statement_spec(DECAY_EQUATION, DECAY, conditions=[condition])

    diagnostics = _diagnostics(statement_validator, spec)

    assert DiagnosticCode.MALFORMED_CONDITION in {item.code for item in diagnostics}
    assert {item.pointer for item in diagnostics} == {"/conditions/0"}


def test_second_condition_is_refused_for_a_first_order_equation(
    statement_validator: StatementValidator,
) -> None:
    spec = statement_spec(DECAY_EQUATION, DECAY, conditions=[DECAY_CONDITION, "y(1) = y_0"])

    diagnostics = _diagnostics(statement_validator, spec)

    assert (DiagnosticCode.MALFORMED_CONDITION, "/conditions/1") in {
        (item.code, item.pointer) for item in diagnostics
    }


@pytest.mark.parametrize("candidate", ["y(t) = 2*y(t)", "y(0) = y_0", "y_0*exp(-k*t)"])
def test_candidate_that_does_not_give_the_function_explicitly_is_refused(
    statement_validator: StatementValidator, candidate: str
) -> None:
    spec = statement_spec(DECAY_EQUATION, DECAY, conditions=[DECAY_CONDITION], candidate=candidate)

    diagnostic = _only(statement_validator, spec)

    assert diagnostic.code is DiagnosticCode.MALFORMED_CANDIDATE
    assert diagnostic.pointer == "/candidate"


def test_zero_is_accepted_as_a_point_of_any_dimension(
    statement_validator: StatementValidator,
) -> None:
    spec = statement_spec(DECAY_EQUATION, DECAY, conditions=[DECAY_CONDITION])

    assert _validate(statement_validator, spec).result_dimension == Dimension()


def test_condition_at_a_point_of_the_wrong_dimension_is_refused(
    statement_validator: StatementValidator,
) -> None:
    spec = statement_spec(DECAY_EQUATION, DECAY, conditions=["y(k) = y_0"])

    diagnostic = _only(statement_validator, spec)

    assert diagnostic.code is DiagnosticCode.DIMENSION_MISMATCH
    assert diagnostic.pointer == "/conditions/0"
    assert _excerpt(diagnostic) == "k"


@pytest.mark.parametrize("name", ["pi", "d", "sin", "diff", "integral"])
def test_reserved_name_cannot_be_declared_as_a_symbol(
    statement_validator: StatementValidator, name: str
) -> None:
    symbols = {"x": REAL_VARIABLE, name: POSITIVE_PARAMETER}

    diagnostic = _only(statement_validator, statement_spec("diff(x^2, x)", symbols))

    assert diagnostic.code is DiagnosticCode.RESERVED_NAME
    assert diagnostic.pointer == f"/symbols/{name}"


def test_same_symbol_declared_in_two_spellings_is_a_duplicate(
    statement_validator: StatementValidator,
) -> None:
    symbols = {"x": REAL_VARIABLE, "lambda": POSITIVE_PARAMETER, LAMBDA: POSITIVE_PARAMETER}

    diagnostic = _only(statement_validator, statement_spec("diff(lambda*x, x)", symbols))

    assert diagnostic.code is DiagnosticCode.DUPLICATE_FIELD
    assert diagnostic.pointer == f"/symbols/{LAMBDA}"


def test_every_defect_of_the_symbol_table_is_reported_in_one_pass(
    statement_validator: StatementValidator,
) -> None:
    symbols = {
        "x": {"role": "unknown", "domain": "complex", "unit": "furlong"},
        "2x": REAL_VARIABLE,
        "f": {"role": "function", "domain": "real", "unit": "1"},
        "g": {"role": "function", "domain": "real", "unit": "1", "argument": "q"},
        "k": {"role": "parameter", "domain": "real", "unit": "1", "argument": "x"},
    }

    diagnostics = _diagnostics(statement_validator, statement_spec("diff(x^2, x)", symbols))

    assert [(item.code, item.pointer) for item in diagnostics] == [
        (DiagnosticCode.UNKNOWN_OPTION, "/symbols/x/role"),
        (DiagnosticCode.UNKNOWN_OPTION, "/symbols/x/domain"),
        (DiagnosticCode.UNKNOWN_UNIT, "/symbols/x/unit"),
        (DiagnosticCode.INVALID_SYMBOL_NAME, "/symbols/2x"),
        (DiagnosticCode.MISSING_FIELD, "/symbols/f/argument"),
        (DiagnosticCode.UNEXPECTED_FIELD, "/symbols/k/argument"),
        (DiagnosticCode.NOT_A_VARIABLE, "/symbols/g/argument"),
    ]


def test_unknown_notation_is_refused_with_the_accepted_ones(
    statement_validator: StatementValidator,
) -> None:
    diagnostic = _only(statement_validator, statement_spec("diff(x^2, x)", CALCULUS, "mathml"))

    assert diagnostic.code is DiagnosticCode.UNKNOWN_OPTION
    assert diagnostic.pointer == "/notation"
    assert "text, latex" in diagnostic.expected


def test_text_and_latex_give_the_same_canonical_problem(
    statement_validator: StatementValidator,
) -> None:
    text = _validate(statement_validator, statement_spec(DECAY_EQUATION, DECAY))
    latex = _validate(
        statement_validator, statement_spec("\\frac{dy}{dt} = -k y(t)", DECAY, "latex")
    )

    assert text.statement == latex.statement
    assert text.card is latex.card
    assert text.symbols == latex.symbols


def test_over_long_statement_is_refused_without_echoing_it_back(
    statement_validator: StatementValidator,
) -> None:
    spec = statement_spec("diff(" + "+".join(["x"] * 300) + ", x)", CALCULUS)

    diagnostic = _only(statement_validator, spec)

    assert diagnostic.code is DiagnosticCode.STATEMENT_TOO_LONG
    assert diagnostic.category is DiagnosticCategory.BUDGET_EXCEEDED
    assert diagnostic.excerpt is None
