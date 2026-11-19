import math
from dataclasses import dataclass
from fractions import Fraction

from quantum_calculator.application.workbench.summaries import (
    NUMERICAL_RUN_RECORD,
    RUN_RECORD,
    document_kind,
)
from quantum_calculator.domain.rounding import DEFAULT_SIGNIFICANT_DIGITS
from quantum_calculator.domain.workbench.documents import (
    Document,
    member,
    object_member,
    object_members,
    text_member,
)

_DIGITS_LOCATIONS = (
    ("plan", "rounding", "significant_digits"),
    ("problem", "rounding", "significant_digits"),
)


@dataclass(frozen=True, slots=True)
class ReportedError:
    display: str
    origin: str
    magnitude: Fraction | None


@dataclass(frozen=True, slots=True)
class ReportedAnswer:
    name: str
    symbol: str
    label: str
    display: str
    unit: str
    magnitude: Fraction | None
    error: ReportedError | None


def reported_answers(record: Document) -> tuple[ReportedAnswer, ...]:
    kind = document_kind(record)
    if kind == RUN_RECORD:
        return _closed_form_answers(record)
    if kind == NUMERICAL_RUN_RECORD:
        return tuple(
            _numerical_answer(answer) for answer in object_members(record, "result", "answers")
        )
    return ()


def significant_digits(record: Document) -> int:
    for location in _DIGITS_LOCATIONS:
        digits = member(record, *location)
        if isinstance(digits, int) and not isinstance(digits, bool):
            return digits
    return DEFAULT_SIGNIFICANT_DIGITS


def _closed_form_answers(record: Document) -> tuple[ReportedAnswer, ...]:
    value = object_member(record, "result", "value")
    if value is None:
        return ()
    answer = ReportedAnswer(
        name=text_member(record, "result", "quantity") or "",
        symbol=text_member(record, "result", "symbol") or "",
        label=text_member(record, "problem", "requested", "label") or "",
        display=text_member(value, "decimal") or "",
        unit=text_member(value, "unit") or "",
        magnitude=_ratio(text_member(value, "numerator"), text_member(value, "denominator")),
        error=_propagated_uncertainty(record),
    )
    return (answer,)


def _propagated_uncertainty(record: Document) -> ReportedError | None:
    uncertainty = object_member(record, "result", "uncertainty")
    if uncertainty is None or uncertainty.get("status") != "evaluated":
        return None
    display = text_member(uncertainty, "standard_uncertainty", "decimal")
    if display is None:
        return None
    covariance = text_member(uncertainty, "covariance")
    return ReportedError(
        display=display,
        origin=f"incerteza-padrão por propagação linear, covariância {covariance}",
        magnitude=_decimal(display),
    )


def _numerical_answer(answer: Document) -> ReportedAnswer:
    estimate = object_member(answer, "estimate")
    return ReportedAnswer(
        name=text_member(answer, "name") or "",
        symbol=text_member(answer, "symbol") or "",
        label=text_member(answer, "label") or "",
        display=text_member(answer, "display") or "",
        unit=text_member(answer, "unit") or "",
        magnitude=_binary(answer.get("value")),
        error=(
            None
            if estimate is None
            else ReportedError(
                display=text_member(estimate, "display") or "",
                origin=text_member(estimate, "origin") or "",
                magnitude=_binary(estimate.get("value")),
            )
        ),
    )


def _ratio(numerator: str | None, denominator: str | None) -> Fraction | None:
    if numerator is None or denominator is None:
        return None
    try:
        return Fraction(int(numerator), int(denominator))
    except (ValueError, ZeroDivisionError):
        return None


def _decimal(literal: str) -> Fraction | None:
    try:
        return Fraction(literal)
    except (ValueError, ZeroDivisionError):
        return None


def _binary(value: object) -> Fraction | None:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        return None
    return Fraction(value)
