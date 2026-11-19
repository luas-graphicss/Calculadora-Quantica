from quantum_calculator.domain.numerical.problems import NumericalProblem
from quantum_calculator.domain.numerical.report import NumericalPlan, NumericalRunRecord
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.interfaces.serialization.encoding.common_sections import (
    document_header,
    encode_budgeted_plan,
    encode_environment,
    encode_input,
    encode_verification,
)
from quantum_calculator.interfaces.serialization.encoding.constants import encode_constant
from quantum_calculator.interfaces.serialization.encoding.exact_values import (
    JsonObject,
    QuantityEncoder,
)
from quantum_calculator.interfaces.serialization.encoding.numerical_encoding import (
    encode_numerical_problem,
    encode_numerical_result,
)


class NumericalDocumentEncoder:
    def __init__(self, units: UnitRegistry) -> None:
        self._quantities = QuantityEncoder(units)

    def validation(self, problem: NumericalProblem, plan: NumericalPlan) -> JsonObject:
        return {
            **document_header("numerical_validation"),
            "input": encode_input(problem.context.spec),
            "problem": encode_numerical_problem(problem),
            "plan": encode_budgeted_plan(plan.method, plan.budget),
        }

    def run_record(self, record: NumericalRunRecord) -> JsonObject:
        context = record.problem.context
        return {
            **document_header("numerical_run_record"),
            "input": encode_input(context.spec),
            "problem": encode_numerical_problem(record.problem),
            "plan": encode_budgeted_plan(record.plan.method, record.plan.budget),
            "catalog": {"version": record.catalog_version},
            "constants": {
                "edition": record.constants_edition,
                "used": [
                    encode_constant(constant, self._quantities) for constant in context.constants
                ],
            },
            "units": {"registry_version": record.unit_registry_version},
            "result": encode_numerical_result(record.report, context.rounding.significant_digits),
            "verification": encode_verification(record.verification),
            "limitations": list(context.card.limitations),
            "environment": encode_environment(record.environment),
        }
