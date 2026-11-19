from enum import StrEnum
from typing import Protocol

from quantum_calculator.application.review_numerical import NumericalReview
from quantum_calculator.application.review_problem import ProblemReview
from quantum_calculator.application.review_statement import StatementReview
from quantum_calculator.domain.cards import CatalogListing
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.numerical.report import NumericalRunRecord
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.run_record import RunRecord
from quantum_calculator.domain.symbolic_solution import StatementRunRecord
from quantum_calculator.interfaces.cli.rendering.json_renderer import JsonRenderer
from quantum_calculator.interfaces.cli.rendering.text_renderer import TextRenderer


class OutputFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


class ReportRenderer(Protocol):
    def validation(self, review: ProblemReview) -> str: ...

    def run_record(self, record: RunRecord) -> str: ...

    def statement_validation(self, review: StatementReview) -> str: ...

    def statement_run_record(self, record: StatementRunRecord) -> str: ...

    def numerical_validation(self, review: NumericalReview) -> str: ...

    def numerical_run_record(self, record: NumericalRunRecord) -> str: ...

    def catalog(self, listing: CatalogListing) -> str: ...

    def rejection(self, rejection: ProblemRejectedError) -> str: ...


def renderer_for(output_format: OutputFormat, units: UnitRegistry) -> ReportRenderer:
    if output_format is OutputFormat.JSON:
        return JsonRenderer(units)
    return TextRenderer(units)
