from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from quantum_calculator.composition import Calculator
from quantum_calculator.domain.diagnostics import DiagnosticCategory, ProblemRejectedError
from quantum_calculator.domain.execution import (
    CalculationCancelledError,
    CalculationFailedError,
    CancellationSignal,
)
from quantum_calculator.domain.statements import StatementSpec
from quantum_calculator.domain.verification import VerificationReport, VerificationStatus
from quantum_calculator.interfaces.cli.exit_codes import ExitCode
from quantum_calculator.interfaces.cli.rendering.renderer import ReportRenderer
from quantum_calculator.interfaces.serialization.decoding.input_decoder import (
    InputSpec,
    decode_input,
)
from quantum_calculator.interfaces.serialization.decoding.json_document import MAX_DOCUMENT_BYTES

_EXIT_CODE_BY_CATEGORY = {
    DiagnosticCategory.INVALID_INPUT: ExitCode.INVALID_INPUT,
    DiagnosticCategory.UNSUPPORTED_PROBLEM: ExitCode.UNSUPPORTED_PROBLEM,
    DiagnosticCategory.AMBIGUOUS_INPUT: ExitCode.AMBIGUOUS_INPUT,
    DiagnosticCategory.BUDGET_EXCEEDED: ExitCode.BUDGET_EXCEEDED,
}
_NOTHING_KEPT = "nenhum resultado parcial foi aproveitado"


class ProblemCommands:
    def __init__(
        self,
        calculator: Calculator,
        renderer: ReportRenderer,
        stdout: TextIO,
        stderr: TextIO,
        cancellation: CancellationSignal,
    ) -> None:
        self._calculator = calculator
        self._renderer = renderer
        self._stdout = stdout
        self._stderr = stderr
        self._cancellation = cancellation

    def validate(self, path: Path) -> ExitCode:
        return self._run(path, self._review)

    def solve(self, path: Path) -> ExitCode:
        return self._run(path, self._solve)

    def _review(self, spec: InputSpec) -> ExitCode:
        if isinstance(spec, StatementSpec):
            review = self._calculator.review_statement.execute(spec)
            self._stdout.write(self._renderer.statement_validation(review))
        else:
            self._stdout.write(
                self._renderer.validation(self._calculator.review_problem.execute(spec))
            )
        return ExitCode.SUCCESS

    def _solve(self, spec: InputSpec) -> ExitCode:
        if isinstance(spec, StatementSpec):
            solved = self._calculator.solve_statement.execute(spec, self._cancellation)
            self._stdout.write(self._renderer.statement_run_record(solved))
            return _exit_code_for(solved.verification)
        record = self._calculator.solve_problem.execute(spec)
        self._stdout.write(self._renderer.run_record(record))
        return _exit_code_for(record.verification)

    def _run(self, path: Path, command: Callable[[InputSpec], ExitCode]) -> ExitCode:
        try:
            raw = _read(path)
        except OSError as error:
            self._stderr.write(f"qcalc: não foi possível ler {path}: {error.strerror}\n")
            return ExitCode.INPUT_UNREADABLE
        try:
            return command(decode_input(raw))
        except ProblemRejectedError as rejection:
            self._stderr.write(self._renderer.rejection(rejection))
            return _EXIT_CODE_BY_CATEGORY[rejection.category]
        except CalculationCancelledError:
            self._stderr.write(f"qcalc: cálculo cancelado; {_NOTHING_KEPT}.\n")
            return ExitCode.CANCELLED
        except CalculationFailedError as failure:
            self._stderr.write(
                "qcalc: o processo de cálculo terminou sem resultado (código de saída "
                f"{failure.exit_code}); {_NOTHING_KEPT}.\n"
            )
            return ExitCode.CALCULATION_FAILED


def _exit_code_for(verification: VerificationReport) -> ExitCode:
    if verification.status is VerificationStatus.PASSED:
        return ExitCode.SUCCESS
    return ExitCode.VERIFICATION_NOT_PASSED


def _read(path: Path) -> bytes:
    with path.open("rb") as stream:
        return stream.read(MAX_DOCUMENT_BYTES + 1)
