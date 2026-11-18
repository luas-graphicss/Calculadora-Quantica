from fractions import Fraction

import pytest

from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.statements.unit_expressions import (
    UnitExpressionError,
    dimension_of_unit,
    measure_of_unit,
)
from quantum_calculator.domain.dimensions import ACTION, ENERGY, LENGTH, MASS, TIME, Dimension


@pytest.mark.parametrize(
    ("expression", "dimension"),
    [
        ("1", Dimension()),
        ("s", TIME),
        ("1/s", Dimension(time=-1)),
        ("m/s", LENGTH / TIME),
        ("m/s^2", LENGTH / TIME**2),
        ("m s^-1", LENGTH / TIME),
        ("kg m^2/s^2", ENERGY),
        ("J s", ACTION),
        ("eV/nm", ENERGY / LENGTH),
        ("kg/m s", MASS / (LENGTH * TIME)),
    ],
)
def test_compound_unit_gives_the_product_of_its_factor_dimensions(
    units: SiUnitRegistry, expression: str, dimension: Dimension
) -> None:
    assert dimension_of_unit(expression, units) == dimension


@pytest.mark.algebraic
@pytest.mark.parametrize(
    ("expression", "si_factor"),
    [
        ("1", Fraction(1)),
        ("1/s", Fraction(1)),
        ("nm", Fraction(1, 10**9)),
        ("1/fs", Fraction(10**15)),
        ("nm^2", Fraction(1, 10**18)),
        ("g/nm ps^2", Fraction(10**30)),
        ("eV/nm", Fraction("1.602176634e-19") * 10**9),
    ],
)
def test_compound_unit_carries_the_exact_factor_to_coherent_si(
    units: SiUnitRegistry, expression: str, si_factor: Fraction
) -> None:
    assert measure_of_unit(expression, units).si_factor == si_factor


@pytest.mark.parametrize(
    ("expression", "reason"),
    [
        ("furlong", "não consta do registro"),
        ("m/s/s", "mais de uma barra"),
        ("/s", "falta uma unidade"),
        ("m/", "falta uma unidade"),
        ("", "falta uma unidade"),
        ("m^x", "não é uma unidade com expoente inteiro"),
        ("m^12", "não é uma unidade com expoente inteiro"),
    ],
)
def test_malformed_unit_expression_is_refused_with_its_reason(
    units: SiUnitRegistry, expression: str, reason: str
) -> None:
    with pytest.raises(UnitExpressionError, match=reason):
        dimension_of_unit(expression, units)
