from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.symbolic_solution import StatementPlan, StatementRunRecord
from quantum_calculator.interfaces.serialization.encoding.common_sections import (
    document_header,
    encode_environment,
    encode_input,
    encode_verification,
)
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject
from quantum_calculator.interfaces.serialization.encoding.statement_encoding import (
    StatementEncoder,
    encode_statement_plan,
)


class StatementDocumentEncoder:
    def __init__(self, units: UnitRegistry) -> None:
        self._statements = StatementEncoder(units)

    def validation(self, problem: ValidatedStatement, plan: StatementPlan) -> JsonObject:
        return {
            **document_header("statement_validation"),
            "input": encode_input(problem.spec),
            "problem": self._statements.encode_problem(problem),
            "plan": encode_statement_plan(plan),
        }

    def run_record(self, record: StatementRunRecord) -> JsonObject:
        return {
            **document_header("statement_run_record"),
            "input": encode_input(record.problem.spec),
            "problem": self._statements.encode_problem(record.problem),
            "plan": encode_statement_plan(record.plan),
            "catalog": {"version": record.catalog_version},
            "units": {"registry_version": record.unit_registry_version},
            "result": self._statements.encode_result(record.problem, record.report),
            "verification": encode_verification(record.verification),
            "limitations": list(record.problem.card.limitations),
            "environment": encode_environment(record.environment),
        }
