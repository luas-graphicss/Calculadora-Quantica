from pathlib import Path

import pytest

from quantum_calculator.application.workbench.canonical_documents import parse_document
from quantum_calculator.application.workbench.submit_run import (
    IdempotencyConflictError,
    Submission,
    SubmissionRejectedError,
)
from quantum_calculator.domain.workbench.runs import (
    ArtifactRole,
    RunNotFoundError,
    RunOrigin,
    RunState,
)
from support.workbench import (
    CARD,
    INTERPRETATION,
    OTHER_SOURCE,
    PACKAGE_VERSION,
    REJECTION,
    SOURCE,
    ScriptedDocuments,
    build_bench,
)

_KEY = "submission-key-0001"


def _submission(source: bytes = SOURCE, key: str = _KEY, parent: str | None = None) -> Submission:
    return Submission(
        source=source, idempotency_key=key, wall_seconds=30.0, parent_identifier=parent
    )


def test_an_accepted_problem_becomes_a_queued_run(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)

    receipt = bench.submit.execute(_submission())

    run = receipt.run
    assert receipt.created
    assert (run.state, run.origin, run.card_identifier) == (RunState.QUEUED, RunOrigin.LOCAL, CARD)
    assert (run.package_version, run.wall_seconds) == (PACKAGE_VERSION, 30.0)
    assert bench.queue.enqueued == [run.identifier]
    assert bench.runs.find(run.identifier) == run


def test_the_original_input_and_the_canonical_problem_are_kept(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)

    run = bench.submit.execute(_submission()).run

    assert bench.artifacts.read(run.require_artifact(ArtifactRole.INPUT)) == SOURCE
    problem = parse_document(bench.artifacts.read(run.require_artifact(ArtifactRole.PROBLEM)))
    assert problem == {key: value for key, value in INTERPRETATION.items() if key != "input"}


def test_repeating_a_submission_returns_the_same_run_without_a_second_job(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    first = bench.submit.execute(_submission())

    repeated = bench.submit.execute(_submission())

    assert not repeated.created
    assert repeated.run.identifier == first.run.identifier
    assert bench.queue.enqueued == [first.run.identifier]
    assert len(bench.runs.recent()) == 1


def test_a_key_reused_with_another_input_is_a_conflict(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    first = bench.submit.execute(_submission())

    with pytest.raises(IdempotencyConflictError) as conflict:
        bench.submit.execute(_submission(source=OTHER_SOURCE))

    assert conflict.value.run_identifier == first.run.identifier
    assert len(bench.runs.recent()) == 1


def test_a_rejected_problem_creates_no_run(tmp_path: Path) -> None:
    bench = build_bench(tmp_path, ScriptedDocuments(interpretation=REJECTION))

    with pytest.raises(SubmissionRejectedError) as rejected:
        bench.submit.execute(_submission())

    assert rejected.value.rejection == REJECTION
    assert bench.runs.recent() == ()
    assert bench.queue.enqueued == []


def test_a_changed_problem_is_linked_to_the_run_it_came_from(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)
    original = bench.submit.execute(_submission()).run

    changed = bench.submit.execute(
        _submission(source=OTHER_SOURCE, key="submission-key-0002", parent=original.identifier)
    ).run

    assert changed.parent_identifier == original.identifier
    assert bench.runs.find(original.identifier) == original


def test_a_parent_that_is_not_in_the_history_is_refused(tmp_path: Path) -> None:
    bench = build_bench(tmp_path)

    with pytest.raises(RunNotFoundError):
        bench.submit.execute(_submission(parent="run-404"))

    assert bench.runs.recent() == ()
