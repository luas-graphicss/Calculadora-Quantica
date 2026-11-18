import json

from quantum_calculator.application.review_problem import ProblemReview
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.run_record import RunRecord
from quantum_calculator.interfaces.serialization.encoding.documents import (
    DocumentEncoder,
    encode_rejection,
)
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject


class JsonRenderer:
    def __init__(self, units: UnitRegistry) -> None:
        self._encoder = DocumentEncoder(units)

    def validation(self, review: ProblemReview) -> str:
        return _dump(self._encoder.validation(review.problem, review.plan))

    def run_record(self, record: RunRecord) -> str:
        return _dump(self._encoder.run_record(record))

    def rejection(self, rejection: ProblemRejectedError) -> str:
        return _dump(encode_rejection(rejection))


def _dump(document: JsonObject) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"
