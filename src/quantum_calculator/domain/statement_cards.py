from dataclasses import dataclass
from enum import StrEnum

from quantum_calculator.domain.methods import MethodDescription


class StatementShape(StrEnum):
    DERIVATIVE = "derivative"
    ANTIDERIVATIVE = "antiderivative"
    DEFINITE_INTEGRAL = "definite_integral"
    FIRST_ORDER_ODE = "first_order_ode"


class StatementField(StrEnum):
    CONDITIONS = "conditions"
    CANDIDATE = "candidate"


@dataclass(frozen=True, slots=True)
class StatementCard:
    identifier: str
    version: str
    area: str
    problem_type: str
    title: str
    domain: tuple[str, ...]
    shape: StatementShape
    required_fields: frozenset[StatementField]
    method: MethodDescription
    limitations: tuple[str, ...]
    example: str
