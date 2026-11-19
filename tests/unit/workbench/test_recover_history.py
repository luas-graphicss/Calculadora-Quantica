from pathlib import Path

from quantum_calculator.adapters.storage.file_artifacts import FileArtifactStore
from quantum_calculator.adapters.storage.sqlite_runs import SqliteRunRepository
from quantum_calculator.application.workbench.read_history import ReadHistory
from quantum_calculator.application.workbench.recover_history import (
    InterruptActiveRuns,
    RecoverHistory,
    RecoveryReport,
)
from quantum_calculator.application.workbench.submit_run import Submission
from quantum_calculator.domain.execution import CancellationSignal
from quantum_calculator.domain.workbench.documents import Document
from quantum_calculator.domain.workbench.runs import ArtifactRole, RunState, StateChange
from support.workbench import RECORD, SOURCE, Bench, SteppingClock, build_bench


def _submit(bench: Bench, key: str) -> str:
    return bench.submit.execute(Submission(SOURCE, key, wall_seconds=30.0)).run.identifier


def _restart(directory: Path) -> tuple[SqliteRunRepository, FileArtifactStore, RecoveryReport]:
    runs = SqliteRunRepository(directory / "history.sqlite3")
    artifacts = FileArtifactStore(directory / "artifacts")
    return runs, artifacts, RecoverHistory(runs, artifacts, SteppingClock()).execute()


def test_runs_left_unfinished_by_the_previous_process_become_interrupted(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    waiting = _submit(bench, "submission-key-0001")
    calculating = _submit(bench, "submission-key-0002")
    bench.runs.transition(
        StateChange(calculating, frozenset({RunState.QUEUED}), RunState.RUNNING, bench.clock.now())
    )

    runs, _, report = _restart(tmp_path)

    assert report.interrupted_runs == 2
    for identifier in (waiting, calculating):
        run = runs.find(identifier)
        assert run is not None
        assert run.state is RunState.INTERRUPTED
        assert run.finished_at is not None
        assert run.artifact(ArtifactRole.OUTCOME) is None
        assert run.verification_status is None


def test_a_finished_run_survives_the_restart_with_its_record(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    identifier = _submit(bench, "submission-key-0001")
    bench.execute.execute(identifier)
    completed = bench.runs.find(identifier)

    runs, artifacts, report = _restart(tmp_path)

    assert report == RecoveryReport(interrupted_runs=0, removed_orphans=0)
    assert runs.find(identifier) == completed
    assert ReadHistory(runs, artifacts).complete_outcome(identifier) == RECORD


def test_files_published_without_a_record_are_removed_and_referenced_ones_kept(
    tmp_path: Path,
) -> None:
    bench = build_bench(tmp_path)
    identifier = _submit(bench, "submission-key-0001")
    bench.execute.execute(identifier)
    orphan = bench.artifacts.publish(b"published before a transaction that never committed", "x")
    partial = tmp_path / "artifacts" / orphan.sha256[:2] / "tmp-partial-write"
    partial.write_bytes(b"half a file")

    runs, artifacts, report = _restart(tmp_path)

    assert report.removed_orphans == 2
    assert not partial.exists()
    assert not (partial.parent / orphan.sha256).exists()
    assert ReadHistory(runs, artifacts).complete_outcome(identifier) == RECORD


def test_stopping_the_application_interrupts_the_running_calculation(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    identifier = _submit(bench, "submission-key-0001")
    stop = InterruptActiveRuns(bench.runs, bench.cancellations, bench.clock)
    signalled: list[bool] = []

    def stopped_midway(
        _source: bytes, _wall_seconds: float, cancellation: CancellationSignal
    ) -> Document:
        stop.execute()
        signalled.append(cancellation.is_set())
        return RECORD

    bench.documents.calculation = stopped_midway

    bench.execute.execute(identifier)

    run = bench.runs.find(identifier)
    assert run is not None
    assert signalled == [True]
    assert run.state is RunState.INTERRUPTED
    assert run.artifact(ArtifactRole.OUTCOME) is None
