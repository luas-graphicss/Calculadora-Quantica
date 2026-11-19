from quantum_calculator.application.workbench.cancellations import RunCancellations
from quantum_calculator.domain.workbench.ports import Clock, RunRepository
from quantum_calculator.domain.workbench.runs import (
    ACTIVE_STATES,
    RunNotFoundError,
    RunState,
    StateChange,
    StoredRun,
)


class CancelRun:
    def __init__(self, runs: RunRepository, cancellations: RunCancellations, clock: Clock) -> None:
        self._runs = runs
        self._cancellations = cancellations
        self._clock = clock

    def execute(self, identifier: str) -> StoredRun:
        cancelled = self._runs.transition(
            StateChange(identifier, ACTIVE_STATES, RunState.CANCELLED, self._clock.now())
        )
        if cancelled is not None:
            self._cancellations.request(identifier)
            return cancelled
        settled = self._runs.find(identifier)
        if settled is None:
            raise RunNotFoundError(identifier)
        return settled
