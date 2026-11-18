from collections.abc import Callable

from quantum_calculator.domain.execution import CancellationSignal, ExecutionBudget


class InlineExecutor:
    def run[Result](
        self,
        task: Callable[[], Result],
        _budget: ExecutionBudget,
        _cancellation: CancellationSignal,
    ) -> Result:
        return task()


class RaisingExecutor:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def run[Result](
        self,
        _task: Callable[[], Result],
        _budget: ExecutionBudget,
        _cancellation: CancellationSignal,
    ) -> Result:
        raise self._error
