from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.domain.validated_problem import (
    BoundCount,
    BoundQuantity,
    UncertaintyModel,
    UserQuantity,
    ValidatedProblem,
)
from quantum_calculator.interfaces.serialization.encoding.exact_values import (
    JsonObject,
    QuantityEncoder,
)


class ProblemEncoder:
    def __init__(self, quantities: QuantityEncoder) -> None:
        self._quantities = quantities

    def encode(self, problem: ValidatedProblem) -> JsonObject:
        card = problem.card
        output = problem.output
        return {
            "card": {
                "identifier": card.identifier,
                "version": card.version,
                "area": card.area,
                "title": card.title,
            },
            "scope": list(card.scope),
            "hypotheses": [
                {"key": item.key, "value": item.value, "statement": item.statement}
                for item in problem.hypotheses
            ],
            "parameters": [
                *(self._encode_quantity(bound) for bound in problem.quantities),
                *(_encode_count(bound) for bound in problem.counts),
            ],
            "requested": {
                "quantity": output.rule.quantity,
                "symbol": output.rule.symbol,
                "label": output.rule.label,
                "unit": output.unit.symbol,
                "significant_digits": output.rounding.significant_digits,
            },
            "uncertainty": self._encode_uncertainty(problem.uncertainty),
        }

    def _encode_quantity(self, bound: BoundQuantity) -> JsonObject:
        origin: JsonObject
        if isinstance(bound.origin, PhysicalConstant):
            origin = {"origin": "catalog_constant", "constant": bound.origin.identifier}
        else:
            origin = {"origin": "user", "given": _encode_given(bound.origin)}
        return {
            "name": bound.name,
            "symbol": bound.symbol,
            **origin,
            "si": self._quantities.encode(bound.quantity),
        }

    def _encode_uncertainty(self, model: UncertaintyModel | None) -> JsonObject | None:
        if model is None:
            return None
        return {
            "covariance": model.covariance,
            "standard_uncertainties": [
                {
                    "parameter": declared.parameter,
                    "given": _encode_given(declared.given),
                    "si": self._quantities.encode(declared.given.to_si()),
                }
                for declared in model.standard_uncertainties
            ],
        }


def _encode_given(given: UserQuantity) -> JsonObject:
    return {"value": given.number.literal, "unit": given.unit.symbol}


def _encode_count(bound: BoundCount) -> JsonObject:
    return {"name": bound.name, "symbol": bound.symbol, "origin": "user", "count": str(bound.value)}
