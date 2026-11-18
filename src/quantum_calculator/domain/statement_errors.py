from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.expressions import SourceSpan


class StatementError(Exception):
    def __init__(self, code: DiagnosticCode, span: SourceSpan, message: str, expected: str) -> None:
        super().__init__(message)
        self.code = code
        self.span = span
        self.message = message
        self.expected = expected
