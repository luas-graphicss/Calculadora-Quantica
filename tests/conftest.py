from pathlib import Path

import pytest

from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry


@pytest.fixture(scope="session")
def reference_cases() -> Path:
    return Path(__file__).resolve().parents[1] / "reference_cases" / "quantum"


@pytest.fixture(scope="session")
def constants() -> Codata2022Constants:
    return Codata2022Constants()


@pytest.fixture(scope="session")
def units(constants: Codata2022Constants) -> SiUnitRegistry:
    return SiUnitRegistry(constants)
