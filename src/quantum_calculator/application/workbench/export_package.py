import hashlib
from dataclasses import dataclass
from datetime import datetime

from quantum_calculator.application.workbench.answers import reported_answers
from quantum_calculator.application.workbench.canonical_documents import canonical_json
from quantum_calculator.application.workbench.csv_tables import (
    CSV_MEDIA_TYPE,
    answers_csv,
    table_csv,
)
from quantum_calculator.application.workbench.package_layout import (
    ANSWERS_PATH,
    INPUT_PATH,
    INPUT_ROLE,
    MANIFEST_PATH,
    OUTCOME_PATH,
    OUTCOME_ROLE,
    PACKAGE_DOCUMENT,
    PACKAGE_SCHEMA_VERSION,
    PROBLEM_PATH,
    PROBLEM_ROLE,
    TABLE_ROLE,
    TABLES_DIRECTORY,
)
from quantum_calculator.application.workbench.read_history import ReadHistory
from quantum_calculator.domain.workbench.artifacts import JSON_MEDIA_TYPE
from quantum_calculator.domain.workbench.documents import Document, object_members, text_member
from quantum_calculator.domain.workbench.packages import PackageFile
from quantum_calculator.domain.workbench.ports import PackageArchive
from quantum_calculator.domain.workbench.runs import ACTIVE_STATES, StoredRun


@dataclass(frozen=True, slots=True)
class PackageGenerator:
    name: str
    version: str


@dataclass(frozen=True, slots=True)
class ExportedPackage:
    file_name: str
    content: bytes


@dataclass(frozen=True, slots=True)
class _ListedFile:
    file: PackageFile
    role: str
    media_type: str


class RunStillActiveError(Exception):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"run {identifier} has not finished and cannot be exported yet")
        self.identifier = identifier


class ExportPackage:
    def __init__(
        self, history: ReadHistory, archive: PackageArchive, generator: PackageGenerator
    ) -> None:
        self._history = history
        self._archive = archive
        self._generator = generator

    def execute(self, identifier: str) -> ExportedPackage:
        details = self._history.details(identifier)
        run = details.run
        if run.state in ACTIVE_STATES:
            raise RunStillActiveError(identifier)
        problem = canonical_json(details.problem)
        listed = [
            _ListedFile(PackageFile(INPUT_PATH, details.source), INPUT_ROLE, JSON_MEDIA_TYPE),
            _ListedFile(PackageFile(PROBLEM_PATH, problem), PROBLEM_ROLE, JSON_MEDIA_TYPE),
            *_outcome_files(self._history.complete_outcome(identifier)),
        ]
        manifest = self._manifest(run, hashlib.sha256(problem).hexdigest(), listed)
        files = [item.file for item in listed]
        files.append(PackageFile(MANIFEST_PATH, canonical_json(manifest)))
        return ExportedPackage(f"qcalc-{run.identifier}.zip", self._archive.pack(files))

    def _manifest(self, run: StoredRun, problem_digest: str, listed: list[_ListedFile]) -> Document:
        return {
            "document": PACKAGE_DOCUMENT,
            "schema_version": PACKAGE_SCHEMA_VERSION,
            "generator": {"name": self._generator.name, "version": self._generator.version},
            "run": {
                "identifier": run.identifier,
                "origin": run.origin.value,
                "state": run.state.value,
                "parent_identifier": run.parent_identifier,
                "card": {"identifier": run.card_identifier, "title": run.card_title},
                "wall_seconds": run.wall_seconds,
                "package_version": run.package_version,
                "submitted_at": run.submitted_at.isoformat(),
                "started_at": _instant(run.started_at),
                "finished_at": _instant(run.finished_at),
                "verification_status": run.verification_status,
                "failure_category": run.failure_category,
                "headline": run.headline,
            },
            "canonical_problem_sha256": problem_digest,
            "files": [
                {
                    "path": item.file.path,
                    "role": item.role,
                    "media_type": item.media_type,
                    "size": len(item.file.content),
                    "sha256": hashlib.sha256(item.file.content).hexdigest(),
                }
                for item in sorted(listed, key=lambda item: item.file.path)
            ],
        }


def _outcome_files(outcome: Document | None) -> list[_ListedFile]:
    if outcome is None:
        return []
    listed = [
        _ListedFile(
            PackageFile(OUTCOME_PATH, canonical_json(outcome)), OUTCOME_ROLE, JSON_MEDIA_TYPE
        )
    ]
    answers = reported_answers(outcome)
    if answers:
        listed.append(
            _ListedFile(PackageFile(ANSWERS_PATH, answers_csv(answers)), TABLE_ROLE, CSV_MEDIA_TYPE)
        )
    for table in object_members(outcome, "result", "tables"):
        path = f"{TABLES_DIRECTORY}/{text_member(table, 'name')}.csv"
        listed.append(_ListedFile(PackageFile(path, table_csv(table)), TABLE_ROLE, CSV_MEDIA_TYPE))
    return listed


def _instant(instant: datetime | None) -> str | None:
    return None if instant is None else instant.isoformat()
