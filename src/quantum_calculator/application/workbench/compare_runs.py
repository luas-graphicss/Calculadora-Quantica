import json
from collections.abc import Iterator
from dataclasses import dataclass
from fractions import Fraction

from quantum_calculator.application.workbench.answers import ReportedAnswer, reported_answers
from quantum_calculator.application.workbench.read_history import ReadHistory, RunDetails
from quantum_calculator.application.workbench.summaries import is_failure
from quantum_calculator.domain.diagnostics import json_pointer
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.rounding import DEFAULT_SIGNIFICANT_DIGITS, render_decimal
from quantum_calculator.domain.workbench.documents import (
    Document,
    object_members,
    text_member,
)
from quantum_calculator.domain.workbench.runs import StoredRun

_ABSENT = object()


@dataclass(frozen=True, slots=True)
class VersionDivergence:
    subject: str
    base: str | None
    other: str | None


@dataclass(frozen=True, slots=True)
class InputDifference:
    pointer: str
    base: str | None
    other: str | None


@dataclass(frozen=True, slots=True)
class ComparedValue:
    display: str
    unit: str


@dataclass(frozen=True, slots=True)
class AnswerComparison:
    name: str
    symbol: str
    label: str
    base: ComparedValue | None
    other: ComparedValue | None
    ratio: str | None


@dataclass(frozen=True, slots=True)
class RunComparison:
    base: StoredRun
    other: StoredRun
    version_divergences: tuple[VersionDivergence, ...]
    input_differences: tuple[InputDifference, ...]
    base_method: str | None
    other_method: str | None
    answers: tuple[AnswerComparison, ...]


class CompareRuns:
    def __init__(self, history: ReadHistory, units: UnitRegistry) -> None:
        self._history = history
        self._units = units

    def execute(self, base_identifier: str, other_identifier: str) -> RunComparison:
        base = self._history.details(base_identifier)
        other = self._history.details(other_identifier)
        return RunComparison(
            base=base.run,
            other=other.run,
            version_divergences=_version_divergences(base, other),
            input_differences=tuple(
                _differences(_literal_document(base), _literal_document(other), ())
            ),
            base_method=text_member(base.problem, "plan", "method"),
            other_method=text_member(other.problem, "plan", "method"),
            answers=self._answers(base.outcome, other.outcome),
        )

    def _answers(
        self, base: Document | None, other: Document | None
    ) -> tuple[AnswerComparison, ...]:
        before = {answer.name: answer for answer in _answers_of(base)}
        after = {answer.name: answer for answer in _answers_of(other)}
        return tuple(
            self._compared(before.get(name), after.get(name)) for name in {**before, **after}
        )

    def _compared(
        self, base: ReportedAnswer | None, other: ReportedAnswer | None
    ) -> AnswerComparison:
        described = base or other
        if described is None:
            raise LookupError("an answer comparison needs the answer of at least one run")
        return AnswerComparison(
            name=described.name,
            symbol=described.symbol,
            label=described.label,
            base=None if base is None else ComparedValue(base.display, base.unit),
            other=None if other is None else ComparedValue(other.display, other.unit),
            ratio=None if base is None or other is None else self._ratio(base, other),
        )

    def _ratio(self, base: ReportedAnswer, other: ReportedAnswer) -> str | None:
        before = self._coherent(base, other.unit)
        after = self._coherent(other, base.unit)
        if before is None or after is None or before == 0:
            return None
        return str(render_decimal(after / before, DEFAULT_SIGNIFICANT_DIGITS).decimal)

    def _coherent(self, answer: ReportedAnswer, compared_unit: str) -> Fraction | None:
        if answer.magnitude is None or answer.unit == compared_unit:
            return answer.magnitude
        unit = self._units.find(answer.unit)
        compared = self._units.find(compared_unit)
        if unit is None or compared is None or unit.dimension != compared.dimension:
            return None
        return answer.magnitude * unit.si_factor


def _answers_of(outcome: Document | None) -> tuple[ReportedAnswer, ...]:
    return () if outcome is None else reported_answers(outcome)


def _version_divergences(base: RunDetails, other: RunDetails) -> tuple[VersionDivergence, ...]:
    before = _versions(base)
    after = _versions(other)
    return tuple(
        VersionDivergence(subject, version, after[subject])
        for subject, version in before.items()
        if subject in after and after[subject] != version
    )


def _versions(details: RunDetails) -> dict[str, str]:
    outcome = details.outcome
    recorded: dict[str, str | None] = {
        "calculadora": details.run.package_version,
        "ficha": text_member(details.problem, "problem", "card", "version"),
    }
    if outcome is not None and not is_failure(outcome):
        recorded |= {
            "esquema do registro": text_member(outcome, "schema_version"),
            "catálogo": text_member(outcome, "catalog", "version"),
            "constantes": text_member(outcome, "constants", "edition"),
            "registro de unidades": text_member(outcome, "units", "registry_version"),
            "Python": text_member(outcome, "environment", "python", "version"),
            "plataforma": text_member(outcome, "environment", "platform"),
        }
        for dependency in object_members(outcome, "environment", "dependencies"):
            recorded[str(dependency.get("name"))] = text_member(dependency, "version")
        for library in object_members(outcome, "environment", "linear_algebra"):
            subject = f"{library.get('interface')} usado por {library.get('consumer')}"
            recorded[subject] = f"{library.get('name')} {library.get('version')}"
    return {subject: version for subject, version in recorded.items() if version is not None}


def _literal_document(details: RunDetails) -> object:
    return json.loads(details.input_text, parse_float=str, parse_int=str)


def _differences(base: object, other: object, path: tuple[str, ...]) -> Iterator[InputDifference]:
    if isinstance(base, dict) and isinstance(other, dict):
        for key in sorted(base.keys() | other.keys()):
            yield from _differences(
                base.get(key, _ABSENT), other.get(key, _ABSENT), (*path, str(key))
            )
    elif isinstance(base, list) and isinstance(other, list):
        for index in range(max(len(base), len(other))):
            yield from _differences(_item(base, index), _item(other, index), (*path, str(index)))
    elif base != other:
        yield InputDifference(json_pointer(*path), _shown(base), _shown(other))


def _item(items: list[object], index: int) -> object:
    return items[index] if index < len(items) else _ABSENT


def _shown(value: object) -> str | None:
    if value is _ABSENT:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)
