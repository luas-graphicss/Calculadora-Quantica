from dataclasses import dataclass

from quantum_calculator.application.workbench.canonical_documents import parse_document
from quantum_calculator.application.workbench.sample_tables import (
    attach_table,
    attach_tables,
    find_table,
)
from quantum_calculator.domain.workbench.documents import Document
from quantum_calculator.domain.workbench.ports import ArtifactStore, RunRepository
from quantum_calculator.domain.workbench.runs import ArtifactRole, RunNotFoundError, StoredRun


@dataclass(frozen=True, slots=True)
class RunDetails:
    run: StoredRun
    source: bytes
    problem: Document
    outcome: Document | None

    @property
    def input_text(self) -> str:
        return self.source.decode("utf-8")


class TableNotFoundError(LookupError):
    def __init__(self, run_identifier: str, name: str) -> None:
        super().__init__(f"run {run_identifier} has no table named {name}")
        self.run_identifier = run_identifier
        self.name = name


class ReadHistory:
    def __init__(self, runs: RunRepository, artifacts: ArtifactStore) -> None:
        self._runs = runs
        self._artifacts = artifacts

    def recent(self) -> tuple[StoredRun, ...]:
        return self._runs.recent()

    def run(self, identifier: str) -> StoredRun:
        run = self._runs.find(identifier)
        if run is None:
            raise RunNotFoundError(identifier)
        return run

    def details(self, identifier: str) -> RunDetails:
        run = self.run(identifier)
        source = self._artifacts.read(run.require_artifact(ArtifactRole.INPUT))
        problem = self._artifacts.read(run.require_artifact(ArtifactRole.PROBLEM))
        return RunDetails(
            run=run,
            source=source,
            problem=parse_document(problem),
            outcome=self._stored_outcome(run),
        )

    def complete_outcome(self, identifier: str) -> Document | None:
        outcome = self._stored_outcome(self.run(identifier))
        return None if outcome is None else attach_tables(outcome, self._artifacts)

    def table(self, identifier: str, name: str) -> Document:
        outcome = self._stored_outcome(self.run(identifier))
        table = None if outcome is None else find_table(outcome, name)
        if table is None:
            raise TableNotFoundError(identifier, name)
        return attach_table(table, self._artifacts)

    def _stored_outcome(self, run: StoredRun) -> Document | None:
        reference = run.artifact(ArtifactRole.OUTCOME)
        return None if reference is None else parse_document(self._artifacts.read(reference))
