from dataclasses import dataclass

from quantum_calculator.domain.workbench.documents import (
    Document,
    object_member,
    object_members,
    text_member,
)

REJECTION = "rejection"
CALCULATION_FAILURE = "calculation_failure"
RUN_RECORD = "run_record"
STATEMENT_RUN_RECORD = "statement_run_record"
NUMERICAL_RUN_RECORD = "numerical_run_record"

_SHOWN_ANSWERS = 3


@dataclass(frozen=True, slots=True)
class OutcomeSummary:
    verification_status: str | None
    failure_category: str | None
    headline: str | None


def document_kind(document: Document) -> str | None:
    return text_member(document, "document")


def is_failure(document: Document) -> bool:
    return document_kind(document) in (REJECTION, CALCULATION_FAILURE)


def summarize(outcome: Document) -> OutcomeSummary:
    if is_failure(outcome):
        return OutcomeSummary(None, text_member(outcome, "category"), None)
    return OutcomeSummary(text_member(outcome, "verification", "status"), None, _headline(outcome))


def _headline(record: Document) -> str | None:
    kind = document_kind(record)
    if kind == RUN_RECORD:
        return _closed_form_headline(record)
    if kind == STATEMENT_RUN_RECORD:
        return text_member(record, "result", "answer", "text")
    if kind == NUMERICAL_RUN_RECORD:
        return _numerical_headline(record)
    return None


def _closed_form_headline(record: Document) -> str | None:
    value = object_member(record, "result", "value")
    symbol = text_member(record, "result", "symbol")
    if value is None or symbol is None:
        return None
    return f"{symbol} = {text_member(value, 'decimal')} {text_member(value, 'unit')}"


def _numerical_headline(record: Document) -> str | None:
    answers = object_members(record, "result", "answers")
    if not answers:
        return None
    shown = [
        f"{text_member(answer, 'symbol')} = {text_member(answer, 'display')} "
        f"{text_member(answer, 'unit')}"
        for answer in answers[:_SHOWN_ANSWERS]
    ]
    remaining = len(answers) - len(shown)
    return "; ".join(shown) + (f"; e mais {remaining}" if remaining else "")
