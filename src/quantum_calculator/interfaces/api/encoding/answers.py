from quantum_calculator.application.workbench.display_answers import AnswerDisplay
from quantum_calculator.interfaces.api.documents import api_document
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject


def encode_answers(run_identifier: str, display: AnswerDisplay) -> JsonObject:
    return {
        **api_document("answers"),
        "run_identifier": run_identifier,
        "display_units": list(display.alternatives),
        "answers": [
            {
                "name": answer.name,
                "symbol": answer.symbol,
                "label": answer.label,
                "value": answer.value,
                "unit": answer.unit,
                "error": answer.error,
                "error_origin": answer.error_origin,
            }
            for answer in display.answers
        ],
    }
