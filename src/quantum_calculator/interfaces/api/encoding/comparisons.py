from quantum_calculator.application.workbench.compare_runs import ComparedValue, RunComparison
from quantum_calculator.interfaces.api.documents import api_document
from quantum_calculator.interfaces.api.encoding.runs import encode_run
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject


def encode_comparison(comparison: RunComparison) -> JsonObject:
    return {
        **api_document("run_comparison"),
        "base": encode_run(comparison.base),
        "other": encode_run(comparison.other),
        "version_divergences": [
            {"subject": divergence.subject, "base": divergence.base, "other": divergence.other}
            for divergence in comparison.version_divergences
        ],
        "input_differences": [
            {"pointer": difference.pointer, "base": difference.base, "other": difference.other}
            for difference in comparison.input_differences
        ],
        "method": {"base": comparison.base_method, "other": comparison.other_method},
        "answers": [
            {
                "name": answer.name,
                "symbol": answer.symbol,
                "label": answer.label,
                "base": _encode_value(answer.base),
                "other": _encode_value(answer.other),
                "ratio": answer.ratio,
            }
            for answer in comparison.answers
        ],
    }


def _encode_value(value: ComparedValue | None) -> JsonObject | None:
    return None if value is None else {"value": value.display, "unit": value.unit}
