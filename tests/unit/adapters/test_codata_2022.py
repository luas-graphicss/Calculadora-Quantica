import json
from fractions import Fraction
from pathlib import Path

import pytest

from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.domain.constants import ELECTRON_MASS, ConstantExactness
from quantum_calculator.domain.dimensions import MASS

ORACLE_CONSTANTS = ("planck_constant", "electron_volt", "electron_mass")


@pytest.mark.algebraic
@pytest.mark.parametrize("identifier", ORACLE_CONSTANTS)
def test_constant_matches_the_digits_transcribed_in_the_oracle(
    constants: Codata2022Constants, reference_cases: Path, identifier: str
) -> None:
    oracle = json.loads((reference_cases / "electron_box_1nm.expected.json").read_text("utf-8"))
    expected = oracle["constants"]["values"][identifier]
    uncertainty = expected["standard_uncertainty"]

    constant = constants.find(identifier)

    assert constant is not None
    assert constant.edition == oracle["constants"]["edition"]
    assert constant.value.magnitude == Fraction(expected["value"])
    assert constant.standard_uncertainty == (None if uncertainty is None else Fraction(uncertainty))
    assert constant.source == expected["source"]


def test_only_measured_constants_carry_an_uncertainty(constants: Codata2022Constants) -> None:
    electron_mass = constants.find(ELECTRON_MASS)

    assert electron_mass is not None
    assert electron_mass.exactness is ConstantExactness.MEASURED


def test_constants_are_listed_by_dimension(constants: Codata2022Constants) -> None:
    assert constants.identifiers_for(MASS) == (ELECTRON_MASS,)


def test_unknown_constant_is_not_resolved(constants: Codata2022Constants) -> None:
    assert constants.find("fine_structure_constant") is None
