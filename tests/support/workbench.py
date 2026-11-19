import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from quantum_calculator.adapters.storage.file_artifacts import FileArtifactStore
from quantum_calculator.adapters.storage.sqlite_runs import SqliteRunRepository
from quantum_calculator.application.workbench.cancellations import RunCancellations
from quantum_calculator.application.workbench.execute_run import ExecuteRun
from quantum_calculator.application.workbench.submit_run import Submission, SubmitRun
from quantum_calculator.domain.execution import CancellationSignal
from quantum_calculator.domain.workbench.documents import Document

CARD = "quantum.infinite_square_well.discrete_spectrum"
PACKAGE_VERSION = "0.0.0-test"
SOURCE = b'{"schema_version": "1.0", "problem": "' + CARD.encode() + b'"}'
OTHER_SOURCE = SOURCE.replace(b"1.0", b"1.00")
FIRST_INSTANT = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

INTERPRETATION: Document = {
    "document": "numerical_validation",
    "schema_version": "1.2",
    "input": {"sha256": "0" * 64, "text": SOURCE.decode()},
    "problem": {"card": {"identifier": CARD, "title": "Níveis do poço", "version": "1.0.0"}},
    "plan": {"method": "finite_difference.tridiagonal_eigensolver", "nature": "approximate"},
}
REJECTION: Document = {
    "document": "rejection",
    "schema_version": "1.2",
    "category": "non_convergent",
    "diagnostics": [],
}
RECORD: Document = {
    "document": "numerical_run_record",
    "schema_version": "1.2",
    "problem": {"rounding": {"mode": "half_even", "significant_digits": 6}},
    "result": {
        "nature": "approximate",
        "answers": [
            {
                "name": "energy_1",
                "symbol": "E_1",
                "label": "energia do nível 1",
                "value": 0.375,
                "display": "0.375000",
                "unit": "eV",
                "estimate": {"value": 0.0005, "display": "0.00050", "origin": "refinamento"},
            }
        ],
        "tables": [
            {
                "name": "eigenfunctions",
                "title": "Autofunções",
                "rows": 3,
                "columns": [
                    {"name": "position", "symbol": "x", "unit": "m", "values": [0.0, 0.5, 1.0]},
                    {
                        "name": "psi_1",
                        "symbol": "psi_1(x)",
                        "unit": "m^-1/2",
                        "values": [0.0, 1.5, 0.0],
                    },
                ],
            }
        ],
    },
    "verification": {"status": "passed", "checks": []},
}


class SteppingClock:
    def __init__(self) -> None:
        self._ticks = 0

    def now(self) -> datetime:
        self._ticks += 1
        return FIRST_INSTANT + timedelta(seconds=self._ticks)


type Calculation = Callable[[bytes, float, CancellationSignal], Document]


def returning(outcome: Document) -> Calculation:
    def calculate(
        _source: bytes, _wall_seconds: float, _cancellation: CancellationSignal
    ) -> Document:
        return outcome

    return calculate


def raising(error: Exception) -> Calculation:
    def calculate(
        _source: bytes, _wall_seconds: float, _cancellation: CancellationSignal
    ) -> Document:
        raise error

    return calculate


@dataclass
class ScriptedDocuments:
    interpretation: Document = field(default_factory=lambda: INTERPRETATION)
    calculation: Calculation = field(default_factory=lambda: returning(RECORD))
    calculated: list[bytes] = field(default_factory=list)

    def interpret(self, _source: bytes, _wall_seconds: float) -> Document:
        return self.interpretation

    def calculate(
        self, source: bytes, wall_seconds: float, cancellation: CancellationSignal
    ) -> Document:
        self.calculated.append(source)
        return self.calculation(source, wall_seconds, cancellation)


@dataclass
class RecordingQueue:
    enqueued: list[str] = field(default_factory=list)

    def enqueue(self, identifier: str) -> None:
        self.enqueued.append(identifier)


def sequential_identifiers() -> Callable[[], str]:
    issued = iter(range(1, 1_000_000))
    return lambda: f"run-{next(issued)}"


@dataclass
class Bench:
    documents: ScriptedDocuments
    runs: SqliteRunRepository
    artifacts: FileArtifactStore
    queue: RecordingQueue
    cancellations: RunCancellations
    clock: SteppingClock
    new_identifier: Callable[[], str]
    submit: SubmitRun
    execute: ExecuteRun


def build_bench(directory: Path, documents: ScriptedDocuments | None = None) -> Bench:
    scripted = documents or ScriptedDocuments()
    directory.mkdir(parents=True, exist_ok=True)
    runs = SqliteRunRepository(directory / "history.sqlite3")
    artifacts = FileArtifactStore(directory / "artifacts")
    queue = RecordingQueue()
    cancellations = RunCancellations()
    clock = SteppingClock()
    new_identifier = sequential_identifiers()
    return Bench(
        documents=scripted,
        runs=runs,
        artifacts=artifacts,
        queue=queue,
        cancellations=cancellations,
        clock=clock,
        new_identifier=new_identifier,
        submit=SubmitRun(scripted, runs, artifacts, queue, clock, new_identifier, PACKAGE_VERSION),
        execute=ExecuteRun(scripted, runs, artifacts, cancellations, clock),
    )


def closed_form_record(
    source: bytes, numerator: int, denominator: int, decimal: str, unit: str = "eV"
) -> Document:
    return {
        "document": "run_record",
        "schema_version": "1.2",
        "input": {"sha256": hashlib.sha256(source).hexdigest(), "text": source.decode()},
        "problem": {"requested": {"label": "energia do nível"}},
        "plan": {"rounding": {"mode": "half_even", "significant_digits": 10}},
        "constants": {"edition": "CODATA 2022"},
        "units": {"registry_version": "1.0.0"},
        "result": {
            "quantity": "energy",
            "symbol": "E",
            "nature": "exact",
            "value": {
                "decimal": decimal,
                "numerator": str(numerator),
                "denominator": str(denominator),
                "unit": unit,
            },
            "uncertainty": {"status": "not_evaluated"},
        },
        "verification": {"status": "passed", "checks": []},
        "environment": {
            "package": {"name": "quantum-calculator", "version": PACKAGE_VERSION},
            "python": {"implementation": "CPython", "version": "3.12.0"},
            "platform": "Linux-test",
            "dependencies": [{"name": "numpy", "version": "2.5.5"}],
            "linear_algebra": [
                {"consumer": "numpy", "interface": "blas", "name": "openblas", "version": "0.3"}
            ],
        },
    }


def finish(bench: Bench, key: str, source: bytes, outcome: Document) -> str:
    bench.documents.calculation = returning(outcome)
    identifier = bench.submit.execute(Submission(source, key, wall_seconds=30.0)).run.identifier
    bench.execute.execute(identifier)
    return identifier
