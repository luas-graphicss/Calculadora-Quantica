from quantum_calculator.application.review_numerical import NumericalReview
from quantum_calculator.application.review_problem import ProblemReview
from quantum_calculator.application.review_statement import StatementReview
from quantum_calculator.application.statements.budget import describe_budget
from quantum_calculator.domain.cards import CatalogListing
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.numerical.report import NumericalRunRecord
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.rounding import ROUNDING_MODE
from quantum_calculator.domain.run_record import RunRecord
from quantum_calculator.domain.symbolic_solution import StatementRunRecord
from quantum_calculator.interfaces.cli.rendering.text.catalog_sections import catalog_lines
from quantum_calculator.interfaces.cli.rendering.text.common_sections import (
    environment_section,
    limitations_section,
    verification_section,
)
from quantum_calculator.interfaces.cli.rendering.text.formatting import QuantityFormatter, section
from quantum_calculator.interfaces.cli.rendering.text.numerical_sections import (
    numerical_answer_lines,
    numerical_constants_section,
    numerical_method_section,
    numerical_problem_sections,
)
from quantum_calculator.interfaces.cli.rendering.text.numerical_tables import table_sections
from quantum_calculator.interfaces.cli.rendering.text.problem_sections import (
    problem_sections,
    request_section,
)
from quantum_calculator.interfaces.cli.rendering.text.record_sections import (
    answer_lines,
    calculation_section,
    constants_section,
    uncertainty_section,
)
from quantum_calculator.interfaces.cli.rendering.text.rejection_lines import rejection_lines
from quantum_calculator.interfaces.cli.rendering.text.solution_sections import (
    solution_answer_lines,
    solution_sections,
)
from quantum_calculator.interfaces.cli.rendering.text.statement_sections import (
    result_unit,
    statement_sections,
)


class TextRenderer:
    def __init__(self, units: UnitRegistry) -> None:
        self._units = units
        self._numbers = QuantityFormatter(units)

    def validation(self, review: ProblemReview) -> str:
        problem = review.problem
        method = review.plan.method
        digits = review.plan.rounding.significant_digits
        return _join(
            [
                f"Entrada válida: {problem.card.identifier} {problem.card.version}",
                f"plano: {method.identifier}, resultado {method.nature.value}, "
                f"{digits} algarismos significativos, arredondamento {ROUNDING_MODE}",
                *problem_sections(problem, self._numbers),
                *request_section(problem, self._numbers),
            ]
        )

    def run_record(self, record: RunRecord) -> str:
        return _join(
            [
                *answer_lines(record),
                *problem_sections(record.problem, self._numbers),
                *constants_section(record, self._numbers),
                *calculation_section(record, self._numbers),
                *uncertainty_section(record, self._numbers),
                *verification_section(record.verification),
                *limitations_section(record.problem.card.limitations),
                *environment_section(
                    record.environment, f"registro de unidades {record.unit_registry_version}"
                ),
            ]
        )

    def statement_validation(self, review: StatementReview) -> str:
        problem = review.problem
        method = review.plan.method
        return _join(
            [
                f"Enunciado válido: {problem.card.identifier} {problem.card.version}",
                f"plano: {method.identifier}, resultado {method.nature.value}; "
                f"limites: {describe_budget(review.plan.budget)}",
                *statement_sections(problem),
                *section("Saída", [f"resposta simbólica; {result_unit(problem, self._units)}"]),
                *limitations_section(problem.card.limitations),
            ]
        )

    def statement_run_record(self, record: StatementRunRecord) -> str:
        return _join(
            [
                *solution_answer_lines(record, result_unit(record.problem, self._units)),
                *statement_sections(record.problem),
                *solution_sections(record),
                *verification_section(record.verification),
                *limitations_section(record.problem.card.limitations),
                *environment_section(
                    record.environment,
                    f"catálogo {record.catalog_version}; "
                    f"registro de unidades {record.unit_registry_version}",
                ),
            ]
        )

    def numerical_validation(self, review: NumericalReview) -> str:
        context = review.problem.context
        method = review.plan.method
        return _join(
            [
                f"Problema numérico válido: {context.card.identifier} {context.card.version}",
                f"plano: {method.identifier}, resultado {method.nature.value}, "
                f"{context.rounding.significant_digits} algarismos significativos, "
                f"arredondamento {ROUNDING_MODE}; limites: {describe_budget(review.plan.budget)}",
                *numerical_problem_sections(review.problem),
                *limitations_section(context.card.limitations),
            ]
        )

    def numerical_run_record(self, record: NumericalRunRecord) -> str:
        context = record.problem.context
        return _join(
            [
                *numerical_answer_lines(record),
                *numerical_problem_sections(record.problem),
                *numerical_constants_section(record, self._numbers),
                *numerical_method_section(record),
                *table_sections(record.report.tables, context.rounding.significant_digits),
                *verification_section(record.verification),
                *limitations_section(context.card.limitations),
                *environment_section(
                    record.environment,
                    f"catálogo {record.catalog_version}; "
                    f"registro de unidades {record.unit_registry_version}",
                ),
            ]
        )

    def catalog(self, listing: CatalogListing) -> str:
        return _join(catalog_lines(listing))

    def rejection(self, rejection: ProblemRejectedError) -> str:
        return _join(rejection_lines(rejection))


def _join(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"
