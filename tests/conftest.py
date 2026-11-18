from pathlib import Path

import pytest

from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.catalog.card_catalog import HOMOLOGATED_CARDS, CardCatalog
from support.documents import ProblemDocument


@pytest.fixture(scope="session")
def reference_cases() -> Path:
    return Path(__file__).resolve().parents[1] / "reference_cases" / "quantum"


@pytest.fixture(scope="session")
def constants() -> Codata2022Constants:
    return Codata2022Constants()


@pytest.fixture(scope="session")
def units(constants: Codata2022Constants) -> SiUnitRegistry:
    return SiUnitRegistry(constants)


@pytest.fixture(scope="session")
def validator(units: SiUnitRegistry, constants: Codata2022Constants) -> ProblemValidator:
    return ProblemValidator(CardCatalog(HOMOLOGATED_CARDS), units, constants)


@pytest.fixture
def electron_box(reference_cases: Path) -> ProblemDocument:
    return ProblemDocument.load(reference_cases / "electron_box_1nm.json")


@pytest.fixture
def uncertain_electron_box(reference_cases: Path) -> ProblemDocument:
    return ProblemDocument.load(reference_cases / "electron_box_1nm_uncertainty.json")
