import hashlib
from collections.abc import Callable
from dataclasses import dataclass

from quantum_calculator.application.workbench.canonical_documents import (
    canonical_json,
    canonical_problem,
)
from quantum_calculator.application.workbench.summaries import REJECTION, document_kind
from quantum_calculator.domain.workbench.artifacts import JSON_MEDIA_TYPE
from quantum_calculator.domain.workbench.documents import Document, text_member
from quantum_calculator.domain.workbench.ports import (
    ArtifactStore,
    CalculationDocuments,
    Clock,
    RunQueue,
    RunRepository,
)
from quantum_calculator.domain.workbench.runs import (
    ArtifactRole,
    RunArtifact,
    RunNotFoundError,
    RunOrigin,
    RunState,
    StoredRun,
)


@dataclass(frozen=True, slots=True)
class Submission:
    source: bytes
    idempotency_key: str
    wall_seconds: float
    parent_identifier: str | None = None


@dataclass(frozen=True, slots=True)
class SubmissionReceipt:
    run: StoredRun
    created: bool


class SubmissionRejectedError(Exception):
    def __init__(self, rejection: Document) -> None:
        super().__init__("the submitted problem was rejected before any calculation")
        self.rejection = rejection


class IdempotencyConflictError(Exception):
    def __init__(self, run_identifier: str) -> None:
        super().__init__(
            f"the idempotency key already belongs to run {run_identifier}, with another input"
        )
        self.run_identifier = run_identifier


class SubmitRun:
    def __init__(
        self,
        documents: CalculationDocuments,
        runs: RunRepository,
        artifacts: ArtifactStore,
        queue: RunQueue,
        clock: Clock,
        new_identifier: Callable[[], str],
        package_version: str,
    ) -> None:
        self._documents = documents
        self._runs = runs
        self._artifacts = artifacts
        self._queue = queue
        self._clock = clock
        self._new_identifier = new_identifier
        self._package_version = package_version

    def execute(self, submission: Submission) -> SubmissionReceipt:
        known = self._runs.find_by_idempotency_key(submission.idempotency_key)
        if known is not None:
            return _replayed(known, submission)
        parent = submission.parent_identifier
        if parent is not None and self._runs.find(parent) is None:
            raise RunNotFoundError(parent)
        interpretation = self._documents.interpret(submission.source, submission.wall_seconds)
        if document_kind(interpretation) == REJECTION:
            raise SubmissionRejectedError(interpretation)
        queued = self._queued_run(submission, interpretation)
        stored = self._runs.add(queued)
        if stored.identifier != queued.identifier:
            return _replayed(stored, submission)
        self._queue.enqueue(stored.identifier)
        return SubmissionReceipt(stored, created=True)

    def _queued_run(self, submission: Submission, interpretation: Document) -> StoredRun:
        problem = canonical_json(canonical_problem(interpretation))
        return StoredRun(
            identifier=self._new_identifier(),
            idempotency_key=submission.idempotency_key,
            origin=RunOrigin.LOCAL,
            parent_identifier=submission.parent_identifier,
            state=RunState.QUEUED,
            card_identifier=text_member(interpretation, "problem", "card", "identifier") or "",
            card_title=text_member(interpretation, "problem", "card", "title") or "",
            wall_seconds=submission.wall_seconds,
            package_version=self._package_version,
            submitted_at=self._clock.now(),
            started_at=None,
            finished_at=None,
            verification_status=None,
            failure_category=None,
            headline=None,
            artifacts=(
                RunArtifact(
                    ArtifactRole.INPUT, self._artifacts.publish(submission.source, JSON_MEDIA_TYPE)
                ),
                RunArtifact(
                    ArtifactRole.PROBLEM, self._artifacts.publish(problem, JSON_MEDIA_TYPE)
                ),
            ),
        )


def _replayed(known: StoredRun, submission: Submission) -> SubmissionReceipt:
    submitted_digest = hashlib.sha256(submission.source).hexdigest()
    if known.require_artifact(ArtifactRole.INPUT).sha256 != submitted_digest:
        raise IdempotencyConflictError(known.identifier)
    return SubmissionReceipt(known, created=False)
