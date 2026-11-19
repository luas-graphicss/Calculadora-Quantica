from dataclasses import dataclass

from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode, json_pointer
from quantum_calculator.domain.numerical.cards import NumericalCard
from quantum_calculator.domain.numerical.spec import NumericalSpec


@dataclass(frozen=True, slots=True)
class ValidationRequest:
    card: NumericalCard
    spec: NumericalSpec
    diagnostics: list[Diagnostic]

    def refuse(self, code: DiagnosticCode, pointer: str, message: str, expected: str) -> None:
        self.diagnostics.append(Diagnostic(code, pointer, message, expected))


def pointer_to(*segments: str) -> str:
    return json_pointer(*segments)
