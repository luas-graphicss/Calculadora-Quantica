from dataclasses import dataclass

from quantum_calculator.application.workbench.cancellations import RunCancellations
from quantum_calculator.domain.workbench.ports import ArtifactStore, Clock, RunRepository


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    interrupted_runs: int
    removed_orphans: int


class RecoverHistory:
    def __init__(self, runs: RunRepository, artifacts: ArtifactStore, clock: Clock) -> None:
        self._runs = runs
        self._artifacts = artifacts
        self._clock = clock

    def execute(self) -> RecoveryReport:
        interrupted = self._runs.interrupt_active(self._clock.now())
        removed = self._artifacts.remove_unreferenced(self._runs.referenced_artifacts())
        return RecoveryReport(interrupted_runs=interrupted, removed_orphans=removed)


class InterruptActiveRuns:
    def __init__(self, runs: RunRepository, cancellations: RunCancellations, clock: Clock) -> None:
        self._runs = runs
        self._cancellations = cancellations
        self._clock = clock

    def execute(self) -> int:
        interrupted = self._runs.interrupt_active(self._clock.now())
        self._cancellations.request_all()
        return interrupted
