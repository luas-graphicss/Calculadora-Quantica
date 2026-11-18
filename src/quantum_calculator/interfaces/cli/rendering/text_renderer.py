from quantum_calculator.application.review_problem import ProblemReview
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.rounding import ROUNDING_MODE
from quantum_calculator.domain.run_record import RunRecord
from quantum_calculator.interfaces.cli.rendering.text.formatting import QuantityFormatter, printable
from quantum_calculator.interfaces.cli.rendering.text.problem_sections import (
    problem_sections,
    request_section,
)
from quantum_calculator.interfaces.cli.rendering.text.record_sections import (
    answer_lines,
    calculation_section,
    constants_section,
    environment_section,
    limitations_section,
    uncertainty_section,
    verification_section,
)


class TextRenderer:
    def __init__(self, units: UnitRegistry) -> None:
        self._numbers = QuantityFormatter(units)

    def validation(self, review: ProblemReview) -> str:
        problem = review.problem
        method = review.plan.method
        digits = review.plan.rounding.significant_digits
        return _join(
            [
                f"Entrada válida: {problem.card.identifier} {problem.card.version}",
                f"plano: {method.identifier}, resultado {method.nature.value}, "
                f"{digits} algarismos significativos, arredondamento {ROUNDING_MODE}",
                *problem_sections(problem, self._numbers),
                *request_section(problem, self._numbers),
            ]
        )

    def run_record(self, record: RunRecord) -> str:
        return _join(
            [
                *answer_lines(record),
                *problem_sections(record.problem, self._numbers),
                *constants_section(record, self._numbers),
                *calculation_section(record, self._numbers),
                *uncertainty_section(record, self._numbers),
                *verification_section(record),
                *limitations_section(record),
                *environment_section(record),
            ]
        )

    def rejection(self, rejection: ProblemRejectedError) -> str:
        lines = [f"Entrada recusada ({rejection.category.value})"]
        for item in rejection.diagnostics:
            lines.append(f"  {printable(item.pointer) or '/'} [{item.code.value}]")
            lines.append(f"    {printable(item.message)}")
            lines.append(f"    esperado: {printable(item.expected)}")
        return _join(lines)


def _join(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"
