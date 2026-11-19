import logging

from quantum_calculator.application.workbench.cancellations import RunCancellations
from quantum_calculator.application.workbench.canonical_documents import canonical_json
from quantum_calculator.application.workbench.failures import (
    INTERNAL_ERROR,
    internal_failure,
    process_failure,
)
from quantum_calculator.application.workbench.sample_tables import detach_tables
from quantum_calculator.application.workbench.summaries import is_failure, summarize
from quantum_calculator.domain.execution import (
    CalculationCancelledError,
    CalculationFailedError,
    CancellationSignal,
)
from quantum_calculator.domain.workbench.artifacts import JSON_MEDIA_TYPE
from quantum_calculator.domain.workbench.documents import Document
from quantum_calculator.domain.workbench.ports import (
    ArtifactStore,
    CalculationDocuments,
    Clock,
    RunRepository,
)
from quantum_calculator.domain.workbench.runs import (
    ArtifactRole,
    RunArtifact,
    RunOutcome,
    RunState,
    StateChange,
    StoredRun,
)

_LOGGER = logging.getLogger(__name__)
_QUEUED = frozenset({RunState.QUEUED})
_RUNNING = frozenset({RunState.RUNNING})
_NOT_RECORDED = RunOutcome(
    artifacts=(), verification_status=None, failure_category=INTERNAL_ERROR, headline=None
)


class ExecuteRun:
    def __init__(
        self,
        documents: CalculationDocuments,
        runs: RunRepository,
        artifacts: ArtifactStore,
        cancellations: RunCancellations,
        clock: Clock,
    ) -> None:
        self._documents = documents
        self._runs = runs
        self._artifacts = artifacts
        self._cancellations = cancellations
        self._clock = clock

    def execute(self, identifier: str) -> None:
        cancellation = self._cancellations.open(identifier)
        try:
            started = self._runs.transition(
                StateChange(identifier, _QUEUED, RunState.RUNNING, self._clock.now())
            )
            if started is not None:
                self._calculate(started, cancellation)
        finally:
            self._cancellations.close(identifier)

    def _calculate(self, run: StoredRun, cancellation: CancellationSignal) -> None:
        try:
            state, outcome = self._attempt(run, cancellation)
            self._conclude(run, state, outcome)
        except Exception:
            self._fail(run)
            raise

    def _fail(self, run: StoredRun) -> None:
        try:
            self._conclude(run, RunState.FAILED, internal_failure())
        except OSError:
            self._runs.transition(
                StateChange(
                    run.identifier, _RUNNING, RunState.FAILED, self._clock.now(), _NOT_RECORDED
                )
            )

    def _attempt(
        self, run: StoredRun, cancellation: CancellationSignal
    ) -> tuple[RunState, Document | None]:
        source = self._artifacts.read(run.require_artifact(ArtifactRole.INPUT))
        try:
            outcome = self._documents.calculate(source, run.wall_seconds, cancellation)
        except CalculationCancelledError:
            return RunState.CANCELLED, None
        except CalculationFailedError as failure:
            return RunState.FAILED, process_failure(failure.exit_code)
        return (RunState.FAILED if is_failure(outcome) else RunState.SUCCEEDED), outcome

    def _conclude(self, run: StoredRun, state: RunState, outcome: Document | None) -> None:
        finished_at = self._clock.now()
        recorded = None if outcome is None else self._record(outcome)
        concluded = self._runs.transition(
            StateChange(run.identifier, _RUNNING, state, finished_at, recorded)
        )
        started_at = run.started_at or finished_at
        _LOGGER.info(
            "run %s of card %s ended as %s after %.3f s (failure category: %s)",
            run.identifier,
            run.card_identifier,
            state.value if concluded is not None else "superseded",
            (finished_at - started_at).total_seconds(),
            None if recorded is None else recorded.failure_category,
        )

    def _record(self, outcome: Document) -> RunOutcome:
        stored, tables = detach_tables(outcome, self._artifacts)
        reference = self._artifacts.publish(canonical_json(stored), JSON_MEDIA_TYPE)
        summary = summarize(outcome)
        return RunOutcome(
            artifacts=(RunArtifact(ArtifactRole.OUTCOME, reference), *tables),
            verification_status=summary.verification_status,
            failure_category=summary.failure_category,
            headline=summary.headline,
        )
