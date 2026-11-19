import sqlite3
from collections import defaultdict
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path

from quantum_calculator.adapters.storage.migrations import migrate
from quantum_calculator.domain.workbench.artifacts import ArtifactReference
from quantum_calculator.domain.workbench.runs import (
    ACTIVE_STATES,
    RunArtifact,
    RunOrigin,
    RunState,
    StateChange,
    StoredRun,
)

_BUSY_TIMEOUT_SECONDS = 30.0
_RUN_COLUMNS = (
    "identifier, idempotency_key, origin, parent_identifier, state, card_identifier, "
    "card_title, wall_seconds, package_version, submitted_at, started_at, finished_at, "
    "verification_status, failure_category, headline"
)
_SELECT_RUN = f"SELECT {_RUN_COLUMNS} FROM runs"  # noqa: S608 - fixed column list, no input
_SELECT_BY_IDENTIFIER = f"{_SELECT_RUN} WHERE identifier = ?"
_SELECT_BY_IDEMPOTENCY_KEY = f"{_SELECT_RUN} WHERE idempotency_key = ?"
_SELECT_ARTIFACTS = (
    "SELECT run_artifacts.run_identifier, run_artifacts.role, artifacts.sha256, "
    "artifacts.media_type, artifacts.size "
    "FROM run_artifacts JOIN artifacts ON artifacts.sha256 = run_artifacts.sha256"
)

type _RunRow = tuple[
    str,
    str,
    str,
    str | None,
    str,
    str,
    str,
    float,
    str,
    str,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
]


class SqliteRunRepository:
    def __init__(self, database: Path) -> None:
        self._database = database
        with closing(self._connect()) as connection:
            connection.execute("PRAGMA journal_mode = WAL")
        with self._transaction(writing=True) as connection:
            migrate(connection)

    def add(self, run: StoredRun) -> StoredRun:
        with self._transaction(writing=True) as connection:
            known = _find(connection, _SELECT_BY_IDEMPOTENCY_KEY, run.idempotency_key)
            if known is not None:
                return known
            connection.execute(
                f"INSERT INTO runs ({_RUN_COLUMNS}) "  # noqa: S608 - fixed column list, no input
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run.identifier,
                    run.idempotency_key,
                    run.origin.value,
                    run.parent_identifier,
                    run.state.value,
                    run.card_identifier,
                    run.card_title,
                    run.wall_seconds,
                    run.package_version,
                    run.submitted_at.isoformat(),
                    _stored_instant(run.started_at),
                    _stored_instant(run.finished_at),
                    run.verification_status,
                    run.failure_category,
                    run.headline,
                ),
            )
            _link(connection, run.identifier, run.artifacts)
            return _require(connection, run.identifier)

    def find(self, identifier: str) -> StoredRun | None:
        with self._transaction(writing=False) as connection:
            return _find(connection, _SELECT_BY_IDENTIFIER, identifier)

    def find_by_idempotency_key(self, idempotency_key: str) -> StoredRun | None:
        with self._transaction(writing=False) as connection:
            return _find(connection, _SELECT_BY_IDEMPOTENCY_KEY, idempotency_key)

    def recent(self) -> tuple[StoredRun, ...]:
        with self._transaction(writing=False) as connection:
            rows: list[_RunRow] = connection.execute(
                f"{_SELECT_RUN} ORDER BY submitted_at DESC, rowid DESC"
            ).fetchall()
            artifacts = defaultdict(list)
            for run_identifier, role, sha256, media_type, size in connection.execute(
                f"{_SELECT_ARTIFACTS} ORDER BY run_artifacts.role"
            ):
                artifacts[run_identifier].append(
                    RunArtifact(role, ArtifactReference(sha256, media_type, size))
                )
        return tuple(_stored_run(row, tuple(artifacts[row[0]])) for row in rows)

    def transition(self, change: StateChange) -> StoredRun | None:
        with self._transaction(writing=True) as connection:
            row = connection.execute(
                "SELECT state FROM runs WHERE identifier = ?", (change.identifier,)
            ).fetchone()
            if row is None or RunState(row[0]) not in change.expected:
                return None
            outcome = change.outcome
            instant = change.at.isoformat()
            connection.execute(
                "UPDATE runs SET state = ?, started_at = COALESCE(?, started_at), "
                "finished_at = ?, verification_status = ?, failure_category = ?, headline = ? "
                "WHERE identifier = ?",
                (
                    change.state.value,
                    instant if change.state is RunState.RUNNING else None,
                    None if change.state in ACTIVE_STATES else instant,
                    None if outcome is None else outcome.verification_status,
                    None if outcome is None else outcome.failure_category,
                    None if outcome is None else outcome.headline,
                    change.identifier,
                ),
            )
            if outcome is not None:
                _link(connection, change.identifier, outcome.artifacts)
            return _require(connection, change.identifier)

    def interrupt_active(self, at: datetime) -> int:
        with self._transaction(writing=True) as connection:
            cursor = connection.execute(
                "UPDATE runs SET state = ?, finished_at = ? WHERE state IN (?, ?)",
                (
                    RunState.INTERRUPTED.value,
                    at.isoformat(),
                    RunState.QUEUED.value,
                    RunState.RUNNING.value,
                ),
            )
            return cursor.rowcount

    def referenced_artifacts(self) -> frozenset[str]:
        with self._transaction(writing=False) as connection:
            return frozenset(
                sha256 for (sha256,) in connection.execute("SELECT sha256 FROM run_artifacts")
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database, timeout=_BUSY_TIMEOUT_SECONDS, isolation_level=None
        )
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _transaction(self, *, writing: bool) -> Iterator[sqlite3.Connection]:
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE" if writing else "BEGIN")
            try:
                yield connection
            except BaseException:
                connection.execute("ROLLBACK")
                raise
            connection.execute("COMMIT")


def _find(connection: sqlite3.Connection, query: str, key: str) -> StoredRun | None:
    row: _RunRow | None = connection.execute(query, (key,)).fetchone()
    if row is None:
        return None
    artifacts = tuple(
        RunArtifact(role, ArtifactReference(sha256, media_type, size))
        for _, role, sha256, media_type, size in connection.execute(
            f"{_SELECT_ARTIFACTS} WHERE run_artifacts.run_identifier = ? "
            "ORDER BY run_artifacts.role",
            (row[0],),
        )
    )
    return _stored_run(row, artifacts)


def _require(connection: sqlite3.Connection, identifier: str) -> StoredRun:
    stored = _find(connection, _SELECT_BY_IDENTIFIER, identifier)
    if stored is None:
        raise LookupError(f"run {identifier} disappeared inside its own transaction")
    return stored


def _link(
    connection: sqlite3.Connection, run_identifier: str, artifacts: tuple[RunArtifact, ...]
) -> None:
    for artifact in artifacts:
        reference = artifact.reference
        connection.execute(
            "INSERT OR IGNORE INTO artifacts (sha256, media_type, size) VALUES (?, ?, ?)",
            (reference.sha256, reference.media_type, reference.size),
        )
        connection.execute(
            "INSERT INTO run_artifacts (run_identifier, role, sha256) VALUES (?, ?, ?)",
            (run_identifier, str(artifact.role), reference.sha256),
        )


def _stored_run(row: _RunRow, artifacts: tuple[RunArtifact, ...]) -> StoredRun:
    return StoredRun(
        identifier=row[0],
        idempotency_key=row[1],
        origin=RunOrigin(row[2]),
        parent_identifier=row[3],
        state=RunState(row[4]),
        card_identifier=row[5],
        card_title=row[6],
        wall_seconds=row[7],
        package_version=row[8],
        submitted_at=datetime.fromisoformat(row[9]),
        started_at=_instant(row[10]),
        finished_at=_instant(row[11]),
        verification_status=row[12],
        failure_category=row[13],
        headline=row[14],
        artifacts=artifacts,
    )


def _stored_instant(instant: datetime | None) -> str | None:
    return None if instant is None else instant.isoformat()


def _instant(stored: str | None) -> datetime | None:
    return None if stored is None else datetime.fromisoformat(stored)
