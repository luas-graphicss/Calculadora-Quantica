import os
import time

from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode, ProblemRejectedError

REJECTION = Diagnostic(DiagnosticCode.OUTSIDE_COVERAGE, "/statement", "fora da cobertura", "outro")
_GIBIBYTE = 1024**3


def process_identifier() -> int:
    return os.getpid()


def stall() -> None:
    time.sleep(600)


def spin() -> None:
    while True:
        pass


def claim_eight_gibibytes() -> int:
    return len(bytearray(8 * _GIBIBYTE))


def descend(level: int = 0) -> int:
    return descend(level + 1)


def reject() -> None:
    raise ProblemRejectedError((REJECTION,))


def crash() -> None:
    os._exit(3)
