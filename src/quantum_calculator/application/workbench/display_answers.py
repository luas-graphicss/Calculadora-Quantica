from dataclasses import dataclass
from fractions import Fraction

from quantum_calculator.application.workbench.answers import (
    ReportedAnswer,
    reported_answers,
    significant_digits,
)
from quantum_calculator.application.workbench.read_history import ReadHistory
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.rounding import UNCERTAINTY_SIGNIFICANT_DIGITS, render_decimal
from quantum_calculator.domain.units import Unit


@dataclass(frozen=True, slots=True)
class DisplayedAnswer:
    name: str
    symbol: str
    label: str
    value: str
    unit: str
    error: str | None
    error_origin: str | None


@dataclass(frozen=True, slots=True)
class AnswerDisplay:
    alternatives: tuple[str, ...]
    answers: tuple[DisplayedAnswer, ...]


class DisplayUnitRefusedError(Exception):
    def __init__(self, unit: str, alternatives: tuple[str, ...]) -> None:
        super().__init__(f"the answers of this run cannot be shown in {unit}")
        self.unit = unit
        self.alternatives = alternatives


class DisplayAnswers:
    def __init__(self, history: ReadHistory, units: UnitRegistry) -> None:
        self._history = history
        self._units = units

    def execute(self, identifier: str, unit: str | None) -> AnswerDisplay:
        record = self._history.details(identifier).outcome
        answers = () if record is None else reported_answers(record)
        alternatives = self._alternatives(answers)
        if record is None or unit is None:
            return AnswerDisplay(alternatives, tuple(_as_reported(answer) for answer in answers))
        target = self._units.find(unit)
        if target is None or target.symbol not in alternatives:
            raise DisplayUnitRefusedError(unit, alternatives)
        digits = significant_digits(record)
        return AnswerDisplay(
            alternatives, tuple(self._expressed(answer, target, digits) for answer in answers)
        )

    def _alternatives(self, answers: tuple[ReportedAnswer, ...]) -> tuple[str, ...]:
        for answer in answers:
            unit = self._units.find(answer.unit)
            if unit is not None and answer.magnitude is not None:
                return self._units.symbols_for(unit.dimension)
        return ()

    def _expressed(self, answer: ReportedAnswer, target: Unit, digits: int) -> DisplayedAnswer:
        source = self._units.find(answer.unit)
        if (
            source is None
            or source == target
            or source.dimension != target.dimension
            or answer.magnitude is None
        ):
            return _as_reported(answer)
        factor = source.si_factor / target.si_factor
        error = answer.error
        return DisplayedAnswer(
            name=answer.name,
            symbol=answer.symbol,
            label=answer.label,
            value=_rendered(answer.magnitude * factor, digits),
            unit=target.symbol,
            error=(
                None
                if error is None
                else error.display
                if error.magnitude is None
                else _rendered(error.magnitude * factor, UNCERTAINTY_SIGNIFICANT_DIGITS)
            ),
            error_origin=None if error is None else error.origin,
        )


def _as_reported(answer: ReportedAnswer) -> DisplayedAnswer:
    error = answer.error
    return DisplayedAnswer(
        name=answer.name,
        symbol=answer.symbol,
        label=answer.label,
        value=answer.display,
        unit=answer.unit,
        error=None if error is None else error.display,
        error_origin=None if error is None else error.origin,
    )


def _rendered(value: Fraction, digits: int) -> str:
    return str(render_decimal(value, digits).decimal)
