import hashlib
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from datetime import datetime

from quantum_calculator.application.workbench.canonical_documents import (
    MalformedDocumentError,
    canonical_json,
    parse_document,
)
from quantum_calculator.application.workbench.package_layout import (
    INPUT_ROLE,
    MANIFEST_PATH,
    OUTCOME_ROLE,
    PACKAGE_DOCUMENT,
    PACKAGE_SCHEMA_VERSION,
    PROBLEM_ROLE,
)
from quantum_calculator.application.workbench.sample_tables import (
    MalformedTableError,
    detach_tables,
)
from quantum_calculator.application.workbench.summaries import (
    CALCULATION_FAILURE,
    document_kind,
    is_failure,
    summarize,
)
from quantum_calculator.domain.workbench.artifacts import JSON_MEDIA_TYPE
from quantum_calculator.domain.workbench.documents import (
    Document,
    member,
    object_member,
    object_members,
    text_member,
)
from quantum_calculator.domain.workbench.packages import PackageRejectedError
from quantum_calculator.domain.workbench.ports import ArtifactStore, PackageArchive, RunRepository
from quantum_calculator.domain.workbench.runs import (
    ACTIVE_STATES,
    ArtifactRole,
    RunArtifact,
    RunOrigin,
    RunState,
    StoredRun,
)

_NOTHING_DONE = "Nada foi importado nem calculado."
_RECORD_IS_A_FAILURE = {RunState.SUCCEEDED: False, RunState.FAILED: True}


@dataclass(frozen=True, slots=True)
class ImportReceipt:
    run: StoredRun
    created: bool


@dataclass(frozen=True, slots=True)
class _VerifiedPackage:
    manifest: Document
    source: bytes
    problem: bytes
    outcome: bytes | None


class ImportPackage:
    def __init__(
        self,
        runs: RunRepository,
        artifacts: ArtifactStore,
        archive: PackageArchive,
        new_identifier: Callable[[], str],
        readable_record_versions: Collection[str],
    ) -> None:
        self._runs = runs
        self._artifacts = artifacts
        self._archive = archive
        self._new_identifier = new_identifier
        self._readable_record_versions = readable_record_versions

    def execute(self, content: bytes) -> ImportReceipt:
        idempotency_key = f"import:{_digest(content)}"
        known = self._runs.find_by_idempotency_key(idempotency_key)
        if known is not None:
            return ImportReceipt(known, created=False)
        files = {file.path: file.content for file in self._archive.unpack(content)}
        imported = self._imported_run(_verified(files), idempotency_key)
        stored = self._runs.add(imported)
        return ImportReceipt(stored, created=stored.identifier == imported.identifier)

    def _imported_run(self, package: _VerifiedPackage, idempotency_key: str) -> StoredRun:
        described = _required_object(package.manifest, "run")
        state = _terminal_state(described)
        problem = _parsed(package.problem, "problem.json")
        _parsed(package.source, "input.json")
        outcome = None if package.outcome is None else _parsed(package.outcome, "outcome.json")
        self._require_consistent(state, outcome, package)
        summary = None if outcome is None else summarize(outcome)
        artifacts = [
            RunArtifact(
                ArtifactRole.INPUT, self._artifacts.publish(package.source, JSON_MEDIA_TYPE)
            ),
            RunArtifact(
                ArtifactRole.PROBLEM,
                self._artifacts.publish(canonical_json(problem), JSON_MEDIA_TYPE),
            ),
            *([] if outcome is None else self._stored_outcome(outcome)),
        ]
        return StoredRun(
            identifier=self._new_identifier(),
            idempotency_key=idempotency_key,
            origin=RunOrigin.IMPORTED,
            parent_identifier=None,
            state=state,
            card_identifier=_required_text(problem, "problem", "card", "identifier"),
            card_title=_required_text(problem, "problem", "card", "title"),
            wall_seconds=_wall_seconds(described),
            package_version=_required_text(described, "package_version"),
            submitted_at=_instant(described, "submitted_at"),
            started_at=_optional_instant(described, "started_at"),
            finished_at=_optional_instant(described, "finished_at"),
            verification_status=None if summary is None else summary.verification_status,
            failure_category=None if summary is None else summary.failure_category,
            headline=None if summary is None else summary.headline,
            artifacts=tuple(artifacts),
        )

    def _require_consistent(
        self, state: RunState, outcome: Document | None, package: _VerifiedPackage
    ) -> None:
        if state not in _RECORD_IS_A_FAILURE:
            if outcome is not None:
                raise _rejected(f"uma execução {state.value} não tem registro de resultado")
            return
        if outcome is None:
            raise _rejected(f"falta o registro da execução {state.value}")
        if is_failure(outcome) != _RECORD_IS_A_FAILURE[state]:
            raise _rejected(f"o registro não corresponde a uma execução {state.value}")
        version = text_member(outcome, "schema_version")
        if document_kind(outcome) != CALCULATION_FAILURE and (
            version not in self._readable_record_versions
        ):
            readable = ", ".join(sorted(self._readable_record_versions))
            raise _rejected(
                f"o registro usa a versão {version} do esquema de saída e esta instalação lê "
                f"{readable}"
            )
        recorded_input = text_member(outcome, "input", "sha256")
        if recorded_input is not None and recorded_input != _digest(package.source):
            raise _rejected("o registro foi calculado a partir de outra entrada")

    def _stored_outcome(self, outcome: Document) -> list[RunArtifact]:
        try:
            stored, tables = detach_tables(outcome, self._artifacts)
        except MalformedTableError as error:
            raise _rejected("uma tabela do registro não é uma lista de números finitos") from error
        reference = self._artifacts.publish(canonical_json(stored), JSON_MEDIA_TYPE)
        return [RunArtifact(ArtifactRole.OUTCOME, reference), *tables]


def _verified(files: Mapping[str, bytes]) -> _VerifiedPackage:
    encoded_manifest = files.get(MANIFEST_PATH)
    if encoded_manifest is None:
        raise _rejected("falta o manifesto manifest.json")
    manifest = _parsed(encoded_manifest, MANIFEST_PATH)
    if document_kind(manifest) != PACKAGE_DOCUMENT:
        raise _rejected("o manifesto não descreve um pacote de reprodução")
    version = text_member(manifest, "schema_version")
    if version != PACKAGE_SCHEMA_VERSION:
        raise _rejected(
            f"o pacote usa a versão {version} do formato e esta instalação lê "
            f"{PACKAGE_SCHEMA_VERSION}"
        )
    by_role = _files_by_role(manifest, files)
    problem = _single(by_role, PROBLEM_ROLE)
    if text_member(manifest, "canonical_problem_sha256") != _digest(problem):
        raise _rejected("o problema canônico não confere com o hash declarado no manifesto")
    return _VerifiedPackage(
        manifest=manifest,
        source=_single(by_role, INPUT_ROLE),
        problem=problem,
        outcome=by_role[OUTCOME_ROLE][0] if by_role.get(OUTCOME_ROLE) else None,
    )


def _files_by_role(manifest: Document, files: Mapping[str, bytes]) -> dict[str, list[bytes]]:
    listed = object_members(manifest, "files")
    paths = [text_member(entry, "path") for entry in listed]
    unlisted = sorted(files.keys() - {MANIFEST_PATH} - set(paths))
    if unlisted:
        raise _rejected(f"o arquivo {unlisted[0]} não consta do manifesto")
    by_role: dict[str, list[bytes]] = {}
    for entry, path in zip(listed, paths, strict=True):
        content = None if path is None else files.get(path)
        if path is None or content is None:
            raise _rejected(f"falta o arquivo {path} listado no manifesto")
        if member(entry, "size") != len(content) or text_member(entry, "sha256") != _digest(
            content
        ):
            raise _rejected(f"o arquivo {path} não confere com o hash declarado no manifesto")
        by_role.setdefault(text_member(entry, "role") or "", []).append(content)
    if len(by_role.get(OUTCOME_ROLE, [])) > 1:
        raise _rejected("o manifesto lista mais de um registro de resultado")
    return by_role


def _single(by_role: Mapping[str, list[bytes]], role: str) -> bytes:
    contents = by_role.get(role, [])
    if len(contents) != 1:
        raise _rejected(f"o manifesto deve listar exatamente um arquivo com o papel {role}")
    return contents[0]


def _parsed(content: bytes, path: str) -> Document:
    try:
        return parse_document(content)
    except MalformedDocumentError as error:
        raise _rejected(f"o arquivo {path} não é um documento JSON válido") from error


def _terminal_state(described: Document) -> RunState:
    declared = text_member(described, "state")
    try:
        state = RunState(declared or "")
    except ValueError as error:
        raise _rejected(f"o manifesto declara o estado desconhecido {declared}") from error
    if state in ACTIVE_STATES:
        raise _rejected(f"o manifesto declara uma execução ainda {state.value}")
    return state


def _wall_seconds(described: Document) -> float:
    seconds = member(described, "wall_seconds")
    if isinstance(seconds, bool) or not isinstance(seconds, int | float) or seconds <= 0:
        raise _rejected("o manifesto não traz o limite de tempo da execução")
    return float(seconds)


def _instant(described: Document, field: str) -> datetime:
    instant = _optional_instant(described, field)
    if instant is None:
        raise _rejected(f"o manifesto não traz o instante {field}")
    return instant


def _optional_instant(described: Document, field: str) -> datetime | None:
    recorded = text_member(described, field)
    if recorded is None:
        return None
    try:
        instant = datetime.fromisoformat(recorded)
    except ValueError as error:
        raise _rejected(f"o instante {field} do manifesto não está em ISO 8601") from error
    if instant.tzinfo is None:
        raise _rejected(f"o instante {field} do manifesto não traz o fuso horário")
    return instant


def _required_object(document: Document, *path: str) -> Document:
    found = object_member(document, *path)
    if found is None:
        raise _rejected(f"falta o campo {'.'.join(path)}")
    return found


def _required_text(document: Document, *path: str) -> str:
    found = text_member(document, *path)
    if not found:
        raise _rejected(f"falta o campo {'.'.join(path)}")
    return found


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _rejected(reason: str) -> PackageRejectedError:
    return PackageRejectedError(f"Pacote recusado: {reason}. {_NOTHING_DONE}")
