from decimal import Decimal
from fractions import Fraction

from quantum_calculator.domain.rounding import UNCERTAINTY_SIGNIFICANT_DIGITS, render_square_root
from quantum_calculator.domain.run_record import RunRecord
from quantum_calculator.domain.solution import UncertaintyEvaluation

NOT_EVALUATED_REASON = "Nenhuma incerteza de entrada foi declarada."


def displayed_value(record: RunRecord) -> Fraction:
    return record.problem.output.unit.from_si(record.report.value)


def displayed_standard_uncertainty(record: RunRecord, evaluation: UncertaintyEvaluation) -> Decimal:
    factor = record.problem.output.unit.si_factor
    return render_square_root(
        evaluation.variance.magnitude / factor**2, UNCERTAINTY_SIGNIFICANT_DIGITS
    )


def displayed_relative_uncertainty(record: RunRecord, evaluation: UncertaintyEvaluation) -> Decimal:
    return render_square_root(
        evaluation.variance.magnitude / record.report.value.magnitude**2,
        UNCERTAINTY_SIGNIFICANT_DIGITS,
    )
