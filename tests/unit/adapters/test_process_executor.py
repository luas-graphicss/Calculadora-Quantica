import multiprocessing
import os
import threading
import time
from collections.abc import Callable

import pytest

from quantum_calculator.adapters.execution.process_executor import ProcessExecutor
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.execution import (
    BudgetExceededError,
    BudgetResource,
    CalculationCancelledError,
    CalculationFailedError,
    ExecutionBudget,
    NeverCancelled,
)
from support import tasks

GIBIBYTE = 1024**3
GENEROUS = ExecutionBudget(wall_seconds=60.0, cpu_seconds=60, memory_bytes=4 * GIBIBYTE)
SHORT = ExecutionBudget(wall_seconds=1.5, cpu_seconds=60, memory_bytes=4 * GIBIBYTE)


@pytest.fixture
def executor() -> ProcessExecutor:
    return ProcessExecutor()


def _run_within[Result](
    executor: ProcessExecutor, task: Callable[[], Result], budget: ExecutionBudget = GENEROUS
) -> Result:
    return executor.run(task, budget, NeverCancelled())


def _is_usable(executor: ProcessExecutor) -> bool:
    return _run_within(executor, tasks.process_identifier) != os.getpid()


def test_task_runs_in_a_separate_process_and_returns_its_value(executor: ProcessExecutor) -> None:
    identifier = _run_within(executor, tasks.process_identifier)

    assert identifier != os.getpid()
    assert multiprocessing.active_children() == []


def test_task_over_its_wall_time_is_stopped_and_the_next_one_runs(
    executor: ProcessExecutor,
) -> None:
    started = time.monotonic()

    with pytest.raises(BudgetExceededError) as exceeded:
        _run_within(executor, tasks.stall, SHORT)

    assert exceeded.value.resource is BudgetResource.WALL_TIME
    assert time.monotonic() - started < 30
    assert multiprocessing.active_children() == []
    assert _is_usable(executor)


def test_task_over_its_cpu_time_is_stopped_by_the_operating_system(
    executor: ProcessExecutor,
) -> None:
    budget = ExecutionBudget(wall_seconds=60.0, cpu_seconds=1, memory_bytes=4 * GIBIBYTE)

    with pytest.raises(BudgetExceededError) as exceeded:
        _run_within(executor, tasks.spin, budget)

    assert exceeded.value.resource is BudgetResource.CPU_TIME
    assert _is_usable(executor)


def test_task_over_its_memory_limit_is_reported_as_memory_exhaustion(
    executor: ProcessExecutor,
) -> None:
    budget = ExecutionBudget(wall_seconds=60.0, cpu_seconds=60, memory_bytes=2 * GIBIBYTE)

    with pytest.raises(BudgetExceededError) as exceeded:
        _run_within(executor, tasks.claim_eight_gibibytes, budget)

    assert exceeded.value.resource is BudgetResource.MEMORY
    assert _is_usable(executor)


def test_runaway_recursion_is_reported_as_depth_exhaustion(executor: ProcessExecutor) -> None:
    with pytest.raises(BudgetExceededError) as exceeded:
        _run_within(executor, tasks.descend)

    assert exceeded.value.resource is BudgetResource.RECURSION_DEPTH


def test_rejection_raised_by_the_task_crosses_the_process_boundary(
    executor: ProcessExecutor,
) -> None:
    with pytest.raises(ProblemRejectedError) as rejection:
        _run_within(executor, tasks.reject)

    assert rejection.value.diagnostics == (tasks.REJECTION,)


def test_process_that_dies_without_a_result_is_a_failure_not_a_result(
    executor: ProcessExecutor,
) -> None:
    with pytest.raises(CalculationFailedError, match="exit code 3"):
        _run_within(executor, tasks.crash)

    assert _is_usable(executor)


def test_cancellation_releases_the_process_and_the_next_task_runs(
    executor: ProcessExecutor,
) -> None:
    cancellation = threading.Event()
    timer = threading.Timer(1.0, cancellation.set)
    timer.start()

    with pytest.raises(CalculationCancelledError):
        executor.run(tasks.stall, GENEROUS, cancellation)

    timer.join()
    assert multiprocessing.active_children() == []
    assert _is_usable(executor)


def test_task_cancelled_before_it_starts_never_returns_a_value(executor: ProcessExecutor) -> None:
    cancellation = threading.Event()
    cancellation.set()

    with pytest.raises(CalculationCancelledError):
        executor.run(tasks.stall, GENEROUS, cancellation)

    assert multiprocessing.active_children() == []
