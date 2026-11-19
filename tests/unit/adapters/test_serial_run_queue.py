import threading

import pytest

from quantum_calculator.adapters.execution.serial_run_queue import SerialRunQueue


def test_runs_are_executed_one_at_a_time_in_submission_order() -> None:
    executed: list[str] = []
    overlapping: list[str] = []
    busy = threading.Lock()

    def execute(identifier: str) -> None:
        if not busy.acquire(blocking=False):
            overlapping.append(identifier)
            return
        try:
            executed.append(identifier)
        finally:
            busy.release()

    runs = SerialRunQueue(execute)
    for identifier in ("run-1", "run-2", "run-3"):
        runs.enqueue(identifier)
    runs.close()

    assert executed == ["run-1", "run-2", "run-3"]
    assert overlapping == []


def test_an_error_in_one_run_is_logged_and_does_not_stop_the_next(
    caplog: pytest.LogCaptureFixture,
) -> None:
    executed: list[str] = []

    def execute(identifier: str) -> None:
        if identifier == "run-1":
            raise RuntimeError("defect")
        executed.append(identifier)

    runs = SerialRunQueue(execute)
    runs.enqueue("run-1")
    runs.enqueue("run-2")
    runs.close()

    assert executed == ["run-2"]
    assert "run run-1 ended with an unexpected error" in caplog.text
