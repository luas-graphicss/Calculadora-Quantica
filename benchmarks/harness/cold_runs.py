import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from benchmarks.harness.precision import NumericalRecord

_SOLVE_SECONDS = 600.0


@dataclass(frozen=True, slots=True)
class ColdRun:
    seconds: float
    record: NumericalRecord


@dataclass(frozen=True, slots=True)
class Refused:
    seconds: float
    exit_code: int
    diagnostics: list[dict[str, object]]


class ColdRunError(Exception):
    pass


def solve_in_new_process(command: str, source: Path) -> ColdRun:
    seconds, completed = _solve(command, source)
    if completed.returncode != 0:
        raise ColdRunError(
            f"{command} solve {source} exited with {completed.returncode}: "
            f"{completed.stderr.decode('utf-8', 'replace').strip()}"
        )
    record: NumericalRecord = json.loads(completed.stdout)
    return ColdRun(seconds, record)


def refuse_in_new_process(command: str, source: Path) -> Refused:
    seconds, completed = _solve(command, source)
    if completed.stdout:
        raise ColdRunError(f"{command} solve {source} printed a result for a refused request")
    rejection = json.loads(completed.stderr)
    return Refused(seconds, completed.returncode, rejection["diagnostics"])


def _solve(command: str, source: Path) -> tuple[float, subprocess.CompletedProcess[bytes]]:
    started = time.perf_counter()
    completed = subprocess.run(  # noqa: S603 - the command is the qcalc under measurement, with fixed arguments
        [command, "solve", str(source), "--format", "json"],
        capture_output=True,
        check=False,
        timeout=_SOLVE_SECONDS,
    )
    return time.perf_counter() - started, completed
