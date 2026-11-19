from pathlib import Path

import pytest

from quantum_calculator.application.workbench.cancel_run import CancelRun
from quantum_calculator.application.workbench.read_history import ReadHistory
from quantum_calculator.application.workbench.submit_run import Submission
from quantum_calculator.domain.execution import (
    CalculationCancelledError,
    CalculationFailedError,
    CancellationSignal,
)
from quantum_calculator.domain.workbench.documents import Document, text_member
from quantum_calculator.domain.workbench.runs import (
    ArtifactRole,
    RunNotFoundError,
    RunState,
    StoredRun,
)
from support.workbench import (
    RECORD,
    REJECTION,
    SOURCE,
    Bench,
    ScriptedDocuments,
    build_bench,
    raising,
    returning,
)


def _queued(bench: Bench, key: str = "submission-key-0001") -> StoredRun:
    return bench.submit.execute(Submission(SOURCE, key, wall_seconds=30.0)).run


def _settled(bench: Bench, identifier: str) -> StoredRun:
    run = bench.runs.find(identifier)
    assert run is not None
    return run


def test_a_completed_calculation_is_recorded_with_its_verification_status(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    queued = _queued(bench)

    bench.execute.execute(queued.identifier)

    run = _settled(bench, queued.identifier)
    assert run.state is RunState.SUCCEEDED
    assert (run.verification_status, run.failure_category) == ("passed", None)
    assert run.headline == "E_1 = 0.375000 eV"
    assert run.started_at is not None
    assert run.finished_at is not None
    assert run.started_at < run.finished_at
    assert ReadHistory(bench.runs, bench.artifacts).complete_outcome(run.identifier) == RECORD


def test_the_stored_record_refers_to_its_tables_instead_of_embedding_them(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    queued = _queued(bench)

    bench.execute.execute(queued.identifier)

    run = _settled(bench, queued.identifier)
    details = ReadHistory(bench.runs, bench.artifacts).details(run.identifier)
    assert details.outcome is not None
    assert run.artifact("table:eigenfunctions") is not None
    assert b'"values"' not in bench.artifacts.read(run.require_artifact(ArtifactRole.OUTCOME))
    assert details.input_text == SOURCE.decode()


def test_a_refusal_during_the_calculation_fails_the_run_with_its_category(tmp_path: Path) -> None:
    bench = build_bench(tmp_path, ScriptedDocuments(calculation=returning(REJECTION)))
    queued = _queued(bench)

    bench.execute.execute(queued.identifier)

    run = _settled(bench, queued.identifier)
    assert run.state is RunState.FAILED
    assert (run.failure_category, run.verification_status, run.headline) == (
        "non_convergent",
        None,
        None,
    )


def test_a_calculation_process_that_dies_fails_the_run_without_a_result(tmp_path: Path) -> None:
    bench = build_bench(
        tmp_path, ScriptedDocuments(calculation=raising(CalculationFailedError(-9)))
    )
    queued = _queued(bench)

    bench.execute.execute(queued.identifier)

    run = _settled(bench, queued.identifier)
    outcome = ReadHistory(bench.runs, bench.artifacts).details(run.identifier).outcome
    assert run.state is RunState.FAILED
    assert run.failure_category == "calculation_failed"
    assert outcome is not None
    assert "-9" in (text_member(outcome, "message") or "")
    assert run.verification_status is None


def test_an_unexpected_error_fails_the_run_and_is_not_swallowed(tmp_path: Path) -> None:
    bench = build_bench(tmp_path, ScriptedDocuments(calculation=raising(RuntimeError("defect"))))
    queued = _queued(bench)

    with pytest.raises(RuntimeError, match="defect"):
        bench.execute.execute(queued.identifier)

    run = _settled(bench, queued.identifier)
    assert (run.state, run.failure_category) == (RunState.FAILED, "internal_error")


def test_a_failed_run_leaves_earlier_results_untouched(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    first = _queued(bench, "submission-key-0001")
    bench.execute.execute(first.identifier)
    completed = _settled(bench, first.identifier)
    bench.documents.calculation = raising(CalculationFailedError(-9))
    second = _queued(bench, "submission-key-0002")

    bench.execute.execute(second.identifier)

    assert _settled(bench, second.identifier).state is RunState.FAILED
    assert _settled(bench, first.identifier) == completed
    assert ReadHistory(bench.runs, bench.artifacts).complete_outcome(first.identifier) == RECORD


def test_a_run_cancelled_while_queued_is_never_calculated(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    queued = _queued(bench)
    cancel = CancelRun(bench.runs, bench.cancellations, bench.clock)

    cancelled = cancel.execute(queued.identifier)
    bench.execute.execute(queued.identifier)

    assert cancelled.state is RunState.CANCELLED
    assert bench.documents.calculated == []
    assert _settled(bench, queued.identifier).state is RunState.CANCELLED


def test_cancelling_a_running_calculation_signals_it_and_discards_the_result(
    tmp_path: Path,
) -> None:
    bench = build_bench(tmp_path)
    queued = _queued(bench)
    cancel = CancelRun(bench.runs, bench.cancellations, bench.clock)
    observed: list[bool] = []

    def cancelled_midway(
        _source: bytes, _wall_seconds: float, cancellation: CancellationSignal
    ) -> Document:
        cancel.execute(queued.identifier)
        observed.append(cancellation.is_set())
        raise CalculationCancelledError

    bench.documents.calculation = cancelled_midway

    bench.execute.execute(queued.identifier)

    run = _settled(bench, queued.identifier)
    assert observed == [True]
    assert run.state is RunState.CANCELLED
    assert run.artifact(ArtifactRole.OUTCOME) is None
    assert run.verification_status is None


def test_a_cancellation_that_races_with_completion_leaves_one_terminal_state(
    tmp_path: Path,
) -> None:
    bench = build_bench(tmp_path)
    queued = _queued(bench)
    cancel = CancelRun(bench.runs, bench.cancellations, bench.clock)

    def completes_after_the_cancellation(
        _source: bytes, _wall_seconds: float, _cancellation: CancellationSignal
    ) -> Document:
        cancel.execute(queued.identifier)
        return RECORD

    bench.documents.calculation = completes_after_the_cancellation

    bench.execute.execute(queued.identifier)

    run = _settled(bench, queued.identifier)
    assert run.state is RunState.CANCELLED
    assert run.artifact(ArtifactRole.OUTCOME) is None
    assert run.headline is None


def test_cancelling_a_finished_run_keeps_its_result(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    queued = _queued(bench)
    bench.execute.execute(queued.identifier)
    completed = _settled(bench, queued.identifier)

    settled = CancelRun(bench.runs, bench.cancellations, bench.clock).execute(queued.identifier)

    assert settled == completed
    assert settled.state is RunState.SUCCEEDED


def test_cancelling_an_unknown_run_is_refused(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)

    with pytest.raises(RunNotFoundError):
        CancelRun(bench.runs, bench.cancellations, bench.clock).execute("run-404")
