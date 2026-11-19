import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from quantum_calculator.adapters.storage.migrations import SCHEMA_VERSION, NewerHistoryError
from quantum_calculator.adapters.storage.sqlite_runs import SqliteRunRepository
from quantum_calculator.domain.workbench.artifacts import ArtifactReference
from quantum_calculator.domain.workbench.runs import (
    ACTIVE_STATES,
    ArtifactRole,
    RunArtifact,
    RunOrigin,
    RunOutcome,
    RunState,
    StateChange,
    StoredRun,
)

_SUBMITTED = datetime(2026, 5, 6, 7, 8, 9, 123456, tzinfo=UTC)
_INPUT = RunArtifact(ArtifactRole.INPUT, ArtifactReference("a" * 64, "application/json", 10))
_PROBLEM = RunArtifact(ArtifactRole.PROBLEM, ArtifactReference("b" * 64, "application/json", 20))
_OUTCOME = RunArtifact(ArtifactRole.OUTCOME, ArtifactReference("c" * 64, "application/json", 30))
_QUEUED = StoredRun(
    identifier="run-1",
    idempotency_key="key-1",
    origin=RunOrigin.LOCAL,
    parent_identifier=None,
    state=RunState.QUEUED,
    card_identifier="quantum.infinite_square_well.energy_level",
    card_title="Nível de energia",
    wall_seconds=30.0,
    package_version="0.4.0",
    submitted_at=_SUBMITTED,
    started_at=None,
    finished_at=None,
    verification_status=None,
    failure_category=None,
    headline=None,
    artifacts=(_INPUT, _PROBLEM),
)
_PASSED = RunOutcome((_OUTCOME,), "passed", None, "E = 0.3760301621 eV")


@pytest.fixture
def database(tmp_path: Path) -> Path:
    return tmp_path / "history.sqlite3"


@pytest.fixture
def runs(database: Path) -> SqliteRunRepository:
    return SqliteRunRepository(database)


def _change(
    state: RunState, expected: frozenset[RunState], seconds: int, outcome: RunOutcome | None = None
) -> StateChange:
    return StateChange("run-1", expected, state, _SUBMITTED + timedelta(seconds=seconds), outcome)


def test_a_stored_run_is_read_back_unchanged(runs: SqliteRunRepository) -> None:
    assert runs.add(_QUEUED) == _QUEUED
    assert runs.find("run-1") == _QUEUED
    assert runs.find_by_idempotency_key("key-1") == _QUEUED
    assert runs.find("run-2") is None


def test_adding_a_run_with_a_known_idempotency_key_returns_the_first_run(
    runs: SqliteRunRepository,
) -> None:
    runs.add(_QUEUED)

    stored = runs.add(replace(_QUEUED, identifier="run-2"))

    assert stored == _QUEUED
    assert runs.find("run-2") is None


def test_the_history_lists_the_most_recent_submission_first(runs: SqliteRunRepository) -> None:
    runs.add(_QUEUED)
    later = replace(
        _QUEUED,
        identifier="run-2",
        idempotency_key="key-2",
        parent_identifier="run-1",
        submitted_at=_SUBMITTED + timedelta(minutes=1),
    )
    runs.add(later)

    assert runs.recent() == (later, _QUEUED)


def test_a_run_moves_through_its_states_with_the_instants_recorded(
    runs: SqliteRunRepository,
) -> None:
    runs.add(_QUEUED)

    running = runs.transition(_change(RunState.RUNNING, frozenset({RunState.QUEUED}), 1))
    succeeded = runs.transition(
        _change(RunState.SUCCEEDED, frozenset({RunState.RUNNING}), 2, _PASSED)
    )

    assert running is not None
    assert (running.state, running.started_at, running.finished_at) == (
        RunState.RUNNING,
        _SUBMITTED + timedelta(seconds=1),
        None,
    )
    assert succeeded == replace(
        _QUEUED,
        state=RunState.SUCCEEDED,
        started_at=_SUBMITTED + timedelta(seconds=1),
        finished_at=_SUBMITTED + timedelta(seconds=2),
        verification_status="passed",
        headline="E = 0.3760301621 eV",
        artifacts=(_INPUT, _OUTCOME, _PROBLEM),
    )


def test_a_change_from_a_state_the_run_is_not_in_is_not_applied(
    runs: SqliteRunRepository,
) -> None:
    runs.add(_QUEUED)
    runs.transition(_change(RunState.CANCELLED, ACTIVE_STATES, 1))
    cancelled = runs.find("run-1")

    late = runs.transition(_change(RunState.SUCCEEDED, frozenset({RunState.RUNNING}), 2, _PASSED))

    assert late is None
    assert runs.find("run-1") == cancelled
    assert runs.referenced_artifacts() == {"a" * 64, "b" * 64}


def test_a_change_to_an_unknown_run_is_not_applied(runs: SqliteRunRepository) -> None:
    assert runs.transition(_change(RunState.RUNNING, frozenset({RunState.QUEUED}), 1)) is None


def test_interrupting_closes_only_the_runs_that_were_still_active(
    runs: SqliteRunRepository,
) -> None:
    runs.add(_QUEUED)
    finished = replace(_QUEUED, identifier="run-2", idempotency_key="key-2")
    runs.add(finished)
    runs.transition(
        StateChange("run-2", ACTIVE_STATES, RunState.CANCELLED, _SUBMITTED + timedelta(seconds=1))
    )
    cancelled = runs.find("run-2")

    interrupted = runs.interrupt_active(_SUBMITTED + timedelta(seconds=5))

    stopped = runs.find("run-1")
    assert interrupted == 1
    assert stopped is not None
    assert (stopped.state, stopped.finished_at) == (
        RunState.INTERRUPTED,
        _SUBMITTED + timedelta(seconds=5),
    )
    assert runs.find("run-2") == cancelled


def test_the_history_survives_reopening_the_database(database: Path) -> None:
    first = SqliteRunRepository(database)
    first.add(_QUEUED)
    first.transition(_change(RunState.RUNNING, frozenset({RunState.QUEUED}), 1))
    succeeded = first.transition(
        _change(RunState.SUCCEEDED, frozenset({RunState.RUNNING}), 2, _PASSED)
    )

    reopened = SqliteRunRepository(database)

    assert reopened.find("run-1") == succeeded
    assert reopened.referenced_artifacts() == {"a" * 64, "b" * 64, "c" * 64}


def test_a_history_written_by_a_newer_storage_schema_is_refused_untouched(database: Path) -> None:
    SqliteRunRepository(database).add(_QUEUED)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")

    with pytest.raises(NewerHistoryError) as refused:
        SqliteRunRepository(database)

    assert refused.value.found == SCHEMA_VERSION + 1
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT identifier FROM runs").fetchall() == [("run-1",)]
