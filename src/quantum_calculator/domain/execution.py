from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ExecutionBudget:
    wall_seconds: float
    cpu_seconds: int
    memory_bytes: int


class BudgetResource(StrEnum):
    WALL_TIME = "wall_time"
    CPU_TIME = "cpu_time"
    MEMORY = "memory"
    RECURSION_DEPTH = "recursion_depth"


class BudgetExceededError(Exception):
    def __init__(self, resource: BudgetResource) -> None:
        super().__init__(f"calculation exceeded its {resource.value} budget")
        self.resource = resource


class CalculationCancelledError(Exception):
    pass


class CalculationFailedError(Exception):
    pass


class CancellationSignal(Protocol):
    def is_set(self) -> bool: ...


class NeverCancelled:
    def is_set(self) -> bool:
        return False
