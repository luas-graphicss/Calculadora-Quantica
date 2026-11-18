from quantum_calculator.domain.rounding import UNCERTAINTY_SIGNIFICANT_DIGITS
from quantum_calculator.domain.run_record import RunRecord
from quantum_calculator.domain.solution import CalculationStep, UncertaintyContribution
from quantum_calculator.interfaces.serialization.encoding.display import (
    NOT_EVALUATED_REASON,
    displayed_relative_uncertainty,
    displayed_standard_uncertainty,
    displayed_value,
)
from quantum_calculator.interfaces.serialization.encoding.exact_values import (
    JsonObject,
    QuantityEncoder,
    encode_exact,
)


class ResultEncoder:
    def __init__(self, quantities: QuantityEncoder) -> None:
        self._quantities = quantities

    def encode(self, record: RunRecord) -> JsonObject:
        output = record.problem.output
        report = record.report
        digits = record.plan.rounding.significant_digits
        return {
            "quantity": output.rule.quantity,
            "symbol": output.rule.symbol,
            "nature": report.nature.value,
            "expression": {"plain": report.expression.plain, "latex": report.expression.latex},
            "value": encode_exact(displayed_value(record), output.unit.symbol, digits),
            "si_value": self._quantities.encode(report.value, digits),
            "conversion": {
                "unit": output.unit.symbol,
                "si_factor": encode_exact(
                    output.unit.si_factor,
                    f"{self._quantities.unit_of(report.value)}/{output.unit.symbol}",
                ),
                "defining_constants": list(output.unit.defining_constants),
            },
            "steps": [self._encode_step(step) for step in report.steps],
            "uncertainty": self._encode_uncertainty(record),
        }

    def _encode_step(self, step: CalculationStep) -> JsonObject:
        return {
            "description": step.description,
            "expression": step.expression,
            "value": None if step.value is None else self._quantities.encode(step.value),
        }

    def _encode_uncertainty(self, record: RunRecord) -> JsonObject:
        evaluation = record.report.uncertainty
        if evaluation is None:
            return {"status": "not_evaluated", "reason": NOT_EVALUATED_REASON}
        return {
            "status": "evaluated",
            "method": "linear_propagation",
            "covariance": evaluation.covariance,
            "standard_uncertainty": {
                "decimal": str(displayed_standard_uncertainty(record, evaluation)),
                "unit": record.problem.output.unit.symbol,
            },
            "relative_standard_uncertainty": str(
                displayed_relative_uncertainty(record, evaluation)
            ),
            "significant_digits": UNCERTAINTY_SIGNIFICANT_DIGITS,
            "variance": self._quantities.encode(evaluation.variance),
            "contributions": [
                self._encode_contribution(contribution) for contribution in evaluation.contributions
            ],
        }

    def _encode_contribution(self, contribution: UncertaintyContribution) -> JsonObject:
        return {
            "parameter": contribution.parameter,
            "symbol": contribution.symbol,
            "sensitivity": self._quantities.encode(contribution.sensitivity),
            "standard_uncertainty": self._quantities.encode(contribution.standard_uncertainty),
            "variance": self._quantities.encode(contribution.variance),
        }
