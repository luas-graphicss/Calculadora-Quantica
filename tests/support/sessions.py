import os
from pathlib import Path

from quantum_calculator.application.workbench.submit_run import Submission
from quantum_calculator.domain.workbench.runs import ACTIVE_STATES, RunState, StoredRun
from quantum_calculator.workbench_composition import Workbench
from support.processes import children_running, wait_until

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
LONG_CALCULATION = (FIXTURES / "inputs" / "long_time_evolution.json").read_bytes()
TIME_LIMIT = 120.0

_CALCULATION_PROCESS = b"spawn_main"


def submit(workbench: Workbench, source: bytes, key: str, parent: str | None = None) -> StoredRun:
    return workbench.submit.execute(Submission(source, key, TIME_LIMIT, parent)).run


def settled(workbench: Workbench, identifier: str) -> StoredRun:
    wait_until(lambda: workbench.history.run(identifier).state not in ACTIVE_STATES, seconds=120)
    return workbench.history.run(identifier)


def calculation_processes() -> list[int]:
    return children_running(os.getpid(), _CALCULATION_PROCESS)


def calculating(workbench: Workbench, identifier: str) -> int:
    wait_until(lambda: workbench.history.run(identifier).state is RunState.RUNNING)
    wait_until(lambda: bool(calculation_processes()))
    return calculation_processes()[0]
