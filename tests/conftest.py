from pathlib import Path

import pytest

from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.catalog.card_catalog import HOMOLOGATED_CARDS, CardCatalog
from quantum_calculator.catalog.statement_catalog import (
    HOMOLOGATED_STATEMENT_CARDS,
    StatementCatalog,
)
from quantum_calculator.composition import Calculator, build_calculator
from quantum_calculator.interfaces.cli.main import main
from quantum_calculator.solvers.symbolic.infinite_square_well import InfiniteSquareWellSolver
from quantum_calculator.verification.infinite_square_well import InfiniteSquareWellVerifier
from support.cli import CliResult, CliRunner
from support.documents import ProblemDocument


@pytest.fixture(scope="session")
def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def reference_cases(repository_root: Path) -> Path:
    return repository_root / "reference_cases" / "quantum"


@pytest.fixture(scope="session")
def symbolic_cases(repository_root: Path) -> Path:
    return repository_root / "reference_cases" / "symbolic"


@pytest.fixture(scope="session")
def constants() -> Codata2022Constants:
    return Codata2022Constants()


@pytest.fixture(scope="session")
def units(constants: Codata2022Constants) -> SiUnitRegistry:
    return SiUnitRegistry(constants)


@pytest.fixture(scope="session")
def validator(units: SiUnitRegistry, constants: Codata2022Constants) -> ProblemValidator:
    return ProblemValidator(CardCatalog(HOMOLOGATED_CARDS), units, constants)


@pytest.fixture(scope="session")
def statement_validator(units: SiUnitRegistry) -> StatementValidator:
    return StatementValidator(StatementCatalog(HOMOLOGATED_STATEMENT_CARDS), units)


@pytest.fixture(scope="session")
def solver(constants: Codata2022Constants) -> InfiniteSquareWellSolver:
    return InfiniteSquareWellSolver(constants)


@pytest.fixture(scope="session")
def verifier(constants: Codata2022Constants) -> InfiniteSquareWellVerifier:
    return InfiniteSquareWellVerifier(constants)


@pytest.fixture(scope="session")
def calculator() -> Calculator:
    return build_calculator()


@pytest.fixture
def electron_box(reference_cases: Path) -> ProblemDocument:
    return ProblemDocument.load(reference_cases / "electron_box_1nm.json")


@pytest.fixture
def uncertain_electron_box(reference_cases: Path) -> ProblemDocument:
    return ProblemDocument.load(reference_cases / "electron_box_1nm_uncertainty.json")


@pytest.fixture
def run_cli(capsys: pytest.CaptureFixture[str]) -> CliRunner:
    def run(*arguments: str | Path) -> CliResult:
        exit_code = main([str(argument) for argument in arguments])
        captured = capsys.readouterr()
        return CliResult(exit_code=exit_code, stdout=captured.out, stderr=captured.err)

    return run
