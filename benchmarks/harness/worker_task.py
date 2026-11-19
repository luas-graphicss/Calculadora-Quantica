import resource
import time
from dataclasses import dataclass

from quantum_calculator.application.solve_numerical import (
    HomologatedNumericalMethod,
    NumericalOutcome,
)
from quantum_calculator.domain.numerical.problems import NumericalProblem

_KIBIBYTE = 1024


@dataclass(frozen=True, slots=True)
class MeasuredOutcome:
    outcome: NumericalOutcome
    solver_seconds: float
    verification_seconds: float
    peak_rss_bytes: int


def solve_and_verify_measured(
    method: HomologatedNumericalMethod, problem: NumericalProblem
) -> MeasuredOutcome:
    started = time.perf_counter()
    report = method.solver.solve(problem)
    solved = time.perf_counter()
    verification = method.verifier.verify(problem, report)
    verified = time.perf_counter()
    return MeasuredOutcome(
        outcome=NumericalOutcome(report, verification),
        solver_seconds=solved - started,
        verification_seconds=verified - solved,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * _KIBIBYTE,
    )
