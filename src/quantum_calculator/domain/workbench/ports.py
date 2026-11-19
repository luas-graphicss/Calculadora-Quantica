from collections.abc import Collection, Sequence
from datetime import datetime
from typing import Protocol

from quantum_calculator.domain.execution import CancellationSignal
from quantum_calculator.domain.workbench.artifacts import ArtifactReference
from quantum_calculator.domain.workbench.documents import Document
from quantum_calculator.domain.workbench.packages import PackageFile
from quantum_calculator.domain.workbench.runs import StateChange, StoredRun


class Clock(Protocol):
    def now(self) -> datetime: ...


class RunRepository(Protocol):
    def add(self, run: StoredRun) -> StoredRun: ...

    def find(self, identifier: str) -> StoredRun | None: ...

    def find_by_idempotency_key(self, idempotency_key: str) -> StoredRun | None: ...

    def recent(self) -> tuple[StoredRun, ...]: ...

    def transition(self, change: StateChange) -> StoredRun | None: ...

    def interrupt_active(self, at: datetime) -> int: ...

    def referenced_artifacts(self) -> frozenset[str]: ...


class ArtifactStore(Protocol):
    def publish(self, content: bytes, media_type: str) -> ArtifactReference: ...

    def read(self, reference: ArtifactReference) -> bytes: ...

    def remove_unreferenced(self, referenced: Collection[str]) -> int: ...


class RunQueue(Protocol):
    def enqueue(self, identifier: str) -> None: ...


class CalculationDocuments(Protocol):
    def interpret(self, source: bytes, wall_seconds: float) -> Document: ...

    def calculate(
        self, source: bytes, wall_seconds: float, cancellation: CancellationSignal
    ) -> Document: ...


class PackageArchive(Protocol):
    def pack(self, files: Sequence[PackageFile]) -> bytes: ...

    def unpack(self, content: bytes) -> tuple[PackageFile, ...]: ...
