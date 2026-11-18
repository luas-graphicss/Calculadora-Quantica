from fractions import Fraction

import pytest

from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCategory,
    DiagnosticCode,
    ProblemRejectedError,
)
from quantum_calculator.domain.dimensions import LENGTH, MASS
from quantum_calculator.domain.quantities import Quantity
from quantum_calculator.domain.validated_problem import UserQuantity, ValidatedProblem
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem
from support.documents import ProblemDocument


def _validate(validator: ProblemValidator, document: ProblemDocument) -> ValidatedProblem:
    return validator.validate(decode_problem(document.encode()))


def _diagnostics(validator: ProblemValidator, document: ProblemDocument) -> tuple[Diagnostic, ...]:
    with pytest.raises(ProblemRejectedError) as rejection:
        _validate(validator, document)
    return rejection.value.diagnostics


def _only(validator: ProblemValidator, document: ProblemDocument) -> Diagnostic:
    (diagnostic,) = _diagnostics(validator, document)
    return diagnostic


def test_reference_case_is_bound_to_coherent_si_values(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    problem = _validate(validator, electron_box)

    mass = problem.quantity("mass")
    width = problem.quantity("width")
    assert isinstance(mass.origin, PhysicalConstant)
    assert mass.quantity == Quantity(Fraction("9.1093837139e-31"), MASS)
    assert isinstance(width.origin, UserQuantity)
    assert width.origin.unit.symbol == "nm"
    assert width.quantity == Quantity(Fraction(1, 10**9), LENGTH)
    assert problem.count("level").value == 1
    assert problem.output.unit.symbol == "eV"
    assert problem.output.rounding.significant_digits == 10
    assert [hypothesis.key for hypothesis in problem.hypotheses] == [
        "walls",
        "interior_potential",
        "boundary_wavefunction",
    ]
    assert problem.uncertainty is None


def test_significant_digits_default_to_ten_when_not_requested(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    problem = _validate(validator, electron_box.without("/requested/significant_digits"))

    assert problem.output.rounding.significant_digits == 10


def test_explicit_mass_is_accepted_in_place_of_the_catalog_constant(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    document = electron_box.with_value(
        "/parameters/mass", {"value": "9.1093837139e-28", "unit": "g"}
    )

    mass = _validate(validator, document).quantity("mass")

    assert mass.quantity == Quantity(Fraction("9.1093837139e-31"), MASS)


def test_unknown_card_is_an_unsupported_problem(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    diagnostic = _only(validator, electron_box.with_value("/problem", "quantum.finite_well"))

    assert diagnostic.code is DiagnosticCode.UNKNOWN_PROBLEM
    assert diagnostic.category is DiagnosticCategory.UNSUPPORTED_PROBLEM
    assert "quantum.infinite_square_well.energy_level" in diagnostic.expected


def test_unit_outside_the_registry_is_refused_with_the_accepted_units(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    document = electron_box.with_value("/parameters/width", {"value": 1, "unit": "furlong"})

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.UNKNOWN_UNIT
    assert diagnostic.pointer == "/parameters/width/unit"
    assert "nm" in diagnostic.expected


def test_unknown_constant_lists_the_constants_of_that_dimension(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    document = electron_box.with_value("/parameters/mass", {"constant": "muon_mass"})

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.UNKNOWN_CONSTANT
    assert diagnostic.pointer == "/parameters/mass/constant"
    assert "electron_mass" in diagnostic.expected


def test_constant_of_another_dimension_is_refused(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    document = electron_box.with_value("/parameters/mass", {"constant": "planck_constant"})

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.DIMENSION_MISMATCH
    assert diagnostic.pointer == "/parameters/mass/constant"


def test_quantity_without_unit_is_refused(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    diagnostic = _only(validator, electron_box.with_value("/parameters/width", 1))

    assert diagnostic.code is DiagnosticCode.INVALID_TYPE
    assert diagnostic.pointer == "/parameters/width"


def test_level_with_a_unit_is_refused(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    document = electron_box.with_value("/parameters/level", {"value": 1, "unit": "m"})

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.INVALID_TYPE
    assert diagnostic.pointer == "/parameters/level"


def test_missing_parameters_are_reported_together(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    document = electron_box.without("/parameters/mass").without("/parameters/level")

    diagnostics = _diagnostics(validator, document)

    assert [(item.code, item.pointer) for item in diagnostics] == [
        (DiagnosticCode.MISSING_FIELD, "/parameters/mass"),
        (DiagnosticCode.MISSING_FIELD, "/parameters/level"),
    ]


def test_parameter_the_card_does_not_use_is_refused(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    document = electron_box.with_value("/parameters/depth", {"value": 1, "unit": "eV"})

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.UNEXPECTED_FIELD
    assert diagnostic.pointer == "/parameters/depth"


def test_hypothesis_the_card_does_not_define_is_refused(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    diagnostic = _only(validator, electron_box.with_value("/hypotheses/temperature", "zero"))

    assert diagnostic.code is DiagnosticCode.UNEXPECTED_FIELD
    assert diagnostic.pointer == "/hypotheses/temperature"


def test_zero_width_in_seconds_reports_both_defects(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    document = electron_box.with_value("/parameters/width", {"value": 0, "unit": "s"})

    diagnostics = _diagnostics(validator, document)

    assert [(item.code, item.pointer) for item in diagnostics] == [
        (DiagnosticCode.DIMENSION_MISMATCH, "/parameters/width/unit"),
        (DiagnosticCode.NON_POSITIVE_QUANTITY, "/parameters/width/value"),
    ]


def test_quantity_the_card_does_not_compute_is_an_unsupported_problem(
    validator: ProblemValidator, electron_box: ProblemDocument
) -> None:
    diagnostic = _only(validator, electron_box.with_value("/requested/quantity", "momentum"))

    assert diagnostic.code is DiagnosticCode.UNSUPPORTED_QUANTITY
    assert diagnostic.category is DiagnosticCategory.UNSUPPORTED_PROBLEM


@pytest.mark.parametrize("digits", [0, 35, 2.5, -1])
def test_significant_digits_outside_the_supported_range_are_refused(
    validator: ProblemValidator, electron_box: ProblemDocument, digits: float
) -> None:
    document = electron_box.with_value("/requested/significant_digits", digits)

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.NUMBER_OUT_OF_RANGE
    assert diagnostic.pointer == "/requested/significant_digits"


def test_declared_independent_uncertainties_are_bound(
    validator: ProblemValidator, uncertain_electron_box: ProblemDocument
) -> None:
    problem = _validate(validator, uncertain_electron_box)

    assert problem.uncertainty is not None
    assert problem.uncertainty.covariance == "independent"
    by_parameter = {
        entry.parameter: entry.given.to_si() for entry in problem.uncertainty.standard_uncertainties
    }
    assert by_parameter == {
        "mass": Quantity(Fraction("2.8e-40"), MASS),
        "width": Quantity(Fraction(1, 10**11), LENGTH),
    }


def test_covariance_model_without_homologation_is_an_unsupported_problem(
    validator: ProblemValidator, uncertain_electron_box: ProblemDocument
) -> None:
    document = uncertain_electron_box.with_value("/uncertainty/covariance", "correlated")

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.UNSUPPORTED_COVARIANCE
    assert diagnostic.category is DiagnosticCategory.UNSUPPORTED_PROBLEM
    assert "independent" in diagnostic.expected


def test_uncertainty_must_be_declared_for_every_quantity(
    validator: ProblemValidator, uncertain_electron_box: ProblemDocument
) -> None:
    document = uncertain_electron_box.without("/uncertainty/standard_uncertainties/mass")

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.MISSING_FIELD
    assert diagnostic.pointer == "/uncertainty/standard_uncertainties/mass"


def test_negative_uncertainty_is_refused(
    validator: ProblemValidator, uncertain_electron_box: ProblemDocument
) -> None:
    document = uncertain_electron_box.with_value(
        "/uncertainty/standard_uncertainties/width", {"value": "-0.01", "unit": "nm"}
    )

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.NEGATIVE_UNCERTAINTY
    assert diagnostic.pointer == "/uncertainty/standard_uncertainties/width/value"


def test_uncertainty_in_a_unit_of_another_dimension_is_refused(
    validator: ProblemValidator, uncertain_electron_box: ProblemDocument
) -> None:
    document = uncertain_electron_box.with_value(
        "/uncertainty/standard_uncertainties/width", {"value": "0.01", "unit": "kg"}
    )

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.DIMENSION_MISMATCH
    assert diagnostic.pointer == "/uncertainty/standard_uncertainties/width/unit"


def test_uncertainty_for_a_quantity_the_card_does_not_have_is_refused(
    validator: ProblemValidator, uncertain_electron_box: ProblemDocument
) -> None:
    document = uncertain_electron_box.with_value(
        "/uncertainty/standard_uncertainties/depth", {"value": 1, "unit": "eV"}
    )

    diagnostic = _only(validator, document)

    assert diagnostic.code is DiagnosticCode.UNEXPECTED_FIELD
    assert diagnostic.pointer == "/uncertainty/standard_uncertainties/depth"
