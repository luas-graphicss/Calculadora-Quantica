from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from quantum_calculator.domain.workbench.artifacts import ArtifactReference


class RunState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


ACTIVE_STATES = frozenset({RunState.QUEUED, RunState.RUNNING})


class RunOrigin(StrEnum):
    LOCAL = "local"
    IMPORTED = "imported"


class ArtifactRole(StrEnum):
    INPUT = "input"
    PROBLEM = "problem"
    OUTCOME = "outcome"


@dataclass(frozen=True, slots=True)
class RunArtifact:
    role: str
    reference: ArtifactReference


@dataclass(frozen=True, slots=True)
class RunOutcome:
    artifacts: tuple[RunArtifact, ...]
    verification_status: str | None
    failure_category: str | None
    headline: str | None


@dataclass(frozen=True, slots=True)
class StoredRun:
    identifier: str
    idempotency_key: str
    origin: RunOrigin
    parent_identifier: str | None
    state: RunState
    card_identifier: str
    card_title: str
    wall_seconds: float
    package_version: str
    submitted_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    verification_status: str | None
    failure_category: str | None
    headline: str | None
    artifacts: tuple[RunArtifact, ...]

    def artifact(self, role: str) -> ArtifactReference | None:
        for artifact in self.artifacts:
            if artifact.role == role:
                return artifact.reference
        return None

    def require_artifact(self, role: str) -> ArtifactReference:
        reference = self.artifact(role)
        if reference is None:
            raise LookupError(f"run {self.identifier} has no {role} artifact")
        return reference


@dataclass(frozen=True, slots=True)
class StateChange:
    identifier: str
    expected: frozenset[RunState]
    state: RunState
    at: datetime
    outcome: RunOutcome | None = None


class RunNotFoundError(LookupError):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"run {identifier} is not in the history")
        self.identifier = identifier
