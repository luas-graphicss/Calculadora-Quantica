from quantum_calculator.domain.numerical.problems import NumericalProblem
from quantum_calculator.domain.numerical.report import (
    NumericalAnswer,
    NumericalSolverReport,
    SampleTable,
)
from quantum_calculator.domain.rounding import (
    ROUNDING_MODE,
    UNCERTAINTY_SIGNIFICANT_DIGITS,
    render_float,
)
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject


def encode_numerical_problem(problem: NumericalProblem) -> JsonObject:
    context = problem.context
    card = context.card
    return {
        "card": {
            "identifier": card.identifier,
            "version": card.version,
            "area": card.area,
            "problem_type": card.problem_type,
            "title": card.title,
            "family": card.family.value,
        },
        "domain": list(card.domain),
        "hypotheses": [
            {"key": item.key, "value": item.value, "statement": item.statement}
            for item in context.hypotheses
        ],
        "inputs": [
            {"name": item.name, "label": item.label, "value": item.value, "origin": item.origin}
            for item in context.inputs
        ],
        "resolution": [
            {"name": item.name, "label": item.label, "value": item.value}
            for item in context.resolution
        ],
        "estimate": {
            "memory_bytes": context.estimate.memory_bytes,
            "operations": context.estimate.operations,
        },
        "rounding": {
            "mode": ROUNDING_MODE,
            "significant_digits": context.rounding.significant_digits,
        },
    }


def encode_numerical_result(report: NumericalSolverReport, significant_digits: int) -> JsonObject:
    return {
        "nature": report.nature.value,
        "answers": [_encode_answer(answer, significant_digits) for answer in report.answers],
        "tables": [_encode_table(table) for table in report.tables],
        "effective": [
            {"name": item.name, "label": item.label, "value": item.value}
            for item in report.effective
        ],
        "warnings": list(report.warnings),
    }


def _encode_answer(answer: NumericalAnswer, significant_digits: int) -> JsonObject:
    estimate = answer.estimate
    return {
        "name": answer.name,
        "symbol": answer.symbol,
        "label": answer.label,
        "value": answer.value,
        "display": str(render_float(answer.value, significant_digits)),
        "unit": answer.unit,
        "estimate": (
            None
            if estimate is None
            else {
                "value": estimate.value,
                "display": str(render_float(estimate.value, UNCERTAINTY_SIGNIFICANT_DIGITS)),
                "origin": estimate.origin,
            }
        ),
    }


def _encode_table(table: SampleTable) -> JsonObject:
    return {
        "name": table.name,
        "title": table.title,
        "rows": table.row_count,
        "columns": [
            {
                "name": column.name,
                "symbol": column.symbol,
                "unit": column.unit,
                "values": list(column.values),
            }
            for column in table.columns
        ],
    }
