from pathlib import Path
from typing import TextIO

from quantum_calculator.composition import Calculator
from quantum_calculator.domain.diagnostics import DiagnosticCategory, ProblemRejectedError
from quantum_calculator.domain.verification import VerificationStatus
from quantum_calculator.interfaces.cli.exit_codes import ExitCode
from quantum_calculator.interfaces.cli.rendering.renderer import ReportRenderer
from quantum_calculator.interfaces.serialization.decoding.json_document import MAX_DOCUMENT_BYTES
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import decode_problem

_EXIT_CODE_BY_CATEGORY = {
    DiagnosticCategory.INVALID_INPUT: ExitCode.INVALID_INPUT,
    DiagnosticCategory.UNSUPPORTED_PROBLEM: ExitCode.UNSUPPORTED_PROBLEM,
}


class ProblemCommands:
    def __init__(
        self, calculator: Calculator, renderer: ReportRenderer, stdout: TextIO, stderr: TextIO
    ) -> None:
        self._calculator = calculator
        self._renderer = renderer
        self._stdout = stdout
        self._stderr = stderr

    def validate(self, path: Path) -> ExitCode:
        try:
            review = self._calculator.review_problem.execute(decode_problem(_read(path)))
        except OSError as error:
            return self._report_unreadable(path, error)
        except ProblemRejectedError as rejection:
            return self._report_rejection(rejection)
        self._stdout.write(self._renderer.validation(review))
        return ExitCode.SUCCESS

    def solve(self, path: Path) -> ExitCode:
        try:
            record = self._calculator.solve_problem.execute(decode_problem(_read(path)))
        except OSError as error:
            return self._report_unreadable(path, error)
        except ProblemRejectedError as rejection:
            return self._report_rejection(rejection)
        self._stdout.write(self._renderer.run_record(record))
        if record.verification.status is not VerificationStatus.PASSED:
            return ExitCode.VERIFICATION_NOT_PASSED
        return ExitCode.SUCCESS

    def _report_unreadable(self, path: Path, error: OSError) -> ExitCode:
        self._stderr.write(f"qcalc: não foi possível ler {path}: {error.strerror}\n")
        return ExitCode.INPUT_UNREADABLE

    def _report_rejection(self, rejection: ProblemRejectedError) -> ExitCode:
        self._stderr.write(self._renderer.rejection(rejection))
        return _EXIT_CODE_BY_CATEGORY[rejection.category]


def _read(path: Path) -> bytes:
    with path.open("rb") as stream:
        return stream.read(MAX_DOCUMENT_BYTES + 1)
