import math

import pytest

from quantum_calculator.application.numerical.estimates import MAX_MEMORY_BYTES, MAX_OPERATIONS
from quantum_calculator.application.numerical.validator import NumericalValidator
from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCategory,
    ProblemRejectedError,
)
from quantum_calculator.domain.numerical.problems import (
    EvolutionProblem,
    FiniteBasisProblem,
    InitialValueProblem,
    PotentialModel,
    QuadratureProblem,
    ScaledGrid,
    SpectrumProblem,
    SymbolValue,
)
from support.documents import ProblemDocument
from support.numerical import ELECTRON_MASS, ELECTRON_VOLT_IN_JOULES, NANOMETER, REDUCED_PLANCK
from support.numerical_documents import REFUSALS, REJECTED, numerical_document, numerical_spec

WELL = "electron_box_1nm_discrete"
OSCILLATOR = "harmonic_oscillator_1ev"
BEAT = "electron_box_1nm_beat"
SPIN = "spin_half_measurement"
DECAY = "decay_trajectory"
SINE = "sine_quadrature"
NANOMETER_PARAMETER = {"role": "parameter", "domain": "positive", "unit": "nm", "value": 2}
LENGTH_VARIABLE = {"role": "variable", "domain": "real", "unit": "m"}
PRE_SOLVE_REFUSALS = [case for case in REFUSALS if case["category"] != "non_convergent"]


def _diagnostics(
    validator: NumericalValidator, document: ProblemDocument
) -> tuple[Diagnostic, ...]:
    with pytest.raises(ProblemRejectedError) as rejection:
        validator.validate(numerical_spec(document))
    return rejection.value.diagnostics


def test_well_is_scaled_by_its_width_and_by_the_matching_energy(
    numerical_validator: NumericalValidator,
) -> None:
    problem = numerical_validator.validate(numerical_spec(numerical_document(WELL)))

    assert isinstance(problem, SpectrumProblem)
    assert problem.scales.length == pytest.approx(NANOMETER, rel=1e-15)
    assert problem.scales.energy == pytest.approx(
        REDUCED_PLANCK**2 / (ELECTRON_MASS * NANOMETER**2), rel=1e-14
    )
    assert problem.scales.time == pytest.approx(REDUCED_PLANCK / problem.scales.energy, rel=1e-14)
    assert problem.grid == ScaledGrid(left=0.0, right=1.0, subintervals=512)
    assert problem.potential is PotentialModel.ZERO
    assert problem.levels == 3
    assert problem.energy_unit.symbol == "eV"
    assert not problem.is_truncated_domain


def test_oscillator_is_scaled_by_its_length_and_cut_at_the_requested_half_width(
    numerical_validator: NumericalValidator,
) -> None:
    problem = numerical_validator.validate(numerical_spec(numerical_document(OSCILLATOR)))

    quantum = float(ELECTRON_VOLT_IN_JOULES)
    assert isinstance(problem, SpectrumProblem)
    assert problem.scales.energy == pytest.approx(quantum, rel=1e-15)
    assert problem.scales.length == pytest.approx(
        REDUCED_PLANCK / math.sqrt(ELECTRON_MASS * quantum), rel=1e-14
    )
    assert problem.grid == ScaledGrid(left=-8.0, right=8.0, subintervals=1024)
    assert problem.potential is PotentialModel.HARMONIC
    assert problem.is_truncated_domain


def test_evolution_duration_is_expressed_in_the_time_scale_of_the_well(
    numerical_validator: NumericalValidator,
) -> None:
    problem = numerical_validator.validate(numerical_spec(numerical_document(BEAT)))

    assert isinstance(problem, EvolutionProblem)
    assert problem.scaled_duration == pytest.approx(3.666077985e-15 / problem.scales.time)
    assert problem.coefficients == (1 + 0j, 1 + 0j)
    assert problem.normalize
    assert (problem.grid.subintervals, problem.steps, problem.samples) == (256, 1024, 9)


def test_integral_bounds_and_tolerances_are_read_as_numbers(
    numerical_validator: NumericalValidator,
) -> None:
    problem = numerical_validator.validate(numerical_spec(numerical_document(SINE)))

    assert isinstance(problem, QuadratureProblem)
    assert (problem.variable, problem.lower, problem.upper) == ("x", 0.0, math.pi)
    assert (problem.absolute_tolerance, problem.relative_tolerance) == (1e-12, 1e-12)
    assert problem.subdivision_limit == 50
    assert problem.result_unit == "1"


def test_parameter_value_is_converted_once_to_coherent_si_units(
    numerical_validator: NumericalValidator,
) -> None:
    document = (
        numerical_document(SINE)
        .with_value("/statement", "integral(x^2, x, 0, a)")
        .with_value("/symbols", {"x": LENGTH_VARIABLE, "a": NANOMETER_PARAMETER})
    )

    problem = numerical_validator.validate(numerical_spec(document))

    assert isinstance(problem, QuadratureProblem)
    assert problem.values == (SymbolValue("a", 2e-9),)
    assert problem.upper == 2e-9
    assert problem.result_unit == "m^3"
    assert [item.origin for item in problem.context.inputs if item.name == "a"] == ["entrada: 2 nm"]


def test_trajectory_interval_starts_at_the_initial_condition_and_ends_where_asked(
    numerical_validator: NumericalValidator,
) -> None:
    document = (
        numerical_document(DECAY)
        .with_value("/symbols/t/unit", "ms")
        .with_value("/symbols/k/unit", "1/ms")
    )

    problem = numerical_validator.validate(numerical_spec(document))

    assert isinstance(problem, InitialValueProblem)
    (component,) = problem.components
    assert (component.function, component.unit, component.initial_value) == ("y", "1", 1.0)
    assert (problem.variable, problem.variable_unit) == ("t", "s")
    assert (problem.start, problem.end, problem.samples) == (0.0, 0.005, 51)
    assert problem.values == (SymbolValue("k", 1000.0),)
    assert (problem.relative_tolerance, problem.absolute_tolerance) == (1e-10, 1e-12)


def test_complex_state_and_basis_are_kept_as_given_with_the_requested_normalization(
    numerical_validator: NumericalValidator,
) -> None:
    rotated = numerical_document("spin_half_measurement_rotated")

    problem = numerical_validator.validate(numerical_spec(rotated))

    assert isinstance(problem, FiniteBasisProblem)
    assert problem.state == (1j, 1j)
    assert problem.normalize
    assert problem.observable == ((1 + 0j, 0j), (0j, -1 + 0j))
    assert problem.basis == ((0.6 + 0j, 0.8 + 0j), (-0.8 + 0j, 0.6 + 0j))
    assert problem.tolerance == 1e-12


def test_context_records_card_hypotheses_resolution_constants_and_estimate(
    numerical_validator: NumericalValidator,
) -> None:
    context = numerical_validator.validate(numerical_spec(numerical_document(WELL))).context

    assert context.card.identifier == "quantum.infinite_square_well.discrete_spectrum"
    assert [item.key for item in context.hypotheses] == [
        "walls",
        "interior_potential",
        "boundary_wavefunction",
    ]
    assert [(item.name, item.value) for item in context.resolution] == [
        ("subintervals", "512"),
        ("levels", "3"),
    ]
    assert {constant.identifier for constant in context.constants} == {
        "planck_constant",
        "electron_mass",
        "electron_volt",
    }
    assert 0 < context.estimate.memory_bytes <= MAX_MEMORY_BYTES
    assert 0 < context.estimate.operations <= MAX_OPERATIONS


@pytest.mark.parametrize("case", PRE_SOLVE_REFUSALS, ids=lambda case: case["file"])
def test_single_defect_is_refused_with_one_diagnostic_at_the_defective_field(
    numerical_validator: NumericalValidator, case: dict[str, str]
) -> None:
    document = ProblemDocument.load(REJECTED / case["file"])

    (diagnostic,) = _diagnostics(numerical_validator, document)

    assert diagnostic.code.value == case["code"]
    assert diagnostic.pointer == case["pointer"]
    assert diagnostic.category.value == case["category"]
    assert diagnostic.expected


@pytest.mark.parametrize(
    ("case", "pointer", "value", "code", "reported_at"),
    [
        (WELL, "/numerics/levels", 0, "number_out_of_range", "/numerics/levels"),
        (WELL, "/numerics/levels", "2.5", "number_out_of_range", "/numerics/levels"),
        (WELL, "/numerics/levels", 33, "resource_limit_exceeded", "/numerics/levels"),
        (WELL, "/numerics/subintervals", 12, "number_out_of_range", "/numerics/levels"),
        (WELL, "/requested/unit", "nm", "dimension_mismatch", "/requested/unit"),
        (
            WELL,
            "/requested/significant_digits",
            0,
            "number_out_of_range",
            "/requested/significant_digits",
        ),
        (WELL, "/hypotheses/walls", "finite", "unsupported_hypothesis", "/hypotheses/walls"),
        (WELL, "/parameters/width/value", 0, "non_positive_quantity", "/parameters/width/value"),
        (WELL, "/parameters/width/unit", "s", "dimension_mismatch", "/parameters/width/unit"),
        (OSCILLATOR, "/numerics/half_width", 65, "number_out_of_range", "/numerics/half_width"),
        (BEAT, "/numerics/samples", 10, "number_out_of_range", "/numerics/samples"),
        (BEAT, "/requested/unit", "eV", "unexpected_field", "/requested/unit"),
        (SPIN, "/observable/matrix", [[1, 0, 0], [0, 1, 0]], "invalid_shape", "/observable/matrix"),
        (SPIN, "/basis", [[1, 0]], "invalid_shape", "/basis"),
        (SPIN, "/observable/unit", "furlong", "unknown_unit", "/observable/unit"),
        (SPIN, "/numerics/tolerance", 1, "number_out_of_range", "/numerics/tolerance"),
        (DECAY, "/numerics/end", -1, "number_out_of_range", "/numerics/end"),
        (DECAY, "/numerics/samples", 1, "number_out_of_range", "/numerics/samples"),
        (
            DECAY,
            "/numerics/relative_tolerance",
            "1e-15",
            "number_out_of_range",
            "/numerics/relative_tolerance",
        ),
        (DECAY, "/symbols/k/value", -1, "number_out_of_range", "/symbols/k/value"),
        (DECAY, "/symbols/t/value", 0, "unexpected_field", "/symbols/t/value"),
        (DECAY, "/equations", ["y'' = -k*y"], "outside_coverage", "/equations/0"),
        (DECAY, "/equations", ["y' = -k*z"], "undeclared_symbol", "/equations/0"),
        (DECAY, "/conditions", ["y(t) = 1"], "malformed_condition", "/conditions/0"),
        (DECAY, "/notation", "mathml", "unknown_option", "/notation"),
        (SINE, "/statement", "integral(sin(x), x)", "card_mismatch", "/statement"),
        (SINE, "/statement", "diff(sin(x), x)", "card_mismatch", "/statement"),
        (SINE, "/statement", "integral(sin(x), x, 0, 1/0)", "undefined_expression", "/statement"),
        (SINE, "/requested/unit", "J", "unexpected_field", "/requested/unit"),
        (
            SINE,
            "/numerics/subdivision_limit",
            0,
            "number_out_of_range",
            "/numerics/subdivision_limit",
        ),
        (SINE, "/problem", "calculus.nothing", "unknown_problem", "/problem"),
    ],
)
def test_defective_field_is_refused_where_it_was_given(
    numerical_validator: NumericalValidator,
    case: str,
    pointer: str,
    value: object,
    code: str,
    reported_at: str,
) -> None:
    document = numerical_document(case).with_value(pointer, value)

    diagnostics = _diagnostics(numerical_validator, document)

    assert [(item.code.value, item.pointer) for item in diagnostics] == [(code, reported_at)]


@pytest.mark.parametrize(
    ("case", "section"),
    [
        (WELL, "hypotheses"),
        (WELL, "parameters"),
        (WELL, "requested"),
        (WELL, "numerics"),
        (SPIN, "state"),
        (SPIN, "observable"),
        (DECAY, "equations"),
        (DECAY, "conditions"),
        (DECAY, "symbols"),
        (SINE, "statement"),
        (BEAT, "initial_state"),
    ],
)
def test_missing_section_is_reported_once_without_derived_diagnostics(
    numerical_validator: NumericalValidator, case: str, section: str
) -> None:
    document = numerical_document(case).without(f"/{section}")

    (diagnostic,) = _diagnostics(numerical_validator, document)

    assert (diagnostic.code.value, diagnostic.pointer) == ("missing_field", f"/{section}")


def test_section_the_card_does_not_use_is_refused(
    numerical_validator: NumericalValidator,
) -> None:
    document = numerical_document(SINE).with_value("/hypotheses", {"walls": "infinite"})

    (diagnostic,) = _diagnostics(numerical_validator, document)

    assert (diagnostic.code.value, diagnostic.pointer) == ("unexpected_field", "/hypotheses")


def test_second_function_without_equation_or_condition_leaves_the_system_open(
    numerical_validator: NumericalValidator,
) -> None:
    other = {"role": "function", "domain": "real", "unit": "1", "argument": "t"}
    document = (
        numerical_document(DECAY)
        .with_value("/symbols/z", other)
        .with_value("/equations", ["y' = -k*z"])
    )

    (diagnostic,) = _diagnostics(numerical_validator, document)

    assert (diagnostic.code.value, diagnostic.pointer) == ("missing_field", "/equations")
    assert "z aparece no sistema" in diagnostic.message


def test_conditions_at_different_instants_are_incompatible(
    numerical_validator: NumericalValidator,
) -> None:
    other = {"role": "function", "domain": "real", "unit": "1", "argument": "t"}
    later = {"role": "parameter", "domain": "positive", "unit": "s", "value": 1}
    document = (
        numerical_document(DECAY)
        .with_value("/symbols/z", other)
        .with_value("/symbols/t_1", later)
        .with_value("/equations", ["y' = -k*z", "z' = k*y"])
        .with_value("/conditions", ["y(0) = 1", "z(t_1) = 0"])
    )

    (diagnostic,) = _diagnostics(numerical_validator, document)

    assert (diagnostic.code.value, diagnostic.pointer) == ("incompatible_condition", "/conditions")


def test_request_over_the_homologated_profile_is_refused_before_anything_is_allocated(
    numerical_validator: NumericalValidator,
) -> None:
    document = ProblemDocument.load(REJECTED / "estimated_work_too_large.json")

    (diagnostic,) = _diagnostics(numerical_validator, document)

    assert diagnostic.category is DiagnosticCategory.BUDGET_EXCEEDED
    assert "Nada foi alocado" in diagnostic.message
    assert str(MAX_OPERATIONS) in diagnostic.expected
