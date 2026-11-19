from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.interfaces.serialization.encoding.exact_values import (
    JsonObject,
    QuantityEncoder,
    encode_exact,
)


def encode_constant(constant: PhysicalConstant, quantities: QuantityEncoder) -> JsonObject:
    uncertainty = constant.standard_uncertainty
    return {
        "identifier": constant.identifier,
        "symbol": constant.symbol,
        "name": constant.name,
        "value": quantities.encode(constant.value),
        "exactness": constant.exactness.value,
        "standard_uncertainty": (
            None
            if uncertainty is None
            else encode_exact(uncertainty, quantities.unit_of(constant.value))
        ),
        "source": constant.source,
    }
