import json

from quantum_calculator.application.review_problem import ProblemReview
from quantum_calculator.application.review_statement import StatementReview
from quantum_calculator.domain.cards import CatalogListing
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.run_record import RunRecord
from quantum_calculator.domain.symbolic_solution import StatementRunRecord
from quantum_calculator.interfaces.serialization.encoding.catalog_document import encode_catalog
from quantum_calculator.interfaces.serialization.encoding.documents import (
    DocumentEncoder,
    encode_rejection,
)
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject
from quantum_calculator.interfaces.serialization.encoding.statement_documents import (
    StatementDocumentEncoder,
)


class JsonRenderer:
    def __init__(self, units: UnitRegistry) -> None:
        self._problems = DocumentEncoder(units)
        self._statements = StatementDocumentEncoder(units)

    def validation(self, review: ProblemReview) -> str:
        return _dump(self._problems.validation(review.problem, review.plan))

    def run_record(self, record: RunRecord) -> str:
        return _dump(self._problems.run_record(record))

    def statement_validation(self, review: StatementReview) -> str:
        return _dump(self._statements.validation(review.problem, review.plan))

    def statement_run_record(self, record: StatementRunRecord) -> str:
        return _dump(self._statements.run_record(record))

    def catalog(self, listing: CatalogListing) -> str:
        return _dump(encode_catalog(listing))

    def rejection(self, rejection: ProblemRejectedError) -> str:
        return _dump(encode_rejection(rejection))


def _dump(document: JsonObject) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"
