from fractions import Fraction

from quantum_calculator.domain.constants import ConstantExactness, PhysicalConstant
from quantum_calculator.domain.dimensions import MASS
from quantum_calculator.domain.quantities import Quantity


def _constant(standard_uncertainty: Fraction | None) -> PhysicalConstant:
    return PhysicalConstant(
        identifier="electron_mass",
        symbol="m_e",
        name="massa do elétron",
        value=Quantity(Fraction("9.1093837139e-31"), MASS),
        standard_uncertainty=standard_uncertainty,
        edition="CODATA 2022",
        source="https://physics.nist.gov/cgi-bin/cuu/Value?me",
    )


def test_constant_without_uncertainty_is_exact() -> None:
    assert _constant(None).exactness is ConstantExactness.EXACT


def test_constant_with_uncertainty_is_measured() -> None:
    assert _constant(Fraction("2.8e-40")).exactness is ConstantExactness.MEASURED
