import multiprocessing
import resource
import signal
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from multiprocessing import resource_tracker
from multiprocessing.connection import Connection
from multiprocessing.context import SpawnProcess
from typing import Final

from quantum_calculator.domain.diagnostics import Diagnostic, ProblemRejectedError
from quantum_calculator.domain.execution import (
    BudgetExceededError,
    BudgetResource,
    CalculationCancelledError,
    CalculationFailedError,
    CancellationSignal,
    ExecutionBudget,
)

_START_METHOD: Final = "spawn"
_POLL_SECONDS = 0.02
_SHUTDOWN_SECONDS = 2.0
_RESOURCE_BY_FATAL_SIGNAL: dict[int, BudgetResource] = {
    signal.SIGXCPU: BudgetResource.CPU_TIME,
    signal.SIGKILL: BudgetResource.MEMORY,
}


@dataclass(frozen=True, slots=True)
class _Completed[Result]:
    value: Result


@dataclass(frozen=True, slots=True)
class _Rejected:
    diagnostics: tuple[Diagnostic, ...]


@dataclass(frozen=True, slots=True)
class _Exhausted:
    resource: BudgetResource


type _Outcome[Result] = _Completed[Result] | _Rejected | _Exhausted


class ProcessExecutor:
    def run[Result](
        self, task: Callable[[], Result], budget: ExecutionBudget, cancellation: CancellationSignal
    ) -> Result:
        context = multiprocessing.get_context(_START_METHOD)
        receiver, sender = context.Pipe(duplex=False)
        process = context.Process(target=_work, args=(task, budget, sender), daemon=True)
        resource_tracker.ensure_running()
        with _interrupts_deferred():
            process.start()
        sender.close()
        try:
            outcome: _Outcome[Result] = _await_outcome(process, receiver, budget, cancellation)
        finally:
            _dispose(process)
            receiver.close()
        if isinstance(outcome, _Rejected):
            raise ProblemRejectedError(outcome.diagnostics)
        if isinstance(outcome, _Exhausted):
            raise BudgetExceededError(outcome.resource)
        return outcome.value


@contextmanager
def _interrupts_deferred() -> Iterator[None]:
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


def _await_outcome[Result](
    process: SpawnProcess,
    receiver: Connection,
    budget: ExecutionBudget,
    cancellation: CancellationSignal,
) -> _Outcome[Result]:
    deadline = time.monotonic() + budget.wall_seconds
    while not receiver.poll(_POLL_SECONDS):
        if cancellation.is_set():
            raise CalculationCancelledError
        if time.monotonic() >= deadline:
            raise BudgetExceededError(BudgetResource.WALL_TIME)
        if not process.is_alive() and not receiver.poll():
            return _exhausted_by_signal(process)
    try:
        outcome: _Outcome[Result] = receiver.recv()
    except EOFError:
        return _exhausted_by_signal(process)
    return outcome


def _exhausted_by_signal(process: SpawnProcess) -> _Exhausted:
    process.join()
    code = process.exitcode
    exhausted = None if code is None else _RESOURCE_BY_FATAL_SIGNAL.get(-code)
    if exhausted is None:
        raise CalculationFailedError(code)
    return _Exhausted(exhausted)


def _dispose(process: SpawnProcess) -> None:
    if process.is_alive():
        process.terminate()
        process.join(_SHUTDOWN_SECONDS)
    if process.is_alive():
        process.kill()
        process.join()
    process.close()


def _work[Result](task: Callable[[], Result], budget: ExecutionBudget, sender: Connection) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    _limit(resource.RLIMIT_CPU, budget.cpu_seconds)
    address_space = _limit(resource.RLIMIT_AS, budget.memory_bytes)
    outcome: _Outcome[Result]
    try:
        outcome = _Completed(task())
    except ProblemRejectedError as rejection:
        outcome = _Rejected(rejection.diagnostics)
    except MemoryError:
        resource.setrlimit(resource.RLIMIT_AS, address_space)
        outcome = _Exhausted(BudgetResource.MEMORY)
    except RecursionError:
        outcome = _Exhausted(BudgetResource.RECURSION_DEPTH)
    sender.send(outcome)
    sender.close()


def _limit(kind: int, amount: int) -> tuple[int, int]:
    previous = resource.getrlimit(kind)
    _, hard = previous
    allowed = amount if hard == resource.RLIM_INFINITY else min(amount, hard)
    resource.setrlimit(kind, (allowed, hard))
    return previous
